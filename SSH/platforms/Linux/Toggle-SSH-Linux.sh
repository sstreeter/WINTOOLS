#!/bin/bash

# WINTOOLS: Toggle-SSH-Linux.sh
# -----------------------------
# Quickly Enable or Disable the SSH Service.
# Usage: sudo ./Toggle-SSH-Linux.sh [on|off]

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Toggle-SSH-Linux.sh)"
  exit 1
fi

MODE=$1

# Interactive mode if no arg provided
if [ -z "$MODE" ]; then
    echo "Current Status:"
    systemctl status ssh --no-pager | grep "Active:"
    echo ""
    read -p "Turn SSH [on] or [off]? " MODE
fi

MODE=$(echo "$MODE" | tr '[:upper:]' '[:lower:]')

if [ "$MODE" == "on" ]; then
    echo "--- Enabling SSH ---"
    if command -v systemctl &> /dev/null; then
        systemctl enable ssh --now || systemctl enable sshd --now
        echo "✅ SSH Service Started."
    else
        service ssh start || service sshd start
        echo "✅ SSH Service Started (Legacy init)."
    fi
elif [ "$MODE" == "off" ]; then
    echo "--- Disabling SSH ---"
    if command -v systemctl &> /dev/null; then
        systemctl disable ssh --now || systemctl disable sshd --now
        echo "zzZ SSH Service Stopped."
    else
        service ssh stop || service sshd stop
        echo "zzZ SSH Service Stopped (Legacy init)."
    fi
else
    echo "❌ Usage: sudo ./Toggle-SSH-Linux.sh [on|off]"
    exit 1
fi
