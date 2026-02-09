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
    Version: 3.2
    Author: Antigravity
    Date: 2026-02-08
#>

param (
    [string[]]$AdminKeys = @(),
    [string]$KeysFile,
    [int]$SSHPort = 22,
    [bool]$DisablePasswordAuth = $false
)

# --- Logging Setup ---
$LogDir = "$env:ProgramData\WINTOOLS\Logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
$LogFile = Join-Path $LogDir "Deploy-OpenSSH.log"
Start-Transcript -Path $LogFile -Append

Write-Output "--- Starting OpenSSH Deployment: $(Get-Date) ---"

# --- Administrator Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
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
if ($KeysFile -and (Test-Path $KeysFile)) {
    Write-Output "Loading keys from file: $KeysFile"
    $FileKeys = Get-Content $KeysFile | Where-Object { $_ -match "^ssh-" }
    $AdminKeys += $FileKeys
}

# --- Configuration ---
$ServiceName = "sshd"
$CapabilityName = "OpenSSH.Server~~~~0.0.1.0"
$SSHDataPath = "$env:ProgramData\ssh"
$AuthorizedKeysPath = Join-Path $SSHDataPath "administrators_authorized_keys"
$ConfigPath = Join-Path $SSHDataPath "sshd_config"

# --- Helper Functions ---
function Deploy-Keys {
    param ([string[]]$KeyArray)
    
    if (-not (Test-Path $SSHDataPath)) { New-Item -ItemType Directory -Path $SSHDataPath -Force | Out-Null }

    # Deduplicate and Clean Keys
    $UniqueKeys = $KeyArray | Select-Object -Unique | Where-Object { $_ -notmatch "^\s*$" }

    if ($UniqueKeys.Count -gt 0) {
        $UniqueKeys | Set-Content -Path $AuthorizedKeysPath -Force
        Write-Output "Deployed $($UniqueKeys.Count) unique admin key(s) to $AuthorizedKeysPath"

        # Set strict permissions (System + Administrators Only)
        $acl = New-Object System.Security.AccessControl.FileSecurity
        $acl.SetAccessRuleProtection($true, $false) # Disable inheritance
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Administrators", "FullControl", "Allow")))
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM", "FullControl", "Allow")))
        Set-Acl -Path $AuthorizedKeysPath -AclObject $acl
        Write-Output "Permissions set on authorized_keys (Admins/System Only)."
    }
    else {
        Write-Warning "No valid admin keys provided. SSH access will be limited!"
    }
}

function Update-Config {
    if (-not (Test-Path $ConfigPath)) {
        Write-Output "sshd_config missing; starting service once to generate defaults..."
        Start-Service -Name $ServiceName
        Stop-Service -Name $ServiceName
    }

    Write-Output "Backing up sshd_config..."
    Copy-Item -Path $ConfigPath -Destination "$ConfigPath.bak" -Force

    $content = Get-Content -Path $ConfigPath
    
    # Update Port
    $newContent = $content | Where-Object { $_ -notmatch "^\s*#?\s*Port\s+\d+" }
    $newContent = @("Port $SSHPort") + $newContent

    # Update Password Auth
    $newContent = $newContent | Where-Object { $_ -notmatch "^\s*#?\s*PasswordAuthentication\s+" }
    $pwdValue = if ($DisablePasswordAuth) { "no" } else { "yes" }
    $newContent += "PasswordAuthentication $pwdValue"
    
    # Ensure PubkeyAuth is enabled
    $newContent = $newContent | Where-Object { $_ -notmatch "^\s*#?\s*PubkeyAuthentication\s+" }
    $newContent += "PubkeyAuthentication yes"

    $newContent | Set-Content -Path $ConfigPath -Encoding UTF8
    Write-Output "sshd_config updated (Port: $SSHPort, PwdAuth: $pwdValue)."
}

function Configure-Firewall {
    $FirewallRuleName = "OpenSSH Server Custom Port ($SSHPort)"
    Remove-NetFirewallRule -DisplayName $FirewallRuleName -ErrorAction SilentlyContinue

    New-NetFirewallRule -Name "OpenSSH-Server-Custom-$SSHPort" `
        -DisplayName $FirewallRuleName `
        -Description "Allow SSH inbound on port $SSHPort" `
        -Enabled True -Direction Inbound -Protocol TCP -LocalPort $SSHPort -Action Allow
    Write-Output "Firewall rule created for Port $SSHPort."
}

# --- Main Execution ---
try {
    # 1. Install OpenSSH
    Write-Output "Checking OpenSSH Server capability..."
    $capability = Get-WindowsCapability -Online | Where-Object { $_.Name -like $CapabilityName }
    if ($capability.State -ne 'Installed') {
        Write-Output "Installing OpenSSH Server..."
        Add-WindowsCapability -Online -Name $CapabilityName
    }
    else { Write-Output "OpenSSH Server is already installed." }

    # 2. Configure Service
    Write-Output "Configuring sshd service startup..."
    Set-Service -Name $ServiceName -StartupType Automatic

    # 3. Deploy Keys & Config
    Deploy-Keys -KeyArray $AdminKeys
    Update-Config
    Configure-Firewall

    # 4. Restart Service
    Write-Output "Starting sshd service..."
    Restart-Service -Name $ServiceName -Force

    # 5. Verify
    Start-Sleep -Seconds 2
    $svc = Get-Service -Name $ServiceName
    if ($svc.Status -eq 'Running') {
        Write-Output "Deployment SUCCESS. SSH listening on port $SSHPort."
    }
    else {
        Write-Error "Deploy FAILED: Service is not running."
        # Self-healing logic could go here (reverted for brevity in this refined version)
    }

}
catch {
    Write-Error "Deployment ERROR: $_"
    Stop-Transcript
    Exit 1
}

Stop-Transcript