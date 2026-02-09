<#
.SYNOPSIS
    Enables Remote Desktop Shadowing (Screen Sharing) on the endpoint.

.DESCRIPTION
    Configures the machine to allow an administrator to view or control a user's session remotely.
    - Sets Group Policy/Registry for "Rules for Remote Control"
    - Enables Remote Desktop (fDenyTSConnections = 0)
    - Configures Windows Firewall Rules

.PARAMETER Mode
    'Consent' (Default): User must accept the connection request.
    'NoConsent': Admin connects immediately (Silent). Use with caution.
    'ViewOnly': Admin can see but not control mouse/keyboard.

.NOTES
    Version: 1.0
    Author: Antigravity
#>

param (
    [ValidateSet("Consent", "NoConsent", "ViewOnly", "ViewNoConsent")]
    [string]$Mode = "Consent",

    [switch]$Silent
)

# --- Administrator Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script must be run as Administrator."
    Exit 1
}

# --- OS Compatibility Check ---
# New-NetFirewallRule requires Windows 8 / Server 2012 or later.
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 6 -or ($osVersion.Major -eq 6 -and $osVersion.Minor -lt 2)) {
    Write-Warning "This script requires Windows 8+, Windows 10, or Windows 11. Your version: $($osVersion.Major).$($osVersion.Minor)."
    Write-Warning "New-NetFirewallRule cmdlets are not available."
    Write-Warning "Exiting gracefully."
    Exit 0
}

$RegistryPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services"

# Registry Mapping
# 0 = Disable
# 1 = Full Control with permission (Consent)
# 2 = Full Control without permission (NoConsent)
# 3 = View with permission (ViewOnly)
# 4 = View without permission (ViewNoConsent)

switch ($Mode) {
    "Consent"       { $ShadowValue = 1 }
    "NoConsent"     { $ShadowValue = 2 }
    "ViewOnly"      { $ShadowValue = 3 }
    "ViewNoConsent" { $ShadowValue = 4 }
}

Write-Output "Configuring Shadow Policy to: $Mode ($ShadowValue)..."

# 1. Set Registry Policy (Global)
if (-not (Test-Path $RegistryPath)) { New-Item -Path $RegistryPath -Force | Out-Null }
Set-ItemProperty -Path $RegistryPath -Name "Shadow" -Value $ShadowValue -Type DWord -Force
Write-Output "Registry policy set."

# 1.5 Set RDP-Tcp Specific Setting (Often Immediate)
$TcpPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
if (Test-Path $TcpPath) {
    Set-ItemProperty -Path $TcpPath -Name "Shadow" -Value $ShadowValue -Type DWord -Force
    Write-Output "RDP-Tcp Connection setting updated (Should be immediate for new connections)."
}

# 2. Enable Remote Desktop Connections
$RDPPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
Set-ItemProperty -Path $RDPPath -Name "fDenyTSConnections" -Value 0 -Force
Write-Output "Remote Desktop connections enabled."

# 3. Configure Firewall
# We need 'Remote Desktop - Shadow (TCP-In)'. 
# Note: Newer Windows versions might group this differently, but 'Remote Desktop' group covers it.
# Let's ensure the 'Remote Desktop' group is allowed for Domain/Private.

Write-Output "Enabling Firewall Rules (Remote Desktop Group)..."
Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue

# Ensure Shadow specifically is allowed if present as separate rule (rare, usually part of group)
# Typically uses dynamic ports negotiated over SMB/RPC.
# So File/Printer Sharing (SMB) might also be needed for initial enumeration.
Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing" -ErrorAction SilentlyContinue

# Result Output
if (-not $Silent) {
    Write-Output "Configuration Complete. Shadowing is ready."
}
else {
    # Exit code for automation
    Exit 0
}
