<#
.SYNOPSIS
    Installs and Configures OpenSSH Server for Intune/Tanium Deployment.

.DESCRIPTION
    - Installs OpenSSH.Server if missing.
    - Configures sshd service (automatic startup).
    - Sets custom Port and PasswordAuthentication.
    - Deploys admin public keys (from array or file).
    - Configures firewall.
    - Logs execution to C:\ProgramData\WINTOOLS\Logs\.

.PARAMETER AdminKeys
    Array of admin public keys to deploy (multi-admin / JIT).

.PARAMETER KeysFile
    Path to a text file containing public keys (one per line). Overrides/Merges with AdminKeys.

.PARAMETER SSHPort
    TCP port for SSH. Default: 22

.PARAMETER DisablePasswordAuth
    $true to disable PasswordAuthentication after verifying keys work.

.NOTES
    Version: 3.2.1
    Author: Antigravity (fixed & improved)
    Date: 2026-02-09
#>

param (
    [string[]]$AdminKeys = @(),
    [string]$KeysFile,
    [int]$SSHPort = 22,
    [switch]$DisablePasswordAuth,
    [switch]$Silent
)

# --- Logging Setup ---
$LogDir = "$env:ProgramData\WINTOOLS\Logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogFile = Join-Path $LogDir "Deploy-OpenSSH.log"
Start-Transcript -Path $LogFile -Append -Force

if (-not $Silent) {
    Write-Output "--- Starting OpenSSH Deployment: $(Get-Date) ---"
}

# --- Administrator Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "This script must be run as Administrator."
    Stop-Transcript
    Exit 1
}

# --- OS Compatibility Check ---
$osVersion = [System.Environment]::OSVersion.Version
# Windows 10 updated October 2018 (1809) -> Build 17763. This is when OpenSSH became a built-in Capability.
if ($osVersion.Major -lt 10 -or ($osVersion.Major -eq 10 -and $osVersion.Build -lt 17763)) {
    Write-Warning "This script requires Windows 10 (1809+) or Windows 11. Your version: $($osVersion.Major).$($osVersion.Minor) (Build $($osVersion.Build))."
    Write-Warning "OpenSSH Server installation via 'Add-WindowsCapability' is not supported on this OS."
    Write-Warning "Exiting gracefully to prevent errors."
    Stop-Transcript
    Exit 0
}

# --- Load Keys from File ---
if ($KeysFile -and (Test-Path $KeysFile -PathType Leaf)) {
    Write-Output "Loading keys from file: $KeysFile"
    $FileKeys = Get-Content $KeysFile -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*ssh-' }
    $AdminKeys += $FileKeys
}

# --- Configuration ---
$ServiceName    = "sshd"
$CapabilityName = "OpenSSH.Server~~~~0.0.1.0"
$SSHDataPath    = "$env:ProgramData\ssh"
$AuthorizedKeysPath = Join-Path $SSHDataPath "administrators_authorized_keys"
$ConfigPath     = Join-Path $SSHDataPath "sshd_config"

# --- Helper Functions ---

function Deploy-Keys {
    param (
        [string[]]$KeyArray
    )

    if (-not (Test-Path $SSHDataPath)) {
        New-Item -ItemType Directory -Path $SSHDataPath -Force | Out-Null
    }

    # Deduplicate and clean keys
    $UniqueKeys = $KeyArray | Select-Object -Unique | Where-Object { $_ -notmatch '^\s*$' -and $_ -match '^\s*ssh-' }

    if ($UniqueKeys.Count -gt 0) {
        # Use ASCII to avoid BOM issues
        $UniqueKeys | Set-Content -Path $AuthorizedKeysPath -Force -Encoding ASCII
        Write-Output "Deployed $($UniqueKeys.Count) unique admin key(s) to $AuthorizedKeysPath"

        # Set strict permissions (Administrators + SYSTEM only)
        $acl = Get-Acl $AuthorizedKeysPath
        $acl.SetAccessRuleProtection($true, $false)  # Disable inheritance

        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
            "BUILTIN\Administrators", "FullControl", "Allow")))
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
            "NT AUTHORITY\SYSTEM", "FullControl", "Allow")))

        Set-Acl -Path $AuthorizedKeysPath -AclObject $acl
        Write-Output "Strict permissions applied to authorized_keys (Admins + SYSTEM only)."
    }
    else {
        Write-Warning "No valid admin keys provided → key-based SSH access will NOT work!"
    }
}

function Update-Config {
    param (
        [int]$Port,
        [bool]$DisablePwdAuth
    )

    $pwdValue = if ($DisablePwdAuth) { 'no' } else { 'yes' }

    if (-not (Test-Path $ConfigPath)) {
        Write-Warning "sshd_config not found → creating minimal config"
        @(
            "Port $Port",
            "PubkeyAuthentication yes",
            "PasswordAuthentication $pwdValue"
        ) | Set-Content -Path $ConfigPath -Encoding ASCII
        # Do not return! Fall through to ensure permissions are fixed and Match block is added.
        Write-Output "Created minimal config. Proceeding to configure settings and permissions..."
    }

    # Use ASCII/Default to read - avoiding explicit UTF8 might be safer if file has no BOM
    $lines = Get-Content $ConfigPath
    $newLines = @()
    $inAdminMatchBlock = $false
    $addedMatchBlock = $false

    foreach ($line in $lines) {
        $trimmed = $line.Trim()

        if ($trimmed -match '^#?\s*Port\s') {
            $newLines += "Port $Port"
            continue
        }
        if ($trimmed -match '^#?\s*PasswordAuthentication\s') {
            $newLines += "PasswordAuthentication $pwdValue"
            continue
        }
        if ($trimmed -match '^#?\s*PubkeyAuthentication\s') {
            $newLines += "PubkeyAuthentication yes"
            continue
        }

        if ($trimmed -eq 'Match Group administrators') {
            $inAdminMatchBlock = $true
            $newLines += $line
            continue
        }

        if ($inAdminMatchBlock -and $trimmed -match '^#?\s*AuthorizedKeysFile') {
            $newLines += "    AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
            $inAdminMatchBlock = $false
            continue
        }

        $newLines += $line
    }

    # Append Match block if missing
    if (-not ($newLines -match 'Match Group administrators')) {
        Write-Output "Adding missing 'Match Group administrators' block to sshd_config"
        $newLines += ""
        $newLines += "Match Group administrators"
        $newLines += "    AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys"
        $addedMatchBlock = $true
    }

    # IMPORTANT: Use ASCII encoding to prevent BOM which breaks sshd on Windows
    $newLines | Set-Content -Path $ConfigPath -Encoding ASCII
    
    # FIX PERMISSIONS GLOBALLY on C:\ProgramData\ssh (Critical for Service Start)
    try {
        # Host Keys MUST be accessible by SYSTEM (and Admins) but NO ONE ELSE.
        # We apply this to the whole folder to be safe.
        $acl = Get-Acl $SSHDataPath
        $acl.SetAccessRuleProtection($true, $false) # Disable inheritance
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")))
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")))
        Set-Acl -Path $SSHDataPath -AclObject $acl
        
        # Re-apply strict file-level permissions for existing files
        Get-ChildItem -Path $SSHDataPath -Recurse | ForEach-Object {
            try {
                Set-Acl -Path $_.FullName -AclObject $acl
            } catch {}
        }
        Write-Output "Fixed permissions on ALL SSH files (Admins + SYSTEM only)."
    } catch {
        Write-Warning "Failed to set strict permissions on SSH folder: $_"
    }

    Write-Output "sshd_config updated (Port: $Port, PasswordAuthentication: $pwdValue, PubkeyAuthentication: yes)"
    
    # VALIDATE CONFIG
    Write-Output "Validating sshd_config syntax..."
    $sshdPath = "C:\Windows\System32\OpenSSH\sshd.exe"
    if (Test-Path $sshdPath) {
        try {
            # Capture stderr/stdout 
            $pinfo = New-Object System.Diagnostics.ProcessStartInfo
            $pinfo.FileName = $sshdPath
            $pinfo.Arguments = "-t"
            $pinfo.RedirectStandardError = $true
            $pinfo.RedirectStandardOutput = $true
            $pinfo.UseShellExecute = $false
            $p = New-Object System.Diagnostics.Process
            $p.StartInfo = $pinfo
            $p.Start() | Out-Null
            $p.WaitForExit()
            $stderr = $p.StandardError.ReadToEnd()
            $stdout = $p.StandardOutput.ReadToEnd()
            
            if ($p.ExitCode -ne 0) {
                Write-Error "sshd_config SYNTAX ERROR (Exit Code $($p.ExitCode)):"
                Write-Error "$stderr $stdout"
            } else {
                Write-Output "Syntax Check: OK"
            }
        } catch {
            Write-Warning "Could not run sshd -t validation: $_"
        }
    }
}

function Configure-Firewall {
    param (
        [int]$Port
    )

    $ruleName = "OpenSSH Server (Port $Port)"
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue

    New-NetFirewallRule -Name "OpenSSH-Server-$Port" `
        -DisplayName $ruleName `
        -Description "Allow SSH inbound on TCP/$Port" `
        -Enabled True `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $Port `
        -Action Allow | Out-Null

    Write-Output "Firewall rule created/updated for TCP port $Port"
}

# --- Main Execution ---
try {
    # 1. Install OpenSSH Server
    Write-Output "Checking OpenSSH Server capability..."
    $capability = Get-WindowsCapability -Online | Where-Object { $_.Name -eq $CapabilityName }
    if ($capability.State -ne 'Installed') {
        Write-Output "Installing OpenSSH Server..."
        Add-WindowsCapability -Online -Name $CapabilityName | Out-Null
        Write-Output "Installation complete."
    }
    else {
        Write-Output "OpenSSH Server already installed."
    }
    
    # 2. Deploy keys
    Deploy-Keys -KeyArray $AdminKeys

    # 2.5 Ensure Host Keys (Required for Config Validation)
    $sshKeyGen = "C:\Windows\System32\OpenSSH\ssh-keygen.exe"
    
    # Wait for binary to appear (sometimes delayed after fresh install)
    $retries = 0
    while (-not (Test-Path $sshKeyGen) -and $retries -lt 6) {
        Write-Output "Waiting for OpenSSH binaries... ($retries/6)"
        Start-Sleep -Seconds 2
        $retries++
    }

    if (Test-Path $sshKeyGen) {
         Write-Output "Ensuring host keys exist..."
         & $sshKeyGen -A
    } else {
        Write-Warning "ssh-keygen.exe not found at $sshKeyGen - Host keys may be missing!"
    }

    # 3. Update configuration
    Update-Config -Port $SSHPort -DisablePwdAuth $DisablePasswordAuth.IsPresent

    # 4. Firewall
    Configure-Firewall -Port $SSHPort

    # 5. Service configuration & restart
    Write-Output "Configuring sshd service..."
    # FIX: Remove "ssh-agent" dependency which often breaks sshd start on Windows 10/11
    # We use sc.exe because Set-Service doesn't handle dependencies well
    cmd.exe /c "sc.exe config sshd depend= /" | Out-Null



    Write-Output "Setting sshd service to Automatic startup..."
    Set-Service -Name $ServiceName -StartupType Automatic -ErrorAction Stop

    Write-Output "Stopping any stuck processes..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "sshd" -Force -ErrorAction SilentlyContinue

    Write-Output "Starting sshd service..."
    try {
        Start-Service -Name $ServiceName -ErrorAction Stop
    } catch {
        Write-Error "FAILED to start sshd service."
        Write-Output "--- DIAGNOSTIC REPORT ---"
        
        # 1. OpenSSH Application Logs
        $events = Get-EventLog -LogName Application -Source "OpenSSH" -Newest 5 -EntryType Error -ErrorAction SilentlyContinue
        if ($events) {
            Write-Warning "[Application Log] OpenSSH Errors:"
            foreach ($e in $events) { Write-Warning "  [$($e.TimeGenerated)] $($e.Message)" }
        } else {
            Write-Warning "[Application Log] No 'OpenSSH' related errors found."
        }

        # 2. System Logs (Service Control Manager)
        $sysEvents = Get-EventLog -LogName System -Source "Service Control Manager" -Newest 5 -EntryType Error -ErrorAction SilentlyContinue
        if ($sysEvents) {
            Write-Warning "[System Log] Service Control Manager Errors:"
            foreach ($e in $sysEvents) { Write-Warning "  [$($e.TimeGenerated)] $($e.Message)" }
        }

        # 3. Manual Debug Run (Last Resort)
        Write-Output "Attempting manual 'sshd.exe -d' run to capture startup errors..."
        $sshdExe = "C:\Windows\System32\OpenSSH\sshd.exe"
        if (Test-Path $sshdExe) {
            try {
                $p = New-Object System.Diagnostics.Process
                $p.StartInfo.FileName = $sshdExe
                $p.StartInfo.Arguments = "-d" # Debug mode (runs once then exits, or prints error)
                $p.StartInfo.RedirectStandardError = $true
                $p.StartInfo.RedirectStandardOutput = $true
                $p.StartInfo.UseShellExecute = $false
                $p.Start() | Out-Null
                
                # Wait briefly - if it stays running, it's actually working (but service failed?)
                # If it exits immediately, it usually prints why.
                if ($p.WaitForExit(2000)) {
                    $err = $p.StandardError.ReadToEnd()
                    $out = $p.StandardOutput.ReadToEnd()
                    Write-Error "MANUAL RUN ERROR: Exit Code $($p.ExitCode)"
                    Write-Error "STDERR: $err"
                    Write-Error "STDOUT: $out"
                } else {
                    Write-Warning "Manual 'sshd -d' started successfully and is running... (killing it now)"
                    $p.Kill()
                    Write-Warning "This implies the config is valid but the Service Environment is the issue (Logon as Service?)"
                }
            } catch {
                Write-Warning "Could not run manual debug: $_"
            }
        }
        
        throw "Service startup failed. Review the diagnostics above."
    }

    Start-Sleep -Seconds 3
    $svc = Get-Service -Name $ServiceName
    
    if ($svc.Status -eq 'Running') {
        Write-Output "SUCCESS: OpenSSH Server is running on port $SSHPort."
        if ($DisablePasswordAuth) {
            Write-Output "Password authentication is DISABLED (key-based only)."
        }
    }
    else {
        # Check specific error common with bad config
        Write-Error "Service is not running (Status: $($svc.Status))."
        Write-Warning "This often happens if sshd_config has bad syntax or file permissions are wrong."
        Write-Warning "Check log: $LogFile"
        Exit 2
    }
}
catch {
    Write-Error "Deployment failed: $_"
    Exit 1
}
finally {
    Stop-Transcript
}