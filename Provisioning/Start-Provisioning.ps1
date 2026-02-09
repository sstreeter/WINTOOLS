# Start-Provisioning.ps1
<#
.SYNOPSIS
    Orchestrates the provisioning of new Windows workstations.
.DESCRIPTION
    Standardizes computer naming, user account creation, and service configuration (RDP/SSH).
#>
Set-StrictMode -Version Latest

param(
    [Parameter(Mandatory=$false)]
    [string]$TargetUser = "Admin",

    [Parameter(Mandatory=$false)]
    [string]$TargetDisplayName = "Administrator",

    [switch]$DebugMode,
    [switch]$ForceProfileDelete
)

# 1. Import Module
$ModulePath = Join-Path -Path $PSScriptRoot -ChildPath "Modules\Provisioning.psm1"
Write-Host "Importing Provisioning Module..."
try {
    Import-Module -Name $ModulePath -Force -ErrorAction Stop
} catch {
    Write-Error "Failed to import module from $ModulePath"
    Exit 1
}

# 2. Main Logic
try {
    Initialize-ProvisioningModule -TargetUser $TargetUser -TargetDisplayName $TargetDisplayName -DebugMode:$DebugMode -ForceProfileDelete:$ForceProfileDelete

    if (-not (Test-ProvisioningPreflightChecks)) {
        Show-ProvisioningSummary
        Save-ProvisioningLog
        Exit 1
    }

    $selectedTasks = Show-ProvisioningMainMenu
    
    foreach ($taskName in $selectedTasks.Keys) {
        if ($selectedTasks[$taskName]) {
            Write-Host "`n=== Executing '$taskName' ==="
            switch ($taskName) {
                "User Management" {
                    $pass = Read-Host "Enter password for '$TargetUser' (Secure)" -AsSecureString
                    Perform-ProvisioningUserManagement -SecurePassword $pass
                }
                "Computer Rename" {
                    $dept = Read-Host "Enter Department/Lab Code (e.g. BIO, SHA)"
                    $name = Read-Host "Enter Computer Base Name"
                    Perform-ProvisioningComputerRename -DeptCode $dept -BaseName $name
                }
                "Remote Desktop (RDP)"     { Perform-ProvisioningRemoteDesktop -Enable:$true }
                "Always-On Power Settings" { Perform-ProvisioningPowerSettings -Enable:$true }
                "OpenSSH Server (SSH)"     { Perform-ProvisioningOpenSsh -Enable:$true }
                "Windows Activation" {
                    $keys = Get-ProvisioningKmsKeys
                    foreach ($k in $keys.Keys) { Write-Host "$k) $($keys[$k].Description)" }
                    $choice = Read-Host "Select edition (or 'C' to Cancel)"
                    if ($choice -ne 'C' -and $keys.ContainsKey($choice)) {
                        Perform-ProvisioningActivation -Key $keys[$choice].Key -Description $keys[$choice].Description
                    }
                }
            }
        }
    }
} catch {
    Write-Error "Unexpected error: $($_.Exception.Message)"
    Perform-ProvisioningRollback
} finally {
    Show-ProvisioningSummary
    Save-ProvisioningLog
}
