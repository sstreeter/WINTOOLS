<#
.SYNOPSIS
    Disables Remote Desktop Shadowing (Screen Sharing) and reverts configuration.

.DESCRIPTION
    Reverts changes made by Enable-ShadowSupport.ps1:
    - Sets Registry "Rules for Remote Control" to Disabled (0).
    - Disables Remote Desktop (fDenyTSConnections = 1).
    - Disables Windows Firewall Rules for Remote Desktop.

.PARAMETER KeepRDPEnabled
    If $true, disables Shadowing but keeps standard RDP enabled. Default is $false (Disable Everything).

.NOTES
    Version: 1.0
    Author: Antigravity
#>

param (
    [switch]$KeepRDPEnabled
)

# --- Administrator Check ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "This script must be run as Administrator."
    Exit 1
}

$RegistryPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services"

# 1. Disable Shadow Policy
Write-Output "Disabling Shadow Policy..."
if (Test-Path $RegistryPath) {
    Set-ItemProperty -Path $RegistryPath -Name "Shadow" -Value 0 -Type DWord -Force
    Write-Output "Shadowing (Remote Control) is now DISABLED."
}

# 2. Disable Remote Desktop Connections (Optional)
if (-not $KeepRDPEnabled) {
    Write-Output "Disabling Remote Desktop Connections..."
    $RDPPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server"
    Set-ItemProperty -Path $RDPPath -Name "fDenyTSConnections" -Value 1 -Force
    
    # 3. Disable Firewall Rules
    Write-Output "Disabling Firewall Rules (Remote Desktop Group)..."
    Disable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
    Disable-NetFirewallRule -DisplayGroup "File and Printer Sharing" -ErrorAction SilentlyContinue
    
    Write-Output "Remote Desktop Access is now BLOCKED."
}
else {
    Write-Output "Keeping Standard RDP Enabled (as requested)."
}

Write-Output "Cleanup Complete."
