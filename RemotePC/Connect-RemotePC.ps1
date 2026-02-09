<#
.SYNOPSIS
    Connects to a remote shadow session (Screen Sharing).

.DESCRIPTION
    Lists active sessions on a target computer and launches mstsc /shadow to view/control a user's desktop.
    Requires 'Enable-ShadowSupport.ps1' to have been run on the target.

.PARAMETER ComputerName
    The hostname or IP address of the target computer.

.NOTES
    Version: 1.0
    Author: Antigravity
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$ComputerName
)

# 1. List Sessions
Write-Output "Querying sessions on $ComputerName..."
try {
    # qwinsta /server:ComputerName
    # Output format involves fixed width columns, tricky to parse perfectly but usually:
    # SESSIONNAME       USERNAME                 ID  STATE   TYPE        DEVICE
    # services                                    0  Disc
    # console           admin                     1  Active
    
    $sessions = qwinsta /server:$ComputerName 2>&1
    
    if ($sessions -match "RpcServer uses dynamic endpoints") {
        Write-Error "Could not connect to $ComputerName. Check RPC/Firewall."
        Exit 1
    }
    
    # Filter for interesting sessions (Active or ID > 0)
    $lines = $sessions | Where-Object { $_ -match "\s+\d+\s+" } # Lines with an ID
    
    if (-not $lines) {
        Write-Warning "No active sessions found."
        $sessions # Print raw output for debug
        Exit
    }
    
    Write-Output "`nAvailable Sessions:"
    write-host "----------------------------------------------------------------" -ForegroundColor Cyan
    $sessions | ForEach-Object { 
        if ($_ -match "SESSIONNAME") { Write-Host $_ -ForegroundColor Cyan }
        elseif ($_ -match "Active") { Write-Host $_ -ForegroundColor Green }
        else { Write-Host $_ }
    }
    write-host "----------------------------------------------------------------`n"
    
    # 2. Prompt for ID
    $SessionID = Read-Host "Enter Session ID to shadow (e.g. 1)"
    
    if (-not ($SessionID -match "^\d+$")) {
        Write-Error "Invalid Session ID."
        Exit
    }
    
    # 3. Connect
    $Control = Read-Host "Control? (Y/N) [Default: Y]"
    $ControlFlag = if ($Control -eq 'N') { "" } else { "/control" }
    
    $NoConsent = Read-Host "No Consent Prompt? (Y/N) [Default: N]"
    $NoConsentFlag = if ($NoConsent -eq 'Y') { "/noConsentPrompt" } else { "" }
    
    Write-Output "Launching Shadow Session..."
    $cmdArgs = "/shadow:$SessionID /v:$ComputerName $ControlFlag $NoConsentFlag"
    Write-Output "mstsc $cmdArgs"
    
    Start-Process "mstsc.exe" -ArgumentList $cmdArgs
    
}
catch {
    Write-Error "Error: $_"
}
