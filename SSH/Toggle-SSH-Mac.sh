#!/bin/bash

# WINTOOLS: Toggle-SSH-Mac.sh
# ---------------------------
# Quickly Enable or Disable Remote Login.
# Usage: sudo ./Toggle-SSH-Mac.sh [on|off]

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Toggle-SSH-Mac.sh)"
  exit 1
fi

MODE=$1

# Interactive mode if no arg provided
if [ -z "$MODE" ]; then
    echo "Current Status:"
    systemsetup -getremotelogin
    echo ""
    read -p "Turn Remote Login [on] or [off]? " MODE
fi

MODE=$(echo "$MODE" | tr '[:upper:]' '[:lower:]')

if [ "$MODE" == "on" ]; then
    echo "--- Enabling Remote Login ---"
    systemsetup -setremotelogin on
    echo "✅ Remote Login is now ON."
elif [ "$MODE" == "off" ]; then
    echo "--- Disabling Remote Login ---"
    systemsetup -setremotelogin off
    echo "zzZ Remote Login is now OFF."
else
    echo "❌ Usage: sudo ./Toggle-SSH-Mac.sh [on|off]"
    exit 1
fi
