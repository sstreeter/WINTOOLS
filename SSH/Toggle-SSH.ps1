<#
.SYNOPSIS
    Toggles the OpenSSH Server (sshd) On or Off, supports temporary JIT keys.

.PARAMETER State
    'On' to start, 'Off' to stop.

.PARAMETER Keys
    Array of temporary admin keys to deploy (JIT / break-glass).

.NOTES
    Version: 2.0
#>

param (
    [ValidateSet("On", "Off")]
    [string]$State = "On",
    [string[]]$Keys = @()
)

$ServiceName = "sshd"
$SSHDataPath = "$env:ProgramData\ssh"
$AuthorizedKeysPath = Join-Path $SSHDataPath "administrators_authorized_keys"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Run as Administrator"
    Exit 1
}

function Deploy-Keys {
    param ([string[]]$KeyArray)
    if (-not (Test-Path $SSHDataPath)) { New-Item -ItemType Directory -Path $SSHDataPath -Force | Out-Null }
    if ($KeyArray.Count -gt 0) {
        $KeyArray | Set-Content -Path $AuthorizedKeysPath -Force
        Write-Output "Deployed $($KeyArray.Count) key(s)"
        $acl = New-Object System.Security.AccessControl.FileSecurity
        $acl.SetAccessRuleProtection($true, $false)
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Administrators", "FullControl", "Allow")))
        $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM", "FullControl", "Allow")))
        Set-Acl -Path $AuthorizedKeysPath -AclObject $acl
    }
}

if ($State -eq "On") {
    Write-Output "Enabling SSH..."
    Set-Service -Name $ServiceName -StartupType Automatic
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    Deploy-Keys -KeyArray $Keys
    Write-Output "SSH is ACTIVE."
}
else {
    Write-Output "Disabling SSH..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    Set-Service -Name $ServiceName -StartupType Disabled
    if (Test-Path $AuthorizedKeysPath) { Remove-Item $AuthorizedKeysPath -Force; Write-Output "Removed temporary keys" }
    Write-Output "SSH is INACTIVE."
}