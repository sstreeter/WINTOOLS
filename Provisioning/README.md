# 🚀 WINTOOLS: Provisioning
Unified workstation setup and onboarding for Labs and Departments.

## 📋 Overview
The **Provisioning** module automates the initial setup of a fresh Windows workstation. It ensures consistent naming, account creation, and remote access configuration across the organization.

### Core Features
*   **User Management**: Creates a standardized administrator account and can optionally delete/cleanup legacy profiles.
*   **Host Naming**: Enforces naming standards (e.g., `DEPT-LAB-01`).
*   **Service Core**: Enables **Remote Desktop (RDP)** and **OpenSSH**.
*   **Optimization**: Sets "Always-On" power profiles for servers/lab machines.
*   **Activation**: One-click KMS activation for various Windows editions.
*   **Rollback Engine**: Safe execution with the ability to revert changes if an error occurs.

## 🛠️ Usage

### Quick Start
Run the orchestrator from an **Elevated PowerShell** prompt:

```powershell
# Default (Target user 'Admin')
.\Start-Provisioning.ps1

# Custom User for a different department
.\Start-Provisioning.ps1 -TargetUser "deptadmin" -TargetDisplayName "Department Admin"
```

### Parameters
| Parameter | Description |
| :--- | :--- |
| `-TargetUser` | The username for the local admin account to create/verify. |
| `-TargetDisplayName` | The full name for the user account. |
| `-ForceProfileDelete` | If specified, deletes local user profiles during account cleanup. |
| `-DebugMode` | Enables verbose logging and debug output. |

## 🔒 Safety & Privacy
*   **No Hardcoding**: This module uses parameters for sensitive names. Avoid modifying the source code to add permanent usernames.
*   **Log Files**: All execution logs (e.g., `Provisioning-*.log`) are ignored by source control to prevent accidental exposure of system details during the onboarding process.

## 📁 Structure
*   `Start-Provisioning.ps1`: The interactive entry point.
*   `Modules/Provisioning.psm1`: Core logic and helper functions.
*   `Modules/Provisioning.psd1`: Module manifest.
