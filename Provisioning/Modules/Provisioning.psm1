# Provisioning.psm1
# This module provides core provisioning logic for setting up new workstations.

#region Module-Specific Global Variables and Configuration
$Global:LogEntries = @()
$Global:SessionId = [guid]::NewGuid().ToString()
$Global:StartTime = Get-Date

# Summary object to track the status and details of each major operation.
$Global:Summary = @{
    UserCreation = $false
    UserDeletion = $false
    ComputerRename = $false
    Activation = $false
    RemoteDesktopEnabled = $false
    PowerSettingsApplied = $false
    SshEnabled = $false
    ComputerOldName = $env:COMPUTERNAME
    ComputerNewName = $null
    OriginalUserWasDeleted = $false
    EnvironmentChecksPassed = $false
    RollbackTriggered = $false
    RollbackSuccessful = $false
    ScriptTerminatedEarly = $false
    SelectedTasks = @{}
    UnexpectedErrorOccurred = $false
}

# Configuration Defaults (Initialized in Initialize-ProvisioningModule)
$script:TargetUserName = "Administrator"
$script:TargetUserDisplayName = "Admin User"

$script:KmsActivationKeys = @{
    "1" = @{ Key = "HQG9K-VGNDD-XQHKH-6QYWY-PR473"; Description = "Windows 10/11 Pro for Education" }
    "2" = @{ Key = "4N9DF-KVXH3-3Q677-F7YQX-RM48R"; Description = "Windows 10/11 Enterprise" }
    "3" = @{ Key = "CCKJY-7NGT9-XJGDT-X3KRJ-29YV9"; Description = "Windows 10/11 Pro for Workstations" }
}

$script:AvailableTasks = @(
    @{ Id = 1; Name = "User Management"; Description = "Create/verify target admin account" }
    @{ Id = 2; Name = "Computer Rename"; Description = "Rename the computer (e.g., DEPT-LAB-COMPNAME)" }
    @{ Id = 3; Name = "Remote Desktop (RDP)"; Description = "Enable Remote Desktop access" }
    @{ Id = 4; Name = "Always-On Power Settings"; Description = "Configure power to prevent sleep" }
    @{ Id = 5; Name = "OpenSSH Server (SSH)"; Description = "Enable/Disable SSH access" }
    @{ Id = 6; Name = "Windows Activation"; Description = "Attempt Windows KMS activation" }
)

$script:ModuleDebugMode = $false
$script:ModuleForceProfileDelete = $false

#endregion

#region Module Utility Functions

function Write-ProvisioningLog {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","DEBUG")]
        [string]$Level = "INFO"
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $entry = "$timestamp [$Level] $Message"
    $Global:LogEntries += $entry
    if ($Level -ne "DEBUG" -or $script:ModuleDebugMode) {
        Write-Host $entry
    }
}

function Show-ProvisioningSummary {
    $endTime = Get-Date
    $duration = New-TimeSpan -Start $Global:StartTime -End $endTime

    Write-Host "`n"
    Write-Host "========================================"
    Write-Host "        Provisioning Summary Report       "
    Write-Host "========================================"
    Write-Host "Session ID:    $Global:SessionId"
    Write-Host "Started at:    $Global:StartTime"
    Write-Host "Finished at:   $endTime"
    Write-Host "Duration:      $("{0:hh\:mm\:ss}" -f $duration)"
    Write-Host ""

    Write-Host "--- Overall Status ---"
    # Logic same as original but with Provisioning naming
    $overallStatus = "[FAILED] Script encountered an unexpected error."
    if ($Global:Summary.ScriptTerminatedEarly -and -not $Global:Summary.EnvironmentChecksPassed) {
        $overallStatus = "[CANCELED] Script terminated early due to critical pre-flight check failure."
    } elseif ($Global:Summary.ScriptTerminatedEarly -and $Global:Summary.EnvironmentChecksPassed) {
        $overallStatus = "[CANCELED] Script exited by user before completion."
    } elseif ($Global:Summary.RollbackTriggered) {
        $overallStatus = "[CANCELED] Operation Canceled, Rollback Attempted"
        if ($Global:Summary.RollbackSuccessful) { $overallStatus += " ([SUCCESS] Rollback successful)" } else { $overallStatus += " ([FAILED] Rollback partial/failed)" }
    } elseif ($Global:Summary.EnvironmentChecksPassed -and -not $Global:Summary.UnexpectedErrorOccurred) {
        $allSelectedTasksCompletedSuccessfully = $true
        $anyTaskSelected = $false

        foreach ($task in $script:AvailableTasks) {
            if ($Global:Summary.SelectedTasks.ContainsKey($task.Name) -and $Global:Summary.SelectedTasks[$task.Name]) {
                $anyTaskSelected = $true
                $taskSuccessFlag = $false
                switch ($task.Name) {
                    "User Management" { $taskSuccessFlag = $Global:Summary.UserCreation }
                    "Computer Rename" { $taskSuccessFlag = $Global:Summary.ComputerRename }
                    "Remote Desktop (RDP)" { $taskSuccessFlag = $Global:Summary.RemoteDesktopEnabled }
                    "Always-On Power Settings" { $taskSuccessFlag = $Global:Summary.PowerSettingsApplied }
                    "OpenSSH Server (SSH)" { $taskSuccessFlag = $Global:Summary.SshEnabled }
                    "Windows Activation" { $taskSuccessFlag = $Global:Summary.Activation }
                }
                if (-not $taskSuccessFlag) { $allSelectedTasksCompletedSuccessfully = $false }
            }
        }
        if (-not $anyTaskSelected) {
            $overallStatus = "[NO OPERATIONS SELECTED] No tasks were chosen to be performed."
        } elseif ($allSelectedTasksCompletedSuccessfully) {
            $overallStatus = "[SUCCESS] All selected operations completed."
        } else {
            $overallStatus = "[PARTIAL SUCCESS] Some selected operations completed, others failed/skipped."
        }
    }
    Write-Host "Overall Script Status: $overallStatus"
    Write-Host ""

    Write-Host "--- Pre-flight Checks Status ---"
    $envCheckStatus = if ($Global:Summary.EnvironmentChecksPassed) { "[SUCCESS] Passed" } else { "[FAILED] Failed" }
    Write-Host "Environment Checks: $envCheckStatus"
    Write-Host ""

    Write-Host "--- Operations Status ---"
    
    if ($Global:Summary.SelectedTasks.ContainsKey('User Management') -and $Global:Summary.SelectedTasks['User Management']) {
        $userDeletionStatus = if ($Global:Summary.UserDeletion) { "[SUCCESS] Deleted (or not present)" } else { "[SKIPPED/FAILED] Not deleted" }
        Write-Host "User Deletion ($script:TargetUserName): $userDeletionStatus"
        $userCreationStatus = if ($Global:Summary.UserCreation) { "[SUCCESS] Created/Verified" } else { "[FAILED] Not created" }
        Write-Host "User Creation ($script:TargetUserName): $userCreationStatus"
    }
    if ($Global:Summary.SelectedTasks.ContainsKey('Computer Rename') -and $Global:Summary.SelectedTasks['Computer Rename']) {
        $renameStatus = if ($Global:Summary.ComputerRename) { "[SUCCESS] Renamed" } else { "[FAILED/SKIPPED] Not renamed" }
        if ($Global:Summary.ComputerOldName -and $Global:Summary.ComputerNewName) {
            Write-Host "Computer Name Change: Old: '$($Global:Summary.ComputerOldName)' -> New: '$($Global:Summary.ComputerNewName)'"
            Write-Host "Status: $renameStatus"
        } else { Write-Host "Computer Name Change: Not attempted." }
    }
    if ($Global:Summary.SelectedTasks.ContainsKey('Remote Desktop (RDP)') -and $Global:Summary.SelectedTasks['Remote Desktop (RDP)']) {
        $rdpStatus = if ($Global:Summary.RemoteDesktopEnabled) { "[SUCCESS] Enabled" } else { "[SKIPPED/FAILED] Not enabled" }
        Write-Host "Remote Desktop:        $rdpStatus"
    }
    if ($Global:Summary.SelectedTasks.ContainsKey('Always-On Power Settings') -and $Global:Summary.SelectedTasks['Always-On Power Settings']) {
        $powerStatus = if ($Global:Summary.PowerSettingsApplied) { "[SUCCESS] Configured" } else { "[SKIPPED/FAILED] Not configured" }
        Write-Host "Always-On Power:       $powerStatus"
    }
    if ($Global:Summary.SelectedTasks.ContainsKey('OpenSSH Server (SSH)') -and $Global:Summary.SelectedTasks['OpenSSH Server (SSH)']) {
        $sshStatus = if ($Global:Summary.SshEnabled) { "[SUCCESS] Enabled" } else { "[SKIPPED/FAILED] Not enabled" }
        Write-Host "OpenSSH Server:        $sshStatus"
    }
    if ($Global:Summary.SelectedTasks.ContainsKey('Windows Activation') -and $Global:Summary.SelectedTasks['Windows Activation']) {
        $activationStatus = if ($Global:Summary.Activation) { "[SUCCESS] Activated" } else { "[FAILED/SKIPPED] Not activated" }
        Write-Host "Windows Activation:    $activationStatus"
    }

    Write-Host ""
    Write-Host "Full log file saved at: $env:SystemDrive\Provisioning-$Global:SessionId.log"
    Write-Host "========================================"
}

function Save-ProvisioningLog {
    $logPath = "$env:SystemDrive\Provisioning-$Global:SessionId.log"
    try {
        $Global:LogEntries | Out-File -FilePath $logPath -Encoding utf8 -Force
        Write-ProvisioningLog "All log entries saved to '$logPath'." "INFO"
    } catch {
        $errorMessage = $_.Exception.Message
        Write-Warning "Failed to save log file to '$logPath': ${errorMessage}"
        Write-ProvisioningLog "Failed to save log file to '$logPath': ${errorMessage}" "ERROR"
    }
}

#endregion

#region Core Provisioning Functions

function Initialize-ProvisioningModule {
    param(
        [string]$TargetUser = "Admin",
        [string]$TargetDisplayName = "Administrator",
        [switch]$DebugMode,
        [switch]$ForceProfileDelete
    )
    $script:TargetUserName = $TargetUser
    $script:TargetUserDisplayName = $TargetDisplayName
    $script:ModuleDebugMode = $DebugMode.IsPresent
    $script:ModuleForceProfileDelete = $ForceProfileDelete.IsPresent
    Write-ProvisioningLog "Provisioning Module initialized for user '$script:TargetUserName'." "DEBUG"
}

function Test-ProvisioningPreflightChecks {
    Write-ProvisioningLog "Initiating all pre-flight checks..." "INFO"
    $allCriticalChecksPassed = $true

    if (-not (Test-IsAdministratorInternal)) { $allCriticalChecksPassed = $false }
    if (-not (Check-OSCompatibilityInternal)) { $allCriticalChecksPassed = $false }
    if (-not (Check-PowerShellVersionInternal)) { $allCriticalChecksPassed = $false }
    Check-DiskSpaceInternal
    Check-UserContextInternal

    if (-not $allCriticalChecksPassed) {
        Write-ProvisioningLog "One or more critical pre-flight checks failed. Script will terminate." "ERROR"
        $Global:Summary.EnvironmentChecksPassed = $false
        $Global:Summary.ScriptTerminatedEarly = $true
        return $false
    }
    Write-ProvisioningLog "All critical pre-flight checks passed." "INFO"
    $Global:Summary.EnvironmentChecksPassed = $true
    return $true
}

function Show-ProvisioningMainMenu {
    $selectedTasks = @{}
    while ($true) {
        Write-Host "`n"
        Write-Host "========================================"
        Write-Host "        Provisioning - Main Menu        "
        Write-Host "========================================"
        Write-Host "Target User: $($script:TargetUserName)"
        Write-Host "----------------------------------------"
        foreach ($task in $script:AvailableTasks) {
            $status = if ($selectedTasks.ContainsKey($task.Name) -and $selectedTasks[$task.Name]) { "[SELECTED]" } else { "[       ]" }
            Write-Host "$($task.Id)) $status $($task.Description)"
        }
        Write-Host "----------------------------------------"
        Write-Host "A) Select All Tasks"
        Write-Host "X) Proceed with Selected Tasks"
        Write-Host "Q) Quit Script (no changes)"
        Write-Host "========================================"

        $choice = Read-Host "Enter your choice(s) (e.g., '1,3' or 'A')"
        if ($null -eq $choice) {
            Write-ProvisioningLog "Cancelled by user." "INFO"
            $Global:Summary.ScriptTerminatedEarly = $true
            exit 0
        }
        $choice = $choice.ToUpper().Trim()

        if ($choice -eq 'A') {
            foreach ($task in $script:AvailableTasks) { $selectedTasks[$task.Name] = $true }
        } elseif ($choice -eq 'X') {
            break
        } elseif ($choice -eq 'Q') {
            $Global:Summary.ScriptTerminatedEarly = $true
            exit 0
        } else {
            foreach ($item in $choice.Split(',')) {
                $item = $item.Trim()
                if ([int]::TryParse($item, [ref]$taskId)) {
                    $task = $script:AvailableTasks | Where-Object { $_.Id -eq $taskId }
                    if ($task) {
                        $selectedTasks[$task.Name] = -not ($selectedTasks.ContainsKey($task.Name) -and $selectedTasks[$task.Name])
                    }
                }
            }
        }
    }
    $Global:Summary.SelectedTasks = $selectedTasks
    return $selectedTasks
}

function Perform-ProvisioningUserManagement {
    param(
        [System.Security.SecureString]$SecurePassword
    )
    Write-ProvisioningLog "Starting user management for account: $script:TargetUserName" "INFO"
    $userExists = Get-LocalUser -Name $script:TargetUserName -ErrorAction SilentlyContinue
    $Global:Summary.UserDeletion = Handle-UserDeletionInternal -Username $script:TargetUserName -ForceProfileDeleteSwitch:$script:ModuleForceProfileDelete
    $Global:Summary.OriginalUserWasDeleted = ($Global:Summary.UserDeletion -and $null -ne $userExists)

    $Global:Summary.UserCreation = Create-NewUserAccountInternal -Username $script:TargetUserName -DisplayName $script:TargetUserDisplayName -SecurePassword $SecurePassword
}

function Perform-ProvisioningComputerRename {
    param(
        [string]$Prefix = "SBS",
        [string]$DeptCode,
        [string]$BaseName
    )
    Write-ProvisioningLog "Starting computer rename process." "INFO"
    $newComputerName = ("{0}-{1}-{2}" -f $Prefix, $DeptCode, $BaseName).ToUpper()
    $Global:Summary.ComputerRename = Rename-LocalComputerInternal -NewName $newComputerName
}

function Perform-ProvisioningRemoteDesktop {
    param([bool]$Enable)
    $Global:Summary.RemoteDesktopEnabled = Configure-RemoteDesktopInternal -Enable:$Enable
}

function Perform-ProvisioningPowerSettings {
    param([bool]$Enable)
    $Global:Summary.PowerSettingsApplied = Configure-PowerSettingsAlwaysOnInternal -Enable:$Enable
}

function Perform-ProvisioningOpenSsh {
    param([bool]$Enable)
    $Global:Summary.SshEnabled = Configure-OpenSshServerInternal -Enable:$Enable
}

function Get-ProvisioningKmsKeys {
    return $script:KmsActivationKeys
}

function Perform-ProvisioningActivation {
    param([string]$Key, [string]$Description)
    $Global:Summary.Activation = Perform-WindowsActivationInternal -Key $Key -Description $Description
}

function Perform-ProvisioningRollback {
    $Global:Summary.RollbackTriggered = $true
    Write-ProvisioningLog "Rollback sequence initiated." "INFO"
    Write-Host "`n--- Initiating Rollback of Applied Changes ---"
    
    $rollbackSuccess = $true

    # Rolback Computer Rename
    if ($Global:Summary.ComputerRename -and $Global:Summary.ComputerOldName -ne $env:COMPUTERNAME) {
        if (Read-Host "Rollback computer name to '$($Global:Summary.ComputerOldName)'? (Y/N)" -eq 'Y') {
            if (-not (Rename-LocalComputerInternal -NewName $Global:Summary.ComputerOldName)) { $rollbackSuccess = $false }
        }
    }

    # Rollback User Creation
    if ($Global:Summary.UserCreation -and -not $Global:Summary.OriginalUserWasDeleted) {
        if (Read-Host "Remove newly created user '$script:TargetUserName'? (Y/N)" -eq 'Y') {
            if (-not (Handle-UserDeletionInternal -Username $script:TargetUserName -ForceProfileDeleteSwitch:$true)) { $rollbackSuccess = $false }
        }
    }

    # Rollback RDP
    if ($Global:Summary.RemoteDesktopEnabled) {
        if (Read-Host "Disable Remote Desktop? (Y/N)" -eq 'Y') {
            if (-not (Configure-RemoteDesktopInternal -Enable:$false)) { $rollbackSuccess = $false }
        }
    }

    # Rollback SSH
    if ($Global:Summary.SshEnabled) {
        if (Read-Host "Disable OpenSSH? (Y/N)" -eq 'Y') {
            if (-not (Configure-OpenSshServerInternal -Enable:$false)) { $rollbackSuccess = $false }
        }
    }

    $Global:Summary.RollbackSuccessful = $rollbackSuccess
    return $rollbackSuccess
}

#endregion

#region Internal Helpers (Internal Module Logic)

function Test-IsAdministratorInternal {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole] "Administrator")
    if (-not $isAdmin) { Write-Warning "Must run as Administrator."; return $false }
    return $true
}

function Check-OSCompatibilityInternal {
    $os = Get-CimInstance Win32_OperatingSystem
    if ([Version]$os.Version -lt [Version]"10.0") { Write-Warning "Requires Windows 10+."; return $false }
    return $true
}

function Check-PowerShellVersionInternal {
    if ($PSVersionTable.PSVersion -lt [Version]"5.1") { Write-Warning "Requires PS 5.1+."; return $false }
    return $true
}

function Check-DiskSpaceInternal {
    param([int]$RequiredGB = 5)
    $drive = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3 and DeviceID='$env:SystemDrive'"
    if ($drive.FreeSpace / 1GB -lt $RequiredGB) { Write-Warning "Low disk space."; return $false }
    return $true
}

function Check-UserContextInternal {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent().Name.Split('\')[-1]
    if ($current -eq $script:TargetUserName) { Write-Warning "Running as target user."; return $true }
    return $false
}

function Handle-UserDeletionInternal {
    param([string]$Username, [switch]$ForceProfileDeleteSwitch)
    try {
        $user = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
        if ($null -eq $user) { return $true }
        
        if ($ForceProfileDeleteSwitch) {
            $sid = $user.SID.Value
            $profile = Get-CimInstance Win32_UserProfile | Where-Object { $_.SID -eq $sid }
            if ($profile) { Remove-CimInstance -InputObject $profile -ErrorAction SilentlyContinue }
        }
        
        Remove-LocalUser -Name $Username -ErrorAction Stop
        return $true
    } catch { return $false }
}

function Create-NewUserAccountInternal {
    param([string]$Username, [string]$DisplayName, [System.Security.SecureString]$SecurePassword)
    try {
        if (Get-LocalUser -Name $Username -ErrorAction SilentlyContinue) {
            Add-LocalGroupMember -Group "Administrators" -Member $Username -ErrorAction SilentlyContinue
            return $true
        }
        New-LocalUser -Name $Username -Password $SecurePassword -FullName $DisplayName -Description "Target Admin" -PasswordNeverExpires | Out-Null
        Add-LocalGroupMember -Group "Administrators" -Member $Username -ErrorAction Stop
        return $true
    } catch { return $false }
}

function Rename-LocalComputerInternal {
    param([string]$NewName)
    try {
        if ($env:COMPUTERNAME -eq $NewName) { return $true }
        Rename-Computer -NewName $NewName -Force -ErrorAction Stop
        return $true
    } catch { return $false }
}

function Configure-RemoteDesktopInternal {
    param([bool]$Enable)
    try {
        $val = if ($Enable) { 0 } else { 1 }
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value $val -Force
        if ($Enable) {
            Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
            Set-Service -Name "TermService" -StartupType Automatic
            Start-Service -Name "TermService" -ErrorAction SilentlyContinue
        } else {
            Disable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
            Set-Service -Name "TermService" -StartupType Disabled
        }
        return $true
    } catch { return $false }
}

function Configure-PowerSettingsAlwaysOnInternal {
    param([bool]$Enable)
    try {
        if ($Enable) {
            powercfg /change standby-timeout-ac 0
            powercfg /change hibernate-timeout-ac 0
        } else {
            powercfg /setactive SCHEME_BALANCED
        }
        return $true
    } catch { return $false }
}

function Configure-OpenSshServerInternal {
    param([bool]$Enable)
    try {
        if ($Enable) {
            Set-Service -Name "sshd" -StartupType Automatic
            Start-Service -Name "sshd" -ErrorAction SilentlyContinue
            Enable-NetFirewallRule -DisplayName "OpenSSH SSH Server (sshd)" -ErrorAction SilentlyContinue
        } else {
            Stop-Service -Name "sshd" -ErrorAction SilentlyContinue
            Set-Service -Name "sshd" -StartupType Disabled
        }
        return $true
    } catch { return $false }
}

function Perform-WindowsActivationInternal {
    param([string]$Key, [string]$Description)
    try {
        cscript C:\Windows\System32\slmgr.vbs /ipk $Key | Out-Null
        cscript C:\Windows\System32\slmgr.vbs /ato | Out-Null
        return $true
    } catch { return $false }
}

#endregion

Export-ModuleMember -Function `
    Initialize-ProvisioningModule, `
    Test-ProvisioningPreflightChecks, `
    Show-ProvisioningMainMenu, `
    Perform-ProvisioningUserManagement, `
    Perform-ProvisioningComputerRename, `
    Perform-ProvisioningRemoteDesktop, `
    Perform-ProvisioningPowerSettings, `
    Perform-ProvisioningOpenSsh, `
    Get-ProvisioningKmsKeys, `
    Perform-ProvisioningActivation, `
    Perform-ProvisioningRollback, `
    Write-ProvisioningLog, `
    Show-ProvisioningSummary, `
    Save-ProvisioningLog

Export-ModuleMember -Variable Global:Summary
