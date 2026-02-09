# WINTOOLS: SSH Module 🔐

Deploy, manage, and secure **OpenSSH Server** on Windows 10/11 endpoints.

## 📜 Included Scripts

| Script | Description |
| :--- | :--- |
| **[SSH_Key_Wizard.py](SSH_Key_Wizard.py)** | **(Admin Local)** Cross-platform Wizard. Generates secure Ed25519 keys, backs up old ones, and helps you organize them for deployment. |
| **[Deploy-OpenSSH.ps1](Deploy-OpenSSH.ps1)** | **(Endpoint)** Installs OpenSSH, configures Port 22, deploys keys, and sets firewall rules. Logs to `C:\ProgramData\WINTOOLS\Logs`. |
| **[Toggle-SSH.ps1](Toggle-SSH.ps1)** | **(Endpoint)** Quickly Enable/Disable SSH service. Supports Just-In-Time (JIT) access. |
| **[Uninstall-OpenSSH.ps1](Uninstall-OpenSSH.ps1)** | **(Endpoint)** Completely removes OpenSSH (Service, Firewall, Keys). |

## 🚀 Workflow

### Step 1: Generate Keys (Admin PC)
Run the Wizard on your secure admin workstation.
```bash
python SSH_Key_Wizard.py
```
This generates your identity keys in `AuthorizedKeys/`.

> [!TIP]
> **New:** The wizard can now automatically create a `Deploy-Package-<device>.zip` containing all necessary scripts and keys. Just answer "Yes" when prompted!


### Step 2: Deploy

You have two options for deployment:

#### Option A: Manual Deployment (Small Scale)
If you are setting up a few machines manually:
1.  At the end of the Wizard, answer **Yes** to "Create Deployment Package?".
2.  Copy the generated `Deploy-Package-<hostname>.zip` to the target machine.
3.  Unzip it on the target machine.
4.  Right-click `Deploy-OpenSSH.ps1` and select **Run with PowerShell**. 
    *   *Alternatively, run as Admin:*
        ```powershell
        powershell -ExecutionPolicy Bypass -File .\Deploy-OpenSSH.ps1 -KeysFile .\AuthorizedKeysPayload.txt -DisablePasswordAuth $true
        ```


#### Option B: Enterprise Deployment (Intune / Tanium)
For mass deployment, push the `Deploy-OpenSSH.ps1` script and your master `AuthorizedKeysPayload.txt` to:
*   `C:\ProgramData\WINTOOLS\Scripts` (or your preferred staging area).
*   Run the script as **System** or **Administrator**.
*   **Command Line:**
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\Deploy-OpenSSH.ps1 -KeysFile .\AuthorizedKeysPayload.txt -DisablePasswordAuth $true
    ```



## 🌍 Multi-Device Strategy (Best Practice)

If you manage servers from multiple computers (e.g., **Work Laptop** and **Home PC**), follow this strategy:

## 🌍 Multi-Device Strategy (Best Practice)

If you manage servers from multiple computers (e.g., **Work Laptop** and **Home PC**), follow this strategy:

1.  **Run the Wizard on EACH Device**:
    *   On **Work Laptop**: Run `SSH_Key_Wizard.py`. Name device `laptop-campus` (or use the auto-detected Smart ID like `mba2023-campus`).
    *   On **Home PC**: Run `SSH_Key_Wizard.py`. Name device `desktop-wfh`.
    *   *Note: Device names are strictly limited to alphanumeric characters and hyphens (a-z, 0-9, -) to ensure compatibility.*
2.  **Consolidate the Payload**:
    *   The Wizard creates an `AuthorizedKeysPayload.txt` on each machine.
    *   **Combine them** into one master file.
    *   *Tip: Use `AuthorizedKeysPayload.example.txt` as a reference template.*

> [!CAUTION]
> **ACCIDENTAL COPYING WARNING**
> Do **NOT** copy the `SSH/` folder in its entirety to Endpoint PCs or unsecured locations.
> - The `AuthorizedKeys/` folder contains your **Private Keys** (Secrets).
> - The `History/` folder contains your **Archived Secrets**.
> - **Only** deploy the `Deploy-OpenSSH.ps1` script and the `AuthorizedKeysPayload.txt` (Public Keys) to target machines.

## 🔒 Security & Data Protection
To prevent accidental data leaks, this project uses a "Local-Only" configuration model:

*   **Automatic Protection**: The root `.gitignore` is configured to ignore all real keys (`*.key`, `*.pem`), the `AuthorizedKeys/` folder, and the production `AuthorizedKeysPayload.txt`.
*   **Your Responsibility**:
    *   **Real Data**: Edit `AuthorizedKeysPayload.txt` with your actual production keys. This file will be used during deployment but will stay local to your machine.
    *   **Shareable Data**: Only edit and commit `AuthorizedKeysPayload.example.txt` if you need to demonstrate the format to others.

> [!IMPORTANT]
> **NEVER** force-add private keys to your repository. Always use the deployment script to transfer them securely.
    *   Example Content:
        ```text
        # Key: id_ed25519_admin_work-laptop
        ssh-ed25519 AAAAC3Nza... admin@work-laptop
        # Key: id_ed25519_admin_home-pc
        ssh-ed25519 AAAAC3Nza... admin@home-pc
        ```
3.  **Deploy Once**:
    *   Use this master file with `Deploy-OpenSSH.ps1` on all your target servers.
    *   Now both your Laptop and Home PC can access all servers! 🚀

## 🔒 Security Best Practices

1.  **Identity is the New Perimeter**:
    *   **SSH**: Use **Ed25519 Keys** only. Disable Password Authentication (`-DisablePasswordAuth $true`).
    *   **RDP**: Require **Network Level Authentication (NLA)** (Default on modern Windows).
2.  **Standards**:
    *   We recommend using **Standard Ports** (SSH: 22, RDP: 3389).
    *   Use **Windows Firewall** to limit access to Admin Subnets.

## ❓ Troubleshooting & FAQ

### 1. Will this lock me out of the computer?
**No.**
*   The script only configures the **OpenSSH Server** application. It sets `PasswordAuthentication no` *only* for SSH connections.
*   It does **not** affect local Windows logins, Remote Desktop (RDP), or other services.
*   As long as you have local admin access (physical or RDP), you are safe.

### 2. I can't SSH in! How do I fix it?
If you lost your private key or the configuration is broken:
1.  Log in to the machine via RDP or Console.
2.  Run the **Uninstall Script**:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\Uninstall-OpenSSH.ps1
    ```
3.  This completely removes OpenSSH and its configuration. You can now start over.

### 3. "Permission denied (publickey)"
This means the server rejected your key. Common causes:
*   **Wrong Private Key:** Are you using the correct `id_ed25519` for this specific target?
*   **Permissions:** On macOS/Linux, run `chmod 600 ~/.ssh/id_ed25519`.
*   **Admin User:** Did you try to SSH as a non-admin? The default config limits access to the **Administrators** group.