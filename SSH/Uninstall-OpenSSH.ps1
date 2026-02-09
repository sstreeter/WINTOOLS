<#
.SYNOPSIS
    Fully uninstalls OpenSSH Server and cleans up configuration.

.DESCRIPTION
    Performs the following:
    1. Stops and disables the sshd service
    2. Removes OpenSSH firewall rules
    3. Uninstalls OpenSSH.Server Windows Capability
    4. Archives ssh configuration & keys to a timestamped backup

.NOTES
    Version: 2.0
    Author: Antigravity
    Date: 2026-01-21
#>

# --- Configuration ---
$ServiceName = "sshd"
$CapabilityName = "OpenSSH.Server~~~~0.0.1.0"
$FirewallRuleNamePattern = "OpenSSH-Server-Custom-*"
$SSHDataPath = "$env:ProgramData\ssh"
$AuthorizedKeysPath = Join-Path $SSHDataPath "administrators_authorized_keys"
# ---------------------

# --- Ensure script runs as Administrator ---
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script must be run as Administrator."
    Exit 1
}

try {
    # 1. Stop and Disable Service
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        Write-Output "Stopping $ServiceName service..."
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        Set-Service -Name $ServiceName -StartupType Disabled -ErrorAction SilentlyContinue
    }

    # 2. Remove Firewall Rules
    Write-Output "Removing firewall rules..."
    Remove-NetFirewallRule -Name $FirewallRuleNamePattern -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -DisplayName "OpenSSH Server Custom Port (*)" -ErrorAction SilentlyContinue

    # 3. Uninstall Capability
    Write-Output "Checking OpenSSH Server capability..."
    $capability = Get-WindowsCapability -Online | Where-Object { $_.Name -like $CapabilityName }
    
    if ($capability.State -eq 'Installed') {
        Write-Output "Uninstalling OpenSSH Server..."
        Remove-WindowsCapability -Online -Name $CapabilityName
    }
    else {
        Write-Output "OpenSSH Server is not installed."
    }

    # 4. Archive Config & Keys
    if (Test-Path $SSHDataPath) {
        $TimeStamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $BackupPath = "${SSHDataPath}_Backup_$TimeStamp"
        
        Write-Output "Archiving SSH data to $BackupPath ..."
        Rename-Item -Path $SSHDataPath -NewName $BackupPath -Force
    }

    Write-Output "Uninstallation complete. System is clean."
}
catch {
    Write-Error "An error occurred during uninstall: $_"
    Exit 1
}