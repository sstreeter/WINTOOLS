#!/usr/bin/env python3
"""
SSH Key Generation Wizard
-------------------------
A cross-platform tool to generate secure Ed25519 SSH keys for WINTOOLS deployment.
- Detects OS.
- Prompts for User and Platform.
- Handles Key Generation.
- Backs up existing keys (Safety).
- Provides clear instructions.
"""

import os
import sys
import platform
import subprocess
import shutil
import datetime
import argparse

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Logging ---
def log_action(message, level="INFO"):
    """Appends a timestamped entry to the wizard_audit.log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    # Log file resides in the same folder as the script
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wizard_audit.log")
    
    try:
        with open(log_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        # Fallback to stderr if log writing fails
        print(f"{Style.RED}Error writing to log: {e}{Style.RESET}", file=sys.stderr)

# --- UI Helpers ---
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

def print_header():
    clear_screen()
    print(f"{Style.BLUE}========================================{Style.RESET}")
    print(f"{Style.BOLD}      WINTOOLS: SSH Key Wizard 🧙‍♂️      {Style.RESET}")
    print(f"{Style.BLUE}========================================{Style.RESET}")
    print(f"{Style.DIM}Running on: {platform.system()} ({platform.release()}){Style.RESET}")
    print(f"{Style.BLUE}----------------------------------------{Style.RESET}")

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    """
    if total == 0: total = 1
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    # Rainbow effect slightly
    color = Style.CYAN if iteration < total else Style.GREEN
    print(f'\r{prefix} {color}|{bar}|{Style.RESET} {percent}% {suffix}', end=printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

class WizardExit(Exception): pass

def get_input(prompt, default=None, allow_empty=False):
    prompt_style = f"{Style.BOLD}{prompt}{Style.RESET}"
    if default:
        prompt_str = f"{prompt_style} [{default}]"
    else:
        prompt_str = prompt_style

    while True:
        try:
            user_input = input(f"{prompt_str}: ").strip()
        except EOFError:
            # Handle Ctrl+D gracefully
            raise WizardExit()
        except KeyboardInterrupt:
            # Handle Ctrl+C as Cancel
            print(f"\n{Style.YELLOW}⚠️  Operation Cancelled.{Style.RESET}")
            raise WizardExit()
        
        # Check for cancel command
        if user_input.lower() in ['cancel', 'exit', 'menu', 'quit']:
            print(f"\n{Style.YELLOW}⚠️  Operation Cancelled.{Style.RESET}")
            raise WizardExit()

        if user_input:
            return user_input
        
        if default is not None:
            return default
            
        if allow_empty:
            return ""
            
        # If we get here, input was empty, default was None, and allow_empty was False
        # Loop continues (implied 'required input')


def print_step(title):
    print(f"\n{Style.BOLD}{Style.CYAN}FEATURE:{Style.RESET} {title}")

def print_success(msg):
    print(f"{Style.GREEN}✅ {msg}{Style.RESET}")

def print_error(msg):
    print(f"{Style.RED}❌ {msg}{Style.RESET}")

def print_report_card(priv_path, pub_path, payload_path, added_to_payload):
    """Prints a stylish summary of the operation."""
    w = 60
    border = f"{Style.BLUE}" + "="*w + f"{Style.RESET}"
    thin_border = f"{Style.BLUE}" + "-"*w + f"{Style.RESET}"
    
    print("\n" + border)
    print(f"{Style.BOLD}{Style.GREEN}           🎉  GENERATION COMPLETE  🎉{Style.RESET}".center(w + 10)) # +10 for color codes length approx
    print(border)
    
    # Private Key
    print(f"\n{Style.BOLD}{Style.RED}🔒 PRIVATE KEY (SECRET){Style.RESET}")
    print(f"{Style.DIM}   Path: {priv_path}{Style.RESET}")
    print(f"   {Style.YELLOW}• DO NOT SHARE.{Style.RESET}")
    print(f"   {Style.YELLOW}• Store in Password Manager or Secure USB.{Style.RESET}")
    
    print(thin_border)
    
    # Public Key
    print(f"\n{Style.BOLD}{Style.GREEN}🌍 PUBLIC KEY (SHAREABLE){Style.RESET}")
    print(f"{Style.DIM}   Path: {pub_path}{Style.RESET}")
    print(f"   {Style.CYAN}• safe to publish.{Style.RESET}")
    print(f"   • {Style.BOLD}Action:{Style.RESET} Upload content to Tanium / Intune.")
    
    print(thin_border)
    
    # Deployment Check
    if added_to_payload:
        print(f"\n{Style.BOLD}{Style.MAGENTA}🚀 DEPLOYMENT READY{Style.RESET}")
        print(f"   Key added to: {Style.BOLD}{os.path.basename(payload_path)}{Style.RESET}")
        print(f"   {Style.DIM}(Use this file with Deploy-OpenSSH.ps1){Style.RESET}")
    else:
        print(f"\n{Style.BOLD}{Style.YELLOW}⚠️  PENDING DEPLOYMENT{Style.RESET}")
        print(f"   Key {Style.BOLD}NOT{Style.RESET} added to payload file.")
        print(f"   You must manually copy the public key content.")
        
    print(border + "\n")

def generate_key(user, target_platform, output_dir, interactive=True):
    # Naming Convention: id_ed25519_<platform>_<user>
    key_name = f"id_ed25519_{target_platform.lower()}_{user.lower()}"
    key_path = os.path.join(output_dir, key_name)
    pub_key_path = f"{key_path}.pub"
    
    # 1. Check for existing key
    if os.path.exists(key_path) or os.path.exists(pub_key_path):
        print(f"\n{Style.YELLOW}⚠️  Key '{key_name}' already exists!{Style.RESET}")
        if interactive:
            choice = get_input("Do you want to overwrite it? (yes/no)", "no")
            if choice.lower() != 'yes':
                print(f"{Style.DIM}Skipping generation.{Style.RESET}")
                return None, None
        
        # Backup Logic
        backup_dir = os.path.join(output_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if os.path.exists(key_path):
            backup_path = os.path.join(backup_dir, f"{key_name}_{timestamp}")
            shutil.move(key_path, backup_path)
            print(f"📦 Backed up old private key to: {os.path.basename(backup_path)}")
            
        if os.path.exists(pub_key_path):
            backup_pub = os.path.join(backup_dir, f"{key_name}_{timestamp}.pub")
            shutil.move(pub_key_path, backup_pub)
            print(f"📦 Backed up old public key to: {os.path.basename(backup_pub)}")

    # 2. Generate Key
    comment = f"{user}@{target_platform}-{datetime.date.today()}"
    print(f"\nGenerating Ed25519 Key Pair for {user}...")
    
    passphrase = ""
    if interactive:
        passphrase = get_input("Enter Passphrase (leave empty for none)", "")
    
    cmd = [
        "ssh-keygen", 
        "-t", "ed25519", 
        "-C", comment, 
        "-f", key_path, 
        "-N", passphrase,
        "-q"
    ]
    
    try:
        subprocess.run(cmd, check=True) # stdout/stderr allowed for q
        print_success(f"Key Generated: {key_name}")
        print_success(f"Key Generated: {key_name}")
        log_action(f"GENERATED NEW KEY: {key_name} (User: {user}, Device: {target_platform}) | Path: {key_path}")
        
        if interactive:
            install_local_key(key_path)
            
        return key_path, pub_key_path
    except subprocess.CalledProcessError as e:
        print_error(f"Error generating key: {e}")
        return None, None
    except FileNotFoundError:
        print_error("ssh-keygen command not found. Please install OpenSSH Client.")
        return None, None

def archive_current_state(output_dir):
    """Moves the entire current output directory into an archival history folder."""
    if not os.path.exists(output_dir):
        print(f"{Style.DIM}Nothing to archive (directory '{os.path.basename(output_dir)}' does not exist).{Style.RESET}")
        return

    # Check if directory is empty
    if not os.listdir(output_dir):
        print(f"{Style.DIM}Archive skipped (directory is empty).{Style.RESET}")
        return

    parent_dir = os.path.dirname(output_dir)
    history_dir = os.path.join(parent_dir, "History")
    os.makedirs(history_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_name = f"Archive_{timestamp}"
    archive_path = os.path.join(history_dir, archive_name)

    print(f"\n{Style.YELLOW}📦 Archiving current state to {Style.BOLD}History/{archive_name}{Style.RESET}...")
    
    try:
        shutil.move(output_dir, archive_path)
        print_success(f"State Archived. Starting fresh.")
        log_action(f"RESET/ARCHIVE: Current state moved to History/{archive_name}", "WARN")
        # Re-create empty directory for immediate use
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print_error(f"Failed to archive state: {e}")
def install_local_key(priv_key_path):
    """Offers to install the private key to the user's local .ssh directory."""
    
    # 1. Detect .ssh directory
    try:
        user_home = os.path.expanduser("~")
        ssh_dir = os.path.join(user_home, ".ssh")
    except Exception:
        # Fallback if expanduser fails (rare)
        return

    print(f"\n{Style.BOLD}--- Client Setup ---{Style.RESET}")
    print(f"Would you like to install the private key to your local SSH client?")
    print(f"   Source: {priv_key_path}")
    print(f"   Dest:   {os.path.join(ssh_dir, os.path.basename(priv_key_path))}")
    
    choice = get_input("Install Key? (yes/no)", "yes")
    if choice.lower() != "yes":
        return

    try:
        # 2. Create .ssh if missing
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
            print(f"   Created directory: {ssh_dir}")

        dest_path = os.path.join(ssh_dir, os.path.basename(priv_key_path))
        
        # 3. Check collision
        if os.path.exists(dest_path):
            overwrite = get_input(f"{Style.YELLOW}⚠️  Key file already exists! Overwrite? (yes/no){Style.RESET}", "no")
            if overwrite.lower() != 'yes':
                print("   Skipping installation.")
                return

        # 4. Copy
        shutil.copy2(priv_key_path, dest_path)
        print_success(f"Key installed to: {dest_path}")
        
        # 5. Fix Permissions (Posix only)
        if os.name == 'posix':
            try:
                os.chmod(dest_path, 0o600)
                print(f"   🔒 Permissions set to 600 (rw-------)")
            except Exception as e:
                print(f"   {Style.YELLOW}⚠️  Could not set permissions: {e}{Style.RESET}")
        elif os.name == 'nt':
            try:
                # Windows equivalent of 600: Remove inheritance, grant user Full Control
                user = os.environ.get('USERNAME', os.getlogin())
                subprocess.run(['icacls', dest_path, '/reset'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['icacls', dest_path, '/grant:r', f'{user}:F'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['icacls', dest_path, '/inheritance:r'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"   🔒 Windows ACLs restricted to '{user}'")
            except Exception as e:
                print(f"   {Style.YELLOW}⚠️  Could not set Windows ACLs: {e}{Style.RESET}")
                
        log_action(f"KEY INSTALLED: {dest_path}")
        
    except Exception as e:
        print_error(f"Failed to install key: {e}")
        get_input("Press Enter to continue...", allow_empty=True)
# --- Input Policy ---
class InputPolicy:
    """Centralized policy for input validation and sanitization."""
    
    MAX_HOSTNAME_LEN = 15
    MAX_USERNAME_LEN = 32
    
    @staticmethod
    def sanitize_hostname(hostname):
        """
        Sanitize device name to strict alphanumerics and hyphens.
        - Allowed: a-z, 0-9, -
        - Max Length: 15 chars (NetBIOS compatibility)
        - Case: Lowercase
        """
        import re
        if not hostname: return "unknown-device"
        
        # Strict: a-z, 0-9, -
        clean = re.sub(r'[^a-zA-Z0-9-]', '', str(hostname)).lower()
        clean = clean.strip('-')
        
        if len(clean) > InputPolicy.MAX_HOSTNAME_LEN:
             clean = clean[:InputPolicy.MAX_HOSTNAME_LEN]
             
        if not clean: return "unknown-device"
        return clean

    @staticmethod
    def sanitize_username(username):
        """
        Sanitize username to safe characters.
        - Allowed: a-z, 0-9, ., _, -
        - Max Length: 32 chars
        - Case: Lowercase
        """
        import re
        if not username: return "user"
        
        # Usernames often allow . _ -
        clean = re.sub(r'[^a-zA-Z0-9._-]', '', str(username)).lower()
        
        if len(clean) > InputPolicy.MAX_USERNAME_LEN:
             clean = clean[:InputPolicy.MAX_USERNAME_LEN]
             
        if not clean: return "user"
        return clean

def install_key_menu(default_dir):
    """Menu interface for installing local keys."""
    print(f"\n{Style.BOLD}🔧 Install/Repair Local Key:{Style.RESET}")
    
    # 1. Find Keys
    keys = [f for f in os.listdir(default_dir) if f.startswith("id_ed25519") and not f.endswith(".pub")]
    
    if not keys:
        print(f"   {Style.DIM}(No keys found in {default_dir}){Style.RESET}")
        get_input("Press Enter to return to menu", allow_empty=True)
        return

    # 2. Select Key
    print(f"Select a private key to install:")
    for i, name in enumerate(keys):
        print(f"   [{Style.CYAN}{i+1}{Style.RESET}] {name}")
    print(f"   [{Style.CYAN}0{Style.RESET}] Cancel")

    choice = get_input("\nSelect Key", "0")
    if choice == '0': return
    
    selected_key = ""
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(keys):
            selected_key = os.path.join(default_dir, keys[idx])
        else:
             return
    except: return

    # 3. Destination
    default_dest_dir = os.path.expanduser("~")
    try:
        default_dest_dir = os.path.join(os.path.expanduser("~"), ".ssh")
    except: pass
    
    print(f"\n{Style.BOLD}Where should this key go?{Style.RESET}")
    print(f"Default: {default_dest_dir}")
    print(f"(Enter a custom path or press Enter for default)")
    
    custom_dest = get_input("Destination Folder", allow_empty=True)
    if not custom_dest:
        dest_dir = default_dest_dir
    else:
        dest_dir = os.path.expanduser(custom_dest) # Handle ~/ expansion if user typed it
    
    # 4. Install Logic (Adapted from install_local_key but with custom dest)
    try:
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, mode=0o700, exist_ok=True)
                print(f"   Created directory: {dest_dir}")
            except Exception as e:
                print_error(f"Could not create directory '{dest_dir}': {e}")
                get_input("Press Enter", allow_empty=True)
                return

        dest_path = os.path.join(dest_dir, os.path.basename(selected_key))
        
        # Check collision
        if os.path.exists(dest_path):
            overwrite = get_input(f"{Style.YELLOW}⚠️  File '{os.path.basename(dest_path)}' exists! Overwrite? (yes/no){Style.RESET}", "no")
            if overwrite.lower() != 'yes':
                print("   Skipping.")
                get_input("Press Enter", allow_empty=True)
                return

        shutil.copy2(selected_key, dest_path)
        print_success(f"Key installed to: {dest_path}")
        
        if os.name == 'posix':
            try:
                os.chmod(dest_path, 0o600)
                print(f"   🔒 Permissions set to 600 (rw-------)")
            except Exception as e:
                print(f"   {Style.YELLOW}⚠️  Could not set permissions: {e}{Style.RESET}")
        elif os.name == 'nt':
            try:
                # Windows equivalent of 600: Remove inheritance, grant user Full Control
                user = os.environ.get('USERNAME', os.getlogin())
                subprocess.run(['icacls', dest_path, '/reset'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['icacls', dest_path, '/grant:r', f'{user}:F'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['icacls', dest_path, '/inheritance:r'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"   🔒 Windows ACLs restricted to '{user}'")
            except Exception as e:
                print(f"   {Style.YELLOW}⚠️  Could not set Windows ACLs: {e}{Style.RESET}")

        get_input("Press Enter to return", allow_empty=True)

    except Exception as e:
        print_error(f"Installation failed: {e}")
        get_input("Press Enter", allow_empty=True)

def get_username_suggestions():
    """Get list of potential usernames based on system info."""
    suggestions = []
    
    # 1. System Username
    try:
        sys_user = os.getlogin().lower()
        suggestions.append(InputPolicy.sanitize_username(sys_user))
    except:
        sys_user = "admin"
        
    # 2. Try to derive First Initial + Last Name (e.g. jdoe)
    print(f"\n{Style.BOLD}--- Identity Setup ---{Style.RESET}")
    full_name = get_input("Enter your Full Name (e.g. John Doe) [Optional]", "").strip()
    
    if full_name:
        parts = full_name.split()
        if len(parts) >= 2:
            first = parts[0].lower()
            last = parts[-1].lower()
            
            # Standard 1: fLast (jdoe)
            s1 = InputPolicy.sanitize_username(f"{first[0]}{last}")
            if s1 not in suggestions: suggestions.append(s1)
            
            # Standard 2: first.last (john.doe)
            s2 = InputPolicy.sanitize_username(f"{first}.{last}")
            if s2 not in suggestions: suggestions.append(s2)
            
            # Standard 3: lastf (doej)
            s3 = InputPolicy.sanitize_username(f"{last}{first[0]}")
            if s3 not in suggestions: suggestions.append(s3)

    return suggestions

def review_payload(payload_path):
    """Interactively review and prune the payload file."""
    if not os.path.exists(payload_path):
        return

    print(f"\n{Style.BOLD}🛡️  Security Review: {os.path.basename(payload_path)}{Style.RESET}")
    
    try:
        with open(payload_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        if not lines:
            print(f"   {Style.DIM}(Payload is empty){Style.RESET}")
            return

        # 1. Identify CURRENT keys (present in local directory)
        local_pub_keys = set()
        dir_path = os.path.dirname(payload_path)
        for f in os.listdir(dir_path):
            if f.endswith(".pub"):
                try:
                     with open(os.path.join(dir_path, f), 'r') as pf:
                         content = pf.read().strip().split()
                         if len(content) >= 2:
                             # Store the key body (part 1)
                             local_pub_keys.add(content[1])
                except: pass

        # Sort by Date (Newest First)
        # Key format: ... user@host-YYYY-MM-DD
        import re
        # 2. Sort Logic
        # Helper to get date
        import re
        def get_date_key(line):
            try:
                parts = line.split()
                if len(parts) > 2:
                    comment = parts[-1]
                    # Find YYYY-MM-DD
                    match = re.search(r'(\d{4}-\d{2}-\d{2})', comment)
                    if match:
                        return match.group(1)
            except: pass
            return None # Return None for undated keys to handle them specially
            
        # Split into Current vs Others (To pin Current to top)
        current_list = []
        dated_list = []
        undated_list = []
        
        for line in lines:
            parts = line.split()
            key_body = parts[1] if len(parts) > 1 else ""
            
            if key_body in local_pub_keys:
                current_list.append(line)
            else:
                date = get_date_key(line)
                if date:
                    dated_list.append(line)
                else:
                    undated_list.append(line)
        
        # Sort "Dated" by Date (Newest first)
        dated_list.sort(key=get_date_key, reverse=True)
        
        # Combine: Current -> Undated (might be new/manual) -> Rated History (Newest->Oldest)
        # This fixes the issue where new keys without dates (or failed parsing) went to the very bottom.
        lines = current_list + undated_list + dated_list

        print(f"   Found {len(lines)} authorized key(s).")
        print(f"   {Style.YELLOW}Review carefully. Remove keys that are no longer needed.{Style.RESET}")
        
        keep_indices = set(range(len(lines)))
        
        while True:
            print(f"\n   {Style.BOLD}Current Payload (Top = Active | Rest = History):{Style.RESET}")
            legacy_count = 0
            
            for i, line in enumerate(lines):
                parts = line.split()
                
                # Metadata
                key_body = parts[1] if len(parts) > 1 else ""
                comment = parts[-1] if len(parts) > 2 else "(no comment)"
                short_key = key_body[:15] + "..." if key_body else "..."
                
                # Detection
                is_current = key_body in local_pub_keys
                is_legacy = "@" not in comment and "202" not in comment # Heuristic for non-standard
                if is_legacy: legacy_count += 1
                
                # Formatting
                status = "✅ KEEP" if i in keep_indices else "❌ REMOVE"
                color = Style.GREEN if i in keep_indices else Style.RED
                
                tags = ""
                if is_current: tags += f"{Style.BOLD}{Style.CYAN}[CURRENT KEY] {Style.RESET}"
                if is_legacy:  tags += f"{Style.YELLOW}[LEGACY?] {Style.RESET}"
                
                # Highlight date if present
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', comment)
                if date_match and not is_current: # Don't double highlight current
                    d_str = date_match.group(1)
                    rel_tag = ""
                    try:
                        key_date = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                        today = datetime.date.today()
                        delta = (today - key_date).days
                        
                        if delta < 0: rel_tag = " (Future)"
                        elif delta == 0: rel_tag = " (Today)"
                        elif delta == 1: rel_tag = " (Yesterday)"
                        elif delta < 30: rel_tag = f" ({delta} days ago)"
                        elif delta < 365: rel_tag = f" ({delta//30} months ago)"
                        else: rel_tag = f" ({delta//365} years ago)"
                    except: pass
                    
                    tags += f"{Style.DIM}[{d_str}{rel_tag}]{Style.RESET} "
                
                print(f"   [{i+1}] {color}{status}{Style.RESET} : {tags}{comment} {Style.DIM}({short_key}){Style.RESET}")
            
            print(f"\n   Actions: [Number/Range] to toggle (e.g. 1-3, 5), [P]urge Legacy, [A]ccept, [C]lear All, [Q]uit")
            choice = get_input("Action", "A").upper()
            
            if choice == 'A':
                # ... (Save block unchanged, but I need to include it if I'm replacing the whole block or just match the context)
                # Actually I can just target the `else` block if I use the right context.
                pass # Placeholder for the 'A' block which I am NOT changing in this specific edit if I can avoid it.
                # Wait, I am replacing the whole loop body or just the input handling?
                # The prompt has `EndLine: 624`. Let's look at the context again. 
                # I'll replace the input prompt and the `else` block. 
                
            # ... (Putting the real code below) ...
            
            if choice == 'A':
                # Safety Check: Current Key Removal
                removed_current_indices = []
                for i, line in enumerate(lines):
                    parts = line.split()
                    key_body = parts[1] if len(parts) > 1 else ""
                    if key_body in local_pub_keys and i not in keep_indices:
                        removed_current_indices.append(i)
                
                if removed_current_indices:
                    print(f"\n{Style.RED}⚠️  WARNING: You are about to remove your CURRENT ACTIVE KEY from the payload!{Style.RESET}")
                    print(f"   This might lock you out or break future deployments.")
                    if get_input("Are you sure? (yes/no)", "no").lower() != 'yes':
                        # Auto-Rescue
                        for idx in removed_current_indices:
                            keep_indices.add(idx)
                        print(f"   {Style.GREEN}✅ Safety override: Current key(s) retained.{Style.RESET}")
                        print(f"   {Style.DIM}Returning to list to verify selections...{Style.RESET}")
                        get_input("Press Enter", allow_empty=True)
                        continue # Return to list view
                
                 # Save changes (preserving sorted order)
                new_lines = [lines[i] for i in range(len(lines)) if i in keep_indices]
                with open(payload_path, 'w') as f:
                    for line in new_lines:
                        f.write(line + "\n")
                
                removed_count = len(lines) - len(new_lines)
                if removed_count > 0:
                    print_success(f"Updated payload. Removed {removed_count} key(s).")
                    log_action(f"PAYLOAD PRUNED: Removed {removed_count} keys.")
                elif len(new_lines) == len(lines):
                     print("   Payload re-saved (sorted).")
                break
            
            elif choice == 'P':
                 # Purge Legacy
                 if legacy_count == 0:
                     print("   No legacy keys detected.")
                 else:
                     confirm = get_input(f"Remove {legacy_count} suspected legacy keys? (yes/no)", "yes")
                     if confirm.lower() == 'yes':
                         # Identify legacy indices
                         for i, line in enumerate(lines):
                             parts = line.split()
                             comment = parts[-1] if len(parts) > 2 else ""
                             is_legacy = "@" not in comment and "202" not in comment
                             if is_legacy and i in keep_indices:
                                 keep_indices.remove(i)
                         print(f"   Marked {legacy_count} keys for removal.")
            
            elif choice == 'C':
                confirm = get_input("Remove ALL keys from payload? (yes/no)", "no")
                if confirm.lower() == 'yes':
                    keep_indices = set()
            
            elif choice == 'Q':
                print("   Review cancelled. No changes made.")
                break
                
            else:
                # Range/List Parser
                try:
                    # Normalize: "1..5" -> "1-5", "1, 2" -> "1,2"
                    cleaned = choice.replace("..", "-").replace(" ", "")
                    chunks = cleaned.split(",")
                    
                    for chunk in chunks:
                        if "-" in chunk:
                            # Range: 1-5
                            start_s, end_s = chunk.split("-", 1)
                            start = int(start_s) - 1
                            end = int(end_s) - 1
                            # Handle reversed range or clamps
                            if start > end: start, end = end, start
                            
                            for idx in range(start, end + 1):
                                if 0 <= idx < len(lines):
                                    if idx in keep_indices: keep_indices.remove(idx)
                                    else: keep_indices.add(idx)
                        else:
                            # Single
                            idx = int(chunk) - 1
                            if 0 <= idx < len(lines):
                                if idx in keep_indices: keep_indices.remove(idx)
                                else: keep_indices.add(idx)
                except:
                    pass
                
    except Exception as e:
        print_error(f"Error reading payload: {e}")

def get_hardware_id():
    """Detects hardware model and year to generate a concise ID (e.g. mba2023, dellxps2024)."""
    system = platform.system().lower()
    hardware_id = "pc"
    
    try:
        if "darwin" in system:
             # macOS
            try:
                cmd_model = "system_profiler SPHardwareDataType | awk -F': ' '/Model Name/ {print $2}'"
                model_name = subprocess.check_output(cmd_model, shell=True).decode().strip()
                cmd_year = "system_profiler SPHardwareDataType | awk -F': ' '/Year/ {print $2}'"
                year = subprocess.check_output(cmd_year, shell=True).decode().strip()
                if not year: year = str(datetime.date.today().year)
                
                prefix = "mac"
                if "MacBook Air" in model_name: prefix = "mba"
                elif "MacBook Pro" in model_name: prefix = "mbp"
                elif "Mac mini" in model_name: prefix = "mini"
                elif "Mac Studio" in model_name: prefix = "studio"
                elif "iMac" in model_name: prefix = "imac"
                elif "Mac Pro" in model_name: prefix = "macpro"
                
                hardware_id = f"{prefix}{year}"
            except: pass

        elif "windows" in system:
            # Windows
             try:
                ps_script = """
                $cs = Get-CimInstance Win32_ComputerSystem; $bios = Get-CimInstance Win32_BIOS;
                $Vendor = $cs.Manufacturer.ToLower(); $Model = $cs.Model.ToLower(); $Year = $bios.ReleaseDate.Substring(0,4);
                $Prefix = "pc";
                if ($Vendor -match "dell") { 
                    if ($Model -match "xps") { $Prefix = "dellxps" } elseif ($Model -match "latitude") { $Prefix = "delllat" } else { $Prefix = "dellpc" }
                } elseif ($Vendor -match "lenovo") {
                    if ($Model -match "thinkpad") { $Prefix = "thinkpad" } else { $Prefix = "lenovopc" }
                } elseif ($Vendor -match "hp") {
                    if ($Model -match "elitebook") { $Prefix = "hpelite" } else { $Prefix = "hppc" }
                } elseif ($Vendor -match "microsoft") {
                    if ($Model -match "surface") { $Prefix = "surface" }
                }
                Write-Output "${Prefix}${Year}"
                """
                cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
                hardware_id = subprocess.check_output(cmd).decode().strip()
             except: pass
            
        elif "linux" in system:
             # Linux
             try:
                vendor = ""; model = ""; bios_date = ""
                with open("/sys/class/dmi/id/sys_vendor", "r") as f: vendor = f.read().strip().lower()
                with open("/sys/class/dmi/id/product_name", "r") as f: model = f.read().strip().lower()
                with open("/sys/class/dmi/id/bios_date", "r") as f: bios_date = f.read().strip()
                
                year = bios_date.split('/')[-1] if '/' in bios_date else str(datetime.date.today().year)
                # Cleanup year if it has full date
                if len(year) > 4: year = year[-4:] 

                prefix = "linuxpc"
                if "dell" in vendor:
                    if "xps" in model: prefix = "dellxps"
                    elif "latitude" in model: prefix = "delllat"
                    else: prefix = "dellpc"
                elif "lenovo" in vendor:
                    if "thinkpad" in model: prefix = "thinkpad"
                    else: prefix = "lenovopc"
                hardware_id = f"{prefix}{year}"
             except: 
                hardware_id = "linuxpc"

    except Exception:
        hardware_id = "pc"

    # Strict Sanitization via Policy
    return InputPolicy.sanitize_hostname(hardware_id)

# --- Refactoring Classes ---

class WizardContext:
    """Holds the session state for User, Device, and Paths."""
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.keys_dir = os.path.join(root_dir, "AuthorizedKeys")
        self.history_dir = os.path.join(root_dir, "History")
        self.payload_path = os.path.join(self.keys_dir, "AuthorizedKeysPayload.txt")
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Identity
        self.user = "admin"
        self.device = "pc"
        self.final_user = "admin" # The sanitized version used for filenames
        self.final_device = "pc"  # The sanitized version used for filenames

    def update_identity(self, user, device):
        self.user = user
        self.device = device
        self.final_user = InputPolicy.sanitize_username(user)
        self.final_device = InputPolicy.sanitize_hostname(device)
        
    def get_key_name(self):
        return f"id_ed25519_{self.final_device}_{self.final_user}"

class ZipEngine:
    """
    Handles robust, high-performance Zip creation in memory (RAM Drive).
    Prevents AV scanning of intermediate files and ensures atomic writes.
    """
    @staticmethod
    def build_and_save(files_map, output_path, console_prefix="Building"):
        """
        files_map: dict {source_abspath: dest_relpath_in_zip}
        output_path: absolute path to save the .zip
        """
        import zipfile
        import io
        import time
        
        t_start = time.time()
        total_ops = len(files_map)
        current_op = 0
        
        print(f"\n   ⏳ {console_prefix} ({total_ops} files)...")
        print_progress_bar(0, total_ops, prefix='Progress:', suffix='Starting...', length=30)
        
        # 1. Build in RAM
        mem_zip = io.BytesIO()
        try:
            # ZIP_STORED (No Compression) for speed and lower AV profile
            with zipfile.ZipFile(mem_zip, 'w', zipfile.ZIP_STORED) as zipf:
                for src, arcname in files_map.items():
                    if os.path.exists(src):
                        try:
                            # Read into memory first
                            with open(src, 'rb') as f: data = f.read()
                            zipf.writestr(arcname, data)
                        except Exception as e:
                            print(f"\n{Style.RED}❌ Error reading {os.path.basename(src)}: {e}{Style.RESET}")
                    elif src.startswith("MEM:"):
                        # Special case for in-memory content: "MEM:filename.txt" -> content string
                        # Handle this if passed, but cleaner to assume files_map contains paths
                        pass 
                    else:
                        print(f"\n{Style.YELLOW}⚠️  Missing: {arcname}{Style.RESET}")
                    
                    current_op += 1
                    print_progress_bar(current_op, total_ops, prefix='Zipping:', suffix=f'{current_op}/{total_ops}', length=30)

        except Exception as e:
            print_error(f"Failed to build zip in memory: {e}")
            return False

        # 2. Atomic Write
        display_size = len(mem_zip.getvalue()) / 1024
        print(f"\n   💾 Writing {display_size:.1f}KB to disk...", end="")
        
        if os.path.exists(output_path):
            try: os.remove(output_path)
            except: pass
            
        try:
            with open(output_path, "wb") as f:
                f.write(mem_zip.getvalue())
            print(" Done.")
            
            # 3. Refresh OS View
            try: os.utime(os.path.dirname(output_path), None)
            except: pass
            
            print_success(f"Saved: {output_path} ({time.time() - t_start:.2f}s)")
            return True
        except Exception as e:
            print_error(f"Failed to save zip file to disk: {e}")
            return False
            
    @staticmethod
    def cleanup_old_archives(directory, prefix="Deploy-Package-"):
        """Removes old zip files matching the prefix."""
        try:
            count = 0
            for f in os.listdir(directory):
                if f.startswith(prefix) and f.endswith(".zip"):
                    try: 
                        os.remove(os.path.join(directory, f))
                        count += 1
                    except: pass
            if count > 0:
                print(f"   🧹 Cleaned up {count} old archive(s).")
        except: pass


def create_deployment_package(ctx, payload_path):
    """Creates a zipped deployment package using ZipEngine."""
    
    print(f"\n{Style.BOLD}Deployment Package:{Style.RESET}")
    if get_input(f"Create a 'Deploy-Package.zip' now? (yes/no)", "yes").lower() != 'yes':
        return

    # Security Review
    if os.path.exists(payload_path):
        if get_input("Quick Review of key list? (yes/no)", "no").lower() == 'yes':
            review_payload(payload_path)

    # Clean old archives
    ZipEngine.cleanup_old_archives(ctx.keys_dir)

    # Prepare File Map
    files_map = {}
    
    # 1. Scripts
    # Define generic mapping from Platforms/X/Script to Platforms/X/Script
    # (Assuming script_dir is set correctly in ctx or we derive it)
    platforms = {
        "Windows": ["Deploy-SSH-Windows.ps1", "Uninstall-SSH-Windows.ps1", "Toggle-SSH-Windows.ps1"],
        "Linux":   ["Deploy-SSH-Linux.sh", "Uninstall-SSH-Linux.sh", "Toggle-SSH-Linux.sh"],
        "Mac":     ["Deploy-SSH-Mac.sh", "Uninstall-SSH-Mac.sh", "Toggle-SSH-Mac.sh"],
    }
    
    for os_name, scripts in platforms.items():
        for script in scripts:
            src = os.path.join(ctx.script_dir, "Platforms", os_name, script)
            arc = os.path.join("Platforms", os_name, script)
            files_map[src] = arc

    # 2. Payload
    if os.path.exists(payload_path):
        files_map[payload_path] = os.path.basename(payload_path)
    else:
        print(f"{Style.YELLOW}⚠️  Warning: Payload not found. Package will be empty of keys.{Style.RESET}")

    # 3. README (Generated in-memory, needs to be written to temp or handled by ZipEngine)
    # Since ZipEngine currently takes paths, we'll write README to a temp file or handle it.
    # To keep ZipEngine simple, let's write README to the output_dir temporarily.
    
    readme_content = f"""
WINTOOLS: SSH Deployment Package
================================
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Target Device: {ctx.final_device} (User: {ctx.final_user})

INSTRUCTIONS:
-------------
[WINDOWS] PowerShell as Admin: 
   powershell -ExecutionPolicy Bypass -File .\\Platforms\\Windows\\Deploy-SSH-Windows.ps1 -KeysFile .\\AuthorizedKeysPayload.txt -DisablePasswordAuth

[LINUX] sudo bash ./Platforms/Linux/Deploy-SSH-Linux.sh
[MACOS] sudo bash ./Platforms/Mac/Deploy-SSH-Mac.sh
"""
    readme_path = os.path.join(ctx.keys_dir, "README_INSTALL.txt")
    with open(readme_path, "w") as f: f.write(readme_content.strip())
    files_map[readme_path] = "README_INSTALL.txt"

    # Execute
    zip_name = f"Deploy-Package-{ctx.final_device}.zip"
    zip_path = os.path.join(ctx.keys_dir, zip_name)
    
    success = ZipEngine.build_and_save(files_map, zip_path, console_prefix="Building Package")
    
    # Cleanup README
    try: os.remove(readme_path)
    except: pass
    
    if success:
        print(f"   {Style.DIM}Contains: Scripts, Payload, and Instructions.{Style.RESET}")
    
    get_input("\nPress Enter to return...", allow_empty=True)
    return zip_path


def create_portable_wizard(ctx):
    """Creates a clean zip of the wizard and scripts for portability using ZipEngine."""
    
    print(f"\n{Style.BOLD}🎒 Create Portable Wizard:{Style.RESET}")
    print("This will create a 'WINTOOLS_SSH_Wizard_Portable.zip' containing only the scripts.")
    print("It will NOT include your secrets, history, or logs.")
    
    if get_input("Proceed? (yes/no)", "yes").lower() != 'yes': return

    zip_name = "WINTOOLS_SSH_Wizard_Portable.zip"
    zip_path = os.path.join(ctx.keys_dir, zip_name)
    
    # Files to include (Source Path -> Dest Path in Zip)
    include_files = {
        "SSH_Key_Wizard.py": "SSH_Key_Wizard.py",
        "README.md": "README.md",
        "LICENSE": "LICENSE",
        os.path.join("Platforms", "Windows", "Deploy-SSH-Windows.ps1"): os.path.join("Platforms", "Windows", "Deploy-SSH-Windows.ps1"),
        os.path.join("Platforms", "Windows", "Uninstall-SSH-Windows.ps1"): os.path.join("Platforms", "Windows", "Uninstall-SSH-Windows.ps1"),
        os.path.join("Platforms", "Windows", "Toggle-SSH-Windows.ps1"): os.path.join("Platforms", "Windows", "Toggle-SSH-Windows.ps1"),
        
        os.path.join("Platforms", "Linux", "Deploy-SSH-Linux.sh"): os.path.join("Platforms", "Linux", "Deploy-SSH-Linux.sh"),
        os.path.join("Platforms", "Linux", "Uninstall-SSH-Linux.sh"): os.path.join("Platforms", "Linux", "Uninstall-SSH-Linux.sh"),
        os.path.join("Platforms", "Linux", "Toggle-SSH-Linux.sh"): os.path.join("Platforms", "Linux", "Toggle-SSH-Linux.sh"),
        
        os.path.join("Platforms", "Mac", "Deploy-SSH-Mac.sh"): os.path.join("Platforms", "Mac", "Deploy-SSH-Mac.sh"),
        os.path.join("Platforms", "Mac", "Uninstall-SSH-Mac.sh"): os.path.join("Platforms", "Mac", "Uninstall-SSH-Mac.sh"),
        os.path.join("Platforms", "Mac", "Toggle-SSH-Mac.sh"): os.path.join("Platforms", "Mac", "Toggle-SSH-Mac.sh"),
    }
    
    files_map = {}
    for src_rel, dest_rel in include_files.items():
        src = os.path.join(ctx.script_dir, src_rel)
        files_map[src] = dest_rel
        
    ZipEngine.build_and_save(files_map, zip_path, console_prefix="Building Portable Wizard")
    get_input("\nPress Enter to return...", allow_empty=True)

def merge_external_payload(local_payload_path):
    """Merges an external AuthorizedKeysPayload.txt into the local one."""
    print(f"\n{Style.BOLD}🔗 Merge External Payload:{Style.RESET}")
    
    external_path = get_input("Path to external 'AuthorizedKeysPayload.txt' (or folder containing it)").strip()
    external_path = external_path.replace('"', '').replace("'", "")
    
    # Auto-resolve if folder provided
    if os.path.isdir(external_path):
        external_path = os.path.join(external_path, "AuthorizedKeysPayload.txt")
        
    if not os.path.exists(external_path):
        print_error(f"File not found: {external_path}")
        get_input("Press Enter to return to menu", allow_empty=True)
        return

    try:
        # Read Local
        local_content = ""
        if os.path.exists(local_payload_path):
            with open(local_payload_path, 'r') as f: local_content = f.read()
        
        # Read External
        with open(external_path, 'r') as f: external_content = f.read()
        
        # Parse and Merge (Simple Line-based deduplication for now)
        # A more robust way would be to parse key string, but line-based is usually sufficient for ssh-keys
        local_lines = set(line.strip() for line in local_content.splitlines() if line.strip())
        external_lines = [line.strip() for line in external_content.splitlines() if line.strip()]
        
        added_count = 0
        with open(local_payload_path, 'a') as f:
            if local_content and not local_content.endswith('\n'):
                f.write("\n")
            
            for line in external_lines:
                if line not in local_lines:
                    f.write(line + "\n")
                    local_lines.add(line) # Add to set to prevent dupes within the same import
                    added_count += 1
        
        print_success(f"Merged! Added {added_count} new line(s) to '{os.path.basename(local_payload_path)}'.")
        log_action(f"MERGED PAYLOAD: Added {added_count} lines from {external_path}")
        
    except Exception as e:
        print_error(f"Merge failed: {e}")
    
    get_input("Press Enter to return to menu", allow_empty=True)


def view_history(history_dir, active_dir):
    """Displays history and allows restoring a previous state."""
    while True:
        clear_screen()
        print(f"\n{Style.BOLD}📜 History Archive:{Style.RESET}")
        
        if not os.path.exists(history_dir) or not os.listdir(history_dir):
            print(f"   {Style.DIM}(No history found){Style.RESET}")
            get_input("Press Enter to return to menu", allow_empty=True)
            return

        archives = sorted([d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))], reverse=True)
        
        if not archives:
             print(f"   {Style.DIM}(No valid archive folders found){Style.RESET}")
             get_input("Press Enter to return to menu", allow_empty=True)
             return

        for i, name in enumerate(archives):
            # Calculate size/count? details?
            item_path = os.path.join(history_dir, name)
            item_count = len(os.listdir(item_path))
            print(f"   [{Style.CYAN}{i+1}{Style.RESET}] {name} {Style.DIM}({item_count} files){Style.RESET}")
        
        print(f"   [{Style.CYAN}0{Style.RESET}] Back to Main Menu")
        
        choice = get_input("\nSelect Archive to Inspect", "0")
        
        if choice == '0':
            return
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(archives):
                selected_archive = archives[idx]
                archive_path = os.path.join(history_dir, selected_archive)
                
                # Inspect
                print(f"\n{Style.BOLD}📂 Contents of '{selected_archive}':{Style.RESET}")
                files = os.listdir(archive_path)
                for f in files:
                    print(f"   - {f}")
                
                print(f"\n{Style.BOLD}{Style.YELLOW}⚠️  Restore this archive?{Style.RESET}")
                print(f"   This will {Style.RED}OVERWRITE{Style.RESET} your current 'AuthorizedKeys' folder.")
                print(f"   (Don't worry, your current state will be auto-archived first.)")
                
                restore = get_input("Restore now? (yes/no)", "no")
                if restore.lower() == 'yes':
                    # 1. Auto-Archive Current
                    print(f"\n{Style.DIM}Backing up current state...{Style.RESET}")
                    # Only archive if there is something to archive
                    if os.path.exists(active_dir) and os.listdir(active_dir):
                         archive_current_state(active_dir)
                    else:
                         # Ensure we have a clear directory even if it was empty/missing
                         if os.path.exists(active_dir): shutil.rmtree(active_dir)
                         os.makedirs(active_dir, exist_ok=True)

                    # 2. Restore
                    try:
                        # Copy all files from archive to active_dir
                        for item in os.listdir(archive_path):
                            s = os.path.join(archive_path, item)
                            d = os.path.join(active_dir, item)
                            if os.path.isdir(s):
                                shutil.copytree(s, d, dirs_exist_ok=True)
                            else:
                                shutil.copy2(s, d)
                        
                        print_success(f"Restored '{selected_archive}' to active directory.")
                        log_action(f"RESTORED: State reset to '{selected_archive}'")
                        get_input("Press Enter to continue", allow_empty=True)
                        return # Return to main menu to show new status
                        
                    except Exception as e:
                        print_error(f"Restore failed: {e}")
                        get_input("Press Enter", allow_empty=True)

            else:
                print_error("Invalid selection.")
                get_input("Press Enter", allow_empty=True)
        except ValueError:
            print_error("Invalid input.")
            get_input("Press Enter", allow_empty=True)



# --- Handler Functions ---

def handle_generate_key(ctx):
    # 1. Username
    suggestions = get_username_suggestions()
    print(f"\n{Style.BOLD}Select a standardized username:{Style.RESET}")
    for i, name in enumerate(suggestions):
        print(f"  [{Style.CYAN}{i+1}{Style.RESET}] {name}")
    print(f"  [{Style.CYAN}{len(suggestions)+1}{Style.RESET}] Custom...")
    
    user_choice = get_input("Select Option", "1")
    user = ""
    try:
        idx = int(user_choice) - 1
        if 0 <= idx < len(suggestions):
             user = suggestions[idx]
        else:
             user = get_input("Enter Custom Username (a-z0-9._- only)")
    except:
         user = get_input("Enter Custom Username (a-z0-9._- only)")
    
    # Update Context
    ctx.update_identity(user, ctx.device)
    print_success(f"Selected Username: {ctx.final_user}")

    # 2. Device Name
    dev_base = InputPolicy.sanitize_hostname(platform.node().split('.')[0])
    if platform.system() == "Darwin":
        try:
             cname = subprocess.check_output("scutil --get ComputerName", shell=True).decode().strip()
             if cname: dev_base = InputPolicy.sanitize_hostname(cname)
        except: pass

    # Suggestion Logic
    suggestions = []
    # 1. Current Context Device
    suggestions.append(ctx.final_device)
    # 2. Hardware ID
    # (Hardware ID detection logic is in get_hardware_id(), we can re-call or pass it. 
    # Ideally ctx should have it initialized. For now, let's re-detect or use "pc" as fallback)
    hw_id = get_hardware_id()
    suggestions.append(hw_id)
    # 3. Hostname
    if dev_base != hw_id: suggestions.append(dev_base)
    # 4. Suffixes
    suggestions.append(f"{hw_id}-wfh")
    suggestions.append(f"{hw_id}-cmp")

    # Deduplicate
    final_suggestions = sorted(list(set(suggestions)))
    
    print(f"\n{Style.BOLD}Select Device Context:{Style.RESET}")
    for i, name in enumerate(final_suggestions):
        print(f"  [{Style.CYAN}{i+1}{Style.RESET}] {name}")
    print(f"  [{Style.CYAN}{len(final_suggestions)+1}{Style.RESET}] Custom...")

    dev_choice = get_input("Select Option", "1")
    device = ""
    try:
        idx = int(dev_choice) - 1
        if 0 <= idx < len(final_suggestions):
            device = final_suggestions[idx]
        else:
             device = get_input("Enter Device Name")
    except:
         device = get_input("Enter Device Name")

    # Update Context Again
    ctx.update_identity(ctx.user, device)
    print_success(f"Selected Device: {ctx.final_device}")

    # 3. Generate
    generate_key(ctx.final_user, ctx.final_device, ctx.keys_dir)
    # Note: generate_key handles the install_local_key prompt internally if interactive=True

def handle_import_key(ctx):
    print(f"\n{Style.BOLD}--- Import Workflow ---{Style.RESET}")
    existing_priv = get_input("Path to your existing PRIVATE key").strip()
    existing_priv = existing_priv.replace('"', '').replace("'", "")
    
    if os.path.exists(existing_priv):
        # We need context to name it correctly
        # For simplicity, reuse the generate handler logic to get user/device or just ask
        user = get_input("Enter Key Username (e.g. admin)", "admin")
        device = get_input("Enter Key DeviceName (e.g. macbook)", "pc")
        ctx.update_identity(user, device)
        
        key_name = ctx.get_key_name()
        new_priv_path = os.path.join(ctx.keys_dir, key_name)
        new_pub_path = f"{new_priv_path}.pub"
        
        try:
            cmd = ["ssh-keygen", "-y", "-f", existing_priv]
            pub_content = subprocess.check_output(cmd).decode().strip()
            comment = f"{ctx.final_user}@{ctx.final_device}-{datetime.date.today()}"
            pub_content_with_comment = f"{pub_content} {comment}"
            
            with open(new_pub_path, "w") as f:
                f.write(pub_content_with_comment + "\n")
            shutil.copy2(existing_priv, new_priv_path)
            if os.name != 'nt': os.chmod(new_priv_path, 0o600)
            
            print_success(f"Imported: {key_name}")
            log_action(f"IMPORTED: {key_name}")
            
            # Offer to add to payload
            add_key_to_payload_interactive(ctx.payload_path, new_priv_path, new_pub_path, ctx.final_user, ctx.final_device)
            
        except Exception as e:
            print_error(f"Import failed: {e}")
    else:
        print_error("File not found.")


def main():
    # 1. Initialization
    current_cwd = os.getcwd()
    root_dir = current_cwd
    
    # If inside 'AuthorizedKeys', move up
    if os.path.basename(current_cwd) == "AuthorizedKeys":
        root_dir = os.path.dirname(current_cwd)
    
    ctx = WizardContext(root_dir)
    os.makedirs(ctx.keys_dir, exist_ok=True)
    
    # Check if this is the first run / setup defaults
    hw_id = get_hardware_id()
    ctx.update_identity("admin", hw_id)

    while True:
        clear_screen()
        print(f"{Style.BLUE}========================================{Style.RESET}")
        print(f"{Style.BOLD}      WINTOOLS: SSH Key Wizard 🧙‍♂️      {Style.RESET}")
        print(f"{Style.BLUE}========================================{Style.RESET}")
        print(f"{Style.DIM}Running on: {platform.system()} ({platform.release()}){Style.RESET}")
        
        # Status Line
        keys_found = [f for f in os.listdir(ctx.keys_dir) if f.startswith("id_ed25519") and not f.endswith(".pub")]
        payload_exists = os.path.exists(ctx.payload_path)
        
        # Intelligence: Try to guess context from existing keys
        if keys_found and ctx.device == "pc":
             try:
                parts = keys_found[0].split('_')
                if len(parts) >= 4:
                    guessed_dev = parts[2]
                    guessed_user = "_".join(parts[3:]) 
                    ctx.update_identity(guessed_user, guessed_dev)
             except: pass

        status_color = Style.GREEN if keys_found else Style.DIM
        print(f"Status: {status_color}{len(keys_found)} Key(s) Found{Style.RESET} | Payload: {'✅' if payload_exists else '❌'}")
        print(f"{Style.BLUE}----------------------------------------{Style.RESET}")
        
        print(f"  [{Style.CYAN}1{Style.RESET}] 🔑  Generate NEW Key Pair")
        print(f"  [{Style.CYAN}2{Style.RESET}] 📥  Import EXISTING Private Key")
        print(f"  [{Style.CYAN}3{Style.RESET}] 📦  Create Deployment Package (Zip)")
        print(f"  [{Style.CYAN}4{Style.RESET}] 📜  View Archive History")
        print(f"  [{Style.CYAN}5{Style.RESET}] ♻️   RESET and Archive Everything")
        print(f"  [{Style.CYAN}6{Style.RESET}] 🚪  Exit")
        print(f"{Style.BLUE}----------------------------------------{Style.RESET}")
        print(f"  [{Style.CYAN}0{Style.RESET}] 🛡️  Review/Edit Authorized Keys Payload")
        print(f"  [{Style.CYAN}7{Style.RESET}] 🎒  Create Portable Wizard (Clean Zip)")
        print(f"  [{Style.CYAN}8{Style.RESET}] 🔗  Merge Another Payload File")
        print(f"  [{Style.CYAN}9{Style.RESET}] 🔧  Install/Repair Local Key")
        
        try:
            choice = get_input("\nSelect Option")

            if choice == "6":
                print(f"\n{Style.DIM}Goodbye 👋{Style.RESET}")
                sys.exit(0)

            elif choice == "0":
                review_payload(ctx.payload_path)
            
            elif choice == "1":
                handle_generate_key(ctx)
                # After gen, if key exists, offer to add to payload? 
                # generate_key returns path, let's capture it?
                # Actually generate_key calls install_local_key. 
                # We need to bridge the gap to 'add_key_to_payload'.
                # Let's fix generate_key to return paths and handle payload adding here?
                # Or just let handle_generate_key do it.
                # Refactoring generate_key is risky without changing its signature.
                # Let's check generate_key... it returns (priv, pub).
                # Good. We need to update handle_generate_key to capture that.
                pass 

            elif choice == "2":
                handle_import_key(ctx)

            elif choice == "3":
                # Create Deployment Package
                print(f"\n{Style.BOLD}--- Package Creation ---{Style.RESET}")
                print(f"Ctx: User={ctx.final_user}, Device={ctx.final_device}")
                if get_input("Use this identity (for filenames/docs)? (yes/no)", "yes").lower() != 'yes':
                     u = get_input("Enter User (e.g. spencer, admin)")
                     d = get_input("Enter Device Name (e.g. macbook-pro)")
                     ctx.update_identity(u, d)

                create_deployment_package(ctx, ctx.payload_path)

            elif choice == "4":
                view_history(ctx.history_dir, ctx.keys_dir)

            elif choice == "5":
                archive_current_state(ctx.keys_dir)
                get_input("Press Enter to continue", allow_empty=True)

            elif choice == "7":
                create_portable_wizard(ctx)

            elif choice == "8":
                merge_external_payload(ctx.payload_path)

            elif choice == "9":
                install_key_menu(ctx.keys_dir)
            
            else:
                 print_error("Invalid Option")

        except WizardExit:
             continue
        except KeyboardInterrupt:
             print("\nGoodbye")
             sys.exit(0)
        except Exception as e:
             print_error(f"Unexpected Error: {e}")
             get_input("Press Enter to recover...", allow_empty=True)

if __name__ == "__main__":
    main()
