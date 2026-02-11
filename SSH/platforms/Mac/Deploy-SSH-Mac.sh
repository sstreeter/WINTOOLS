#!/bin/bash

# WINTOOLS: Deploy-Mac.sh
# -----------------------
# Enables Remote Login (SSH) and configures authorized keys.

set -e  # Exit on error

# 1. Check for Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Deploy-Mac.sh)"
  exit 1
fi

# 2. Get Keys File
KEYS_FILE=""
for f in *.txt; do
    if [[ "$f" == *"AuthorizedKeysPayload"* ]]; then
        KEYS_FILE="$f"
        break
    fi
done

if [ -z "$KEYS_FILE" ]; then
    if [ -n "$1" ]; then
        KEYS_FILE="$1"
    else
        echo "❌ Error: Could not find 'AuthorizedKeysPayload.txt'."
        echo "   Usage: sudo ./Deploy-Mac.sh [path_to_keys_file]"
        exit 1
    fi
fi

echo "✅ Found Keys File: $KEYS_FILE"

# 3. Enable Remote Login (SSH)
echo "--- Enabling Remote Login ---"
systemsetup -setremotelogin on

# 4. Configure User
TARGET_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo "~$TARGET_USER")
SSH_DIR="$USER_HOME/.ssh"
AUTH_KEYS="$SSH_DIR/authorized_keys"

echo "--- Installing Keys for User: $TARGET_USER ---"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
chown "$TARGET_USER:staff" "$SSH_DIR"

if [ -f "$AUTH_KEYS" ] && [ -s "$AUTH_KEYS" ] && [ "$(tail -c1 "$AUTH_KEYS" | wc -l)" -eq 0 ]; then
    echo "" >> "$AUTH_KEYS"
fi

cat "$KEYS_FILE" >> "$AUTH_KEYS"

chmod 600 "$AUTH_KEYS"
chown "$TARGET_USER:staff" "$AUTH_KEYS"

echo "✅ Success! Remote Login enabled and keys added."
echo "   Connect via: ssh $TARGET_USER@$(ipconfig getifaddr en0 || echo 'your-ip')"
