#!/bin/bash

# WINTOOLS: Deploy-Linux.sh
# -------------------------
# Installs OpenSSH Server and configures authorized keys.
# Supports: Debian/Ubuntu (apt), RHEL/CentOS (yum/dnf)

set -e  # Exit on error

# 1. Check for Root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./Deploy-Linux.sh)"
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
    # Try argument
    if [ -n "$1" ]; then
        KEYS_FILE="$1"
    else
        echo "❌ Error: Could not find 'AuthorizedKeysPayload.txt' in current directory."
        echo "   Usage: sudo ./Deploy-Linux.sh [path_to_keys_file]"
        exit 1
    fi
fi

echo "✅ Found Keys File: $KEYS_FILE"

# 3. Install OpenSSH Server (if missing)
echo "--- Checking OpenSSH Server ---"
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    apt-get update -q
    apt-get install -y -q openssh-server
    systemctl enable ssh
    systemctl start ssh
elif command -v dnf &> /dev/null; then
    # Fedora/RHEL 8+
    dnf install -y openssh-server
    systemctl enable sshd
    systemctl start sshd
elif command -v yum &> /dev/null; then
    # CentOS/RHEL 7
    yum install -y openssh-server
    systemctl enable sshd
    systemctl start sshd
else
    echo "⚠️  Package manager not found. Assuming OpenSSH is pre-installed."
fi

# 4. Configure User
# We install keys for the USER who invoked sudo (SUDO_USER) or current root if normal
TARGET_USER="${SUDO_USER:-$USER}"
USER_HOME=$(eval echo "~$TARGET_USER")
SSH_DIR="$USER_HOME/.ssh"
AUTH_KEYS="$SSH_DIR/authorized_keys"

echo "--- Installing Keys for User: $TARGET_USER ---"
echo "    Target: $AUTH_KEYS"

# Create .ssh
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
chown "$TARGET_USER:$TARGET_USER" "$SSH_DIR"

# Append Keys
# Ensure newline before appending
if [ -f "$AUTH_KEYS" ] && [ -s "$AUTH_KEYS" ] && [ "$(tail -c1 "$AUTH_KEYS" | wc -l)" -eq 0 ]; then
    echo "" >> "$AUTH_KEYS"
fi

cat "$KEYS_FILE" >> "$AUTH_KEYS"

# Fix Permissions
chmod 600 "$AUTH_KEYS"
chown "$TARGET_USER:$TARGET_USER" "$AUTH_KEYS"

echo "✅ Success! Valid keys have been added."
echo "   You can now connect via: ssh $TARGET_USER@$(hostname -I | awk '{print $1}')"
