# WINTOOLS: RemotePC 👥

Enable **RDP Shadowing** to view or control user sessions on Windows endpoints for remote support.

## 📜 Included Scripts

| Script | Description |
| :--- | :--- |
| **[Enable-RemotePC.ps1](Enable-RemotePC.ps1)** | **(Endpoint)** Configures Registry & Firewall to allow RDP Shadowing. |
| **[Connect-RemotePC.ps1](Connect-RemotePC.ps1)** | **(Admin Local)** Interactive tool to list remote sessions and launch `mstsc` to shadow them. |
| **[Disable-RemotePC.ps1](Disable-RemotePC.ps1)** | **(Endpoint)** Reverts Shadowing configuration and blocks RDP. |

## 🚀 Workflow

### Step 1: Enable on Endpoint
Deploy `Enable-RemotePC.ps1` to the target machine.
```powershell
.\Enable-RemotePC.ps1 -Mode Consent
```
*   **Consent**: User must click "Yes" to allow connection.

### Step 2: Connect (Admin PC)
Run the connector tool to help a user:
```powershell
.\Connect-RemotePC.ps1 -ComputerName "TARGET-PC"
```
1.  Enter the **Session ID** from the list.
2.  Launch Shadow Session.

### Step 3: Disable
When support is finished or no longer needed:
```powershell
.\Disable-RemotePC.ps1
```

## 💻 Compatibility
*   **Windows 10/11**: Fully Supported.
*   **Windows Server 2012+**: Supported.
