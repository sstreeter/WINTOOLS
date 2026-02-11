#!/bin/bash

# WINTOOLS: Uninstall-SSH-Mac.sh
# ------------------------------
# Disables Remote Login and cleans up configuration.

set -e

# 1. Check for Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Uninstall-SSH-Mac.sh)"
  exit 1
fi

echo "⚠️  WARNING: This will Disable Remote Login (SSH) on this Mac."
read -p "Are you sure? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Cancelled."
    exit 0
fi

# 2. Disable Remote Login
echo "--- Disabling Remote Login ---"
systemsetup -setremotelogin off

echo "✅ Success! Remote Login disabled."
echo "   (Note: User keys in ~/.ssh/authorized_keys were NOT removed to prevent data loss)"
