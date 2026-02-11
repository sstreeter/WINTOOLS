# WINTOOLS: SSH Module 🔐

Deploy, manage, and secure **OpenSSH Server** on Windows 10/11 endpoints.

## 📜 Included Scripts

| Script | Description |
| :--- | :--- |
| **[SSH_Key_Wizard.py](SSH_Key_Wizard.py)** | **(Admin Local)** Cross-platform Wizard. Generates secure Ed25519 keys, backs up old ones, and helps you organize them for deployment. **Now with improved sorting!** |
| **[Deploy-SSH-Windows.ps1](Deploy-SSH-Windows.ps1)** | **(Endpoint)** Installs OpenSSH, configures Port 22, deploys keys, and sets firewall rules. Includes **Deep Diagnostics** for troubleshooting service failures. |
| **[Toggle-SSH-Windows.ps1](Toggle-SSH-Windows.ps1)** | **(Endpoint)** Quickly Enable/Disable SSH service. Supports Just-In-Time (JIT) access. |
| **[Uninstall-SSH-Windows.ps1](Uninstall-SSH-Windows.ps1)** | **(Endpoint)** Completely removes OpenSSH (Service, Firewall, Keys). |

## 🚀 Workflow

### Step 1: Generate Keys (Admin PC)
Run the Wizard on your secure admin workstation.
```bash
python SSH_Key_Wizard.py
```
This generates your identity keys in `AuthorizedKeys/`.

> [!TIP]
> **New:** The wizard prioritizes key sorting, placing any "Undated" or manually added keys at the top of the history list for easy review.

### Step 2: Client Setup (Where to put your keys?)
You must have the **Private Key** on the computer you are connecting *from*.

| OS | Standard Location | Command to Connect |
| :--- | :--- | :--- |
| **Windows** | `C:\Users\You\.ssh\` | `ssh user@host` |
| **Mac/Linux** | `~/.ssh/` | `ssh user@host` |
| **Any (Custom)** | *Anywhere* | `ssh -i path/to/key user@host` |

> [!IMPORTANT]
> On Mac/Linux, you must secure the key permissions: `chmod 600 ~/.ssh/id_ed25519`

#### Managing Multiple Keys (Best Practice)
If the wizard generated a key like `id_ed25519_hostname_user`, SSH won't use it automatically. You must tell it to!
Create or edit `~/.ssh/config`:

```text
# ~/.ssh/config
Host my-server
    HostName 10.0.0.190
    User admin
    IdentityFile ~/.ssh/id_ed25519_hostname_user

Host home-pc
    HostName 192.168.1.5
    User spencer
    IdentityFile ~/.ssh/id_ed25519_personal
```
Now you can just type: `ssh my-server`

### Step 3: Deploy

#### Option A: Manual Deployment (Small Scale)
1.  At the end of the Wizard, answer **Yes** to "Create Deployment Package?".
2.  Copy the generated `Deploy-Package-<hostname>.zip` to the target machine.
3.  Unzip it on the target machine.
4.  Right-click `Deploy-SSH-Windows.ps1` and select **Run with PowerShell**. 
    *   *Alternatively, run as Admin:*
        ```powershell
        powershell -ExecutionPolicy Bypass -File .\Deploy-SSH-Windows.ps1 -KeysFile .\AuthorizedKeysPayload.txt -DisablePasswordAuth
        ```

#### Option B: Enterprise Deployment (Intune / Tanium)
For mass deployment, push the `Deploy-SSH-Windows.ps1` script and your master `AuthorizedKeysPayload.txt` to `C:\ProgramData\WINTOOLS\Scripts`.
Run as **System** or **Administrator**.

## ❓ Troubleshooting & FAQ

### 1. "Service terminated unexpectedly" / Failed to start?
The `Deploy-SSH-Windows.ps1` script now includes **Deep Diagnostics**.
If the service fails, the script will automatically:
1.  Dump "Service Control Manager" errors from the System Event Log.
2.  Attempt to run `sshd.exe -d` (Debug Mode) manually to catch permission errors.

**Common Fix:** The script automatically fixes permissions on `C:\ProgramData\ssh`. If you still have issues, ensure the `SYSTEM` account has Full Control over this folder.

### 2. "Permission denied (publickey)"?
This means the server is running but rejected your key.
1.  **Check Client Config**: Are you using the right private key? Use `ssh -v user@host` to see what key is being offered.
2.  **Check Admin Status**: By default, `administrators_authorized_keys` is used. If you are logging in as a non-admin, you need to configure standard `authorized_keys`.

### 3. I can't SSH in! How do I fix it?
If you lost access:
1.  Log in via RDP/Console.
2.  Run `powershell -ExecutionPolicy Bypass -File .\Uninstall-SSH-Windows.ps1`.
3.  Re-run deployment.