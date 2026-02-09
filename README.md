# WINTOOLS 🛠️

A collection of Windows automations for Help Desk and System Administration.

## 📂 Modules

### 1. **[SSH](SSH/)** 🔐
Deploy and manage **OpenSSH Server** on Windows endpoints.
*   **Key Features**: Ed25519 Keys, JIT Access, secure firewall rules.
*   **Scripts**: `SSH_Key_Wizard.py`, `Deploy-OpenSSH.ps1`, `Toggle-SSH.ps1`.

### 2. **[RemotePC](RemotePC/)** 👥
Enable **RDP Shadowing** for remote assistance (View/Control user sessions).
*   **Key Features**: Helper tools for connecting to user sessions without interrupting them.
*   **Scripts**: `Enable-RemotePC.ps1`, `Connect-RemotePC.ps1`.

### 4. **[IconForge](IconForge/)** 🎨
Professional icon creation utility with advanced masking and edge processing.
*   **Key Features**: Background removal, edge "defringing", Windows ICO/Mac ICNS export.
*   **Scripts**: `IconForge.py`.

### 5. **[NetScan](NetScan/)** 🔍
Cross-platform network discovery and topology mapping.
*   **Key Features**: Subnet scanning, vendor identification, graph visualization.
*   **Scripts**: `NetScan.py`.

### 5. **[WINUSB](WINUSB/)** 🔌
A tool for managing and displaying USB device information on Windows.
*   **Key Features**: Device detection, driver info, and topology visualization.
*   **Scripts**: `winusb.py`.

---
## 🏗️ Architecture: Master Orchestrator
**WINTOOLS** uses a modular delegation pattern. The **[Provisioning](Provisioning/)** module acts as the central director for new workstation setups, delegating specialized tasks (like SSH and Remote Desktop hardening) to the standalone module scripts. This ensures a single source of truth for all security configurations.

---
## 📜 Third-Party Credits
**WINTOOLS** stands on the shoulders of these excellent open-source projects:

| Module | Dependency | License |
| :--- | :--- | :--- |
| **IconForge** | PyQt6, Pillow, NumPy, SciPy | GPLv3, HPND, BSD |
| **WINUSB** | wimlib, diskutil, hdiutil | GPLv3+, BSD |
| **SSH** | OpenSSH Server (Windows) | BSD/MIT |
| **NetScan** | Scapy (Optional) / Socket | GPLv2 / PSF |

---
## 👤 Project Lead & Attribution
**WINTOOLS** is developed and maintained by **Spencer Streeter**.

*   **GitHub**: [@sstreeter](https://github.com/sstreeter)
*   **Role**: Lead Architect & Maintainer

---
*Created for Professional Windows Administration.*
