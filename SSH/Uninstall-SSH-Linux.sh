#!/bin/bash

# WINTOOLS: Uninstall-SSH-Linux.sh
# --------------------------------
# Removes OpenSSH Server and cleans up configuration.

set -e

# 1. Check for Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Uninstall-SSH-Linux.sh)"
  exit 1
fi

echo "⚠️  WARNING: This will remove the OpenSSH Server package and revert configuration."
read -p "Are you sure? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cancelled."
    exit 0
fi

# 2. Stop Service
echo "--- Stopping SSH Service ---"
if systemctl is-active --quiet ssh; then systemctl stop ssh; fi
if systemctl is-active --quiet sshd; then systemctl stop sshd; fi

# 3. Uninstall Package
echo "--- Removing OpenSSH Server ---"
if command -v apt-get &> /dev/null; then
    apt-get remove -y openssh-server
    apt-get autoremove -y
elif command -v dnf &> /dev/null; then
    dnf remove -y openssh-server
elif command -v yum &> /dev/null; then
    yum remove -y openssh-server
else
    echo "⚠️  Package manager not found. Skipping package removal."
fi

# 4. Optional: Remove Config (User Choice?)
# We usually leave /etc/ssh for safety unless explicitly asked to purge, 
# but for a "Clean Uninstall" we might want to rename it.
if [ -d "/etc/ssh" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    mv /etc/ssh "/etc/ssh_backup_$TIMESTAMP"
    echo "📦 Backed up /etc/ssh to /etc/ssh_backup_$TIMESTAMP"
fi

echo "✅ Success! OpenSSH Server uninstalled."
echo "   (Note: User keys in ~/.ssh/authorized_keys were NOT removed to prevent accidental lockout if re-installed)"
