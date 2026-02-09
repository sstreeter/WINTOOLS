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

def get_input(prompt, default=None):
    if default:
        # Style prompt?
        user_input = input(f"{Style.BOLD}{prompt}{Style.RESET} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            # Check if default exists to show brackets
            if default:
                 prompt_str = f"{Style.BOLD}{prompt}{Style.RESET} [{default}]"
            else:
                 prompt_str = f"{Style.BOLD}{prompt}{Style.RESET}"
            
            user_input = input(f"{prompt_str}: ").strip()
            if user_input:
                return user_input
            elif default:
                return default

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
        log_action(f"GENERATED NEW KEY: {key_name} (User: {user}, Device: {target_platform}) | Path: {key_path}")
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


    # ... (existing code) ...

def create_deployment_package(output_dir, payload_path, final_user, device_name):
    """Creates a zipped deployment package with scripts and instructions."""
    import zipfile
    
    print(f"\n{Style.BOLD}Deployment Package:{Style.RESET}")
    create_pkg = get_input(f"Create a 'Deploy-Package.zip' for manual transfer? (yes/no)", "yes")
    
    if create_pkg.lower() not in ['yes', 'y']:
        return

    # 1. Prepare Staging Area
    staging_dir = os.path.join(output_dir, "Deploy_Package_Staging")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Copy Scripts
    files_to_copy = {
        "Deploy-OpenSSH.ps1": "Deploy-OpenSSH.ps1",
        "Uninstall-OpenSSH.ps1": "Uninstall-OpenSSH.ps1",
    }
    
    payload_name = os.path.basename(payload_path)
    
    # Copy Payload (if it exists)
    if os.path.exists(payload_path):
        shutil.copy2(payload_path, os.path.join(staging_dir, payload_name))
    else:
        print(f"{Style.YELLOW}⚠️  Warning: Payload file '{payload_name}' not found. Skipping.{Style.RESET}")

    # Copy Scripts
    for filename, dest_name in files_to_copy.items():
        src = os.path.join(script_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(staging_dir, dest_name))
        else:
            print(f"{Style.RED}❌ Error: Script '{filename}' not found in '{script_dir}'.{Style.RESET}")

    # 3. Create README.txt
    readme_content = f"""
WINTOOLS: SSH Deployment Package
================================
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Target Device: {device_name} (User: {final_user})

INSTRUCTIONS:
-------------
1. Copy this entire folder (or unzip it) to the target Windows machine.
2. Open PowerShell as Administrator.
3. Run the following command to install OpenSSH and configure the keys:

   powershell -ExecutionPolicy Bypass -File .\\Deploy-OpenSSH.ps1 -KeysFile .\\{payload_name} -DisablePasswordAuth $true

4. To test, try SSHing into this machine from your admin station:
   ssh {final_user}@{device_name}

UNINSTALL:
----------
To remove OpenSSH and all configurations, run:
   powershell -ExecutionPolicy Bypass -File .\\Uninstall-OpenSSH.ps1
"""
    with open(os.path.join(staging_dir, "README_INSTALL.txt"), "w") as f:
        f.write(readme_content.strip())

    # 4. Zip It
    zip_name = f"Deploy-Package-{device_name}.zip"
    zip_path = os.path.join(output_dir, zip_name)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(staging_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, staging_dir)
                    zipf.write(file_path, arcname)
        
        print_success(f"Package Created: {zip_path}")
        print(f"   {Style.DIM}Contains: Scripts, Payload, and Instructions.{Style.RESET}")
        
    except Exception as e:
        print_error(f"Failed to create zip package: {e}")
    finally:
        # Cleanup Staging
        shutil.rmtree(staging_dir)

    return zip_path


def create_portable_wizard(output_dir):
    """Creates a clean zip of the wizard and scripts for portability."""
    import zipfile
    
    print(f"\n{Style.BOLD}🎒 Create Portable Wizard:{Style.RESET}")
    print("This will create a 'WINTOOLS_SSH_Wizard_Portable.zip' containing only the scripts.")
    print("It will NOT include your secrets, history, or logs.")
    
    confirm = get_input("Proceed? (yes/no)", "yes")
    if confirm.lower() != 'yes': return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    zip_name = "WINTOOLS_SSH_Wizard_Portable.zip"
    zip_path = os.path.join(output_dir, zip_name)
    
    # Allowlist of files to include
    include_files = [
        "SSH_Key_Wizard.py",
        "Deploy-OpenSSH.ps1",
        "Uninstall-OpenSSH.ps1",
        "Toggle-SSH.ps1",
        "README.md",
        "LICENSE"
    ]
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in include_files:
                src = os.path.join(script_dir, filename)
                if os.path.exists(src):
                    zipf.write(src, filename)
                else:
                    print(f"{Style.YELLOW}⚠️  Skipping missing file: {filename}{Style.RESET}")
        
        print_success(f"Portable Wizard Created: {zip_path}")
        get_input("Press Enter to return to menu")
    except Exception as e:
        print_error(f"Failed to create portable zip: {e}")
        get_input("Press Enter to return to menu")

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
        get_input("Press Enter to return to menu")
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
    
    get_input("Press Enter to return to menu")


def view_history(history_dir):
    """Displays the contents of the History directory."""
    print(f"\n{Style.BOLD}📜 History Archive:{Style.RESET}")
    if not os.path.exists(history_dir) or not os.listdir(history_dir):
        print(f"   {Style.DIM}(No history found){Style.RESET}")
        get_input("Press Enter to return to menu")
        return

    archives = sorted(os.listdir(history_dir), reverse=True)
    for i, name in enumerate(archives):
        print(f"   {i+1}. {name}")
    
    get_input("Press Enter to return to menu")

def main():
    # 1. Initialization
    default_dir = os.path.join(os.getcwd(), "AuthorizedKeys")
    history_dir = os.path.join(os.getcwd(), "History")
    os.makedirs(default_dir, exist_ok=True)
    
    # Pre-calculate Identity once (or could be re-calc'd if needed)
    raw_hostname = platform.node().split('.')[0]
    hostname = InputPolicy.sanitize_hostname(raw_hostname)
    hardware_id = get_hardware_id()
    
    # Default Identity placeholders
    current_user = "admin" 
    current_device = hardware_id

    while True:
        clear_screen()
        print(f"{Style.BLUE}========================================{Style.RESET}")
        print(f"{Style.BOLD}      WINTOOLS: SSH Key Wizard 🧙‍♂️      {Style.RESET}")
        print(f"{Style.BLUE}========================================{Style.RESET}")
        print(f"{Style.DIM}Running on: {platform.system()} ({platform.release()}){Style.RESET}")
        
        # Status Line
        keys_found = [f for f in os.listdir(default_dir) if f.startswith("id_ed25519") and not f.endswith(".pub")]
        payload_exists = os.path.exists(os.path.join(default_dir, "AuthorizedKeysPayload.txt"))
        
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
        print(f"  [{Style.CYAN}7{Style.RESET}] 🎒  Create Portable Wizard (Clean Zip)")
        print(f"  [{Style.CYAN}8{Style.RESET}] 🔗  Merge Another Payload File")
        
        choice = get_input("\nSelect Option", "1")

        if choice == "6":
            print(f"\n{Style.DIM}Goodbye 👋{Style.RESET}")
            sys.exit(0)

        elif choice == "5":
            archive_current_state(default_dir)
            get_input("Press Enter to continue")
            continue
            
        elif choice == "7":
            create_portable_wizard(default_dir)
            continue
            
        elif choice == "8":
            payload_path = os.path.join(default_dir, "AuthorizedKeysPayload.txt")
            merge_external_payload(payload_path)
            continue

        elif choice == "4":
            view_history(history_dir)
            continue
            
        elif choice == "3":
            # Create Deployment Package
            payload_path = os.path.join(default_dir, "AuthorizedKeysPayload.txt")
            
            # We need user/device context for the zip name
            if keys_found and current_device == hardware_id: # Only auto-detect if user hasn't manually set it this session? No, simpler to just re-parse or ask.
                 try:
                    parts = keys_found[0].split('_')
                    if len(parts) >= 4:
                        current_device = parts[2]
                        current_user = "_".join(parts[3:]) 
                 except: pass
            
            print(f"\n{Style.BOLD}--- Package Creation ---{Style.RESET}")
            print(f"Ctx: User={current_user}, Device={current_device}")
            if get_input("Use this identity for package name? (yes/no)", "yes").lower() != 'yes':
                 current_user = get_input("Enter Username")
                 current_device = get_input("Enter Device Name")

            create_deployment_package(default_dir, payload_path, current_user, current_device)
            get_input("Press Enter to return to menu")
            continue

        elif choice in ["1", "2"]:
            # --- Identity Setup (Shared) ---
            suggestions = get_username_suggestions()
    
            print(f"\n{Style.BOLD}Select a standardized username:{Style.RESET}")
            for i, name in enumerate(suggestions):
                print(f"  [{Style.CYAN}{i+1}{Style.RESET}] {name}")
            print(f"  [{Style.CYAN}{len(suggestions)+1}{Style.RESET}] Custom...")
            
            user_choice = get_input("Select Option", "1")
            
            final_user = ""
            try:
                idx = int(user_choice) - 1
                if 0 <= idx < len(suggestions):
                    final_user = suggestions[idx]
                else:
                    final_user = get_input("Enter Custom Username (a-z0-9._- only)")
            except:
                 final_user = get_input("Enter Custom Username (a-z0-9._- only)")
                 
            final_user = InputPolicy.sanitize_username(final_user)
            if len(final_user) < 2:
                final_user = "admin"
            print_success(f"Selected Username: {final_user}")
            # Update loop state
            current_user = final_user

            # --- Device Setup ---
            def format_dev_name(base, tag=None):
                if not tag: return InputPolicy.sanitize_hostname(base)
                max_base = InputPolicy.MAX_HOSTNAME_LEN - (len(tag) + 1)
                clean_base = InputPolicy.sanitize_hostname(base)[:max_base].strip('-')
                return InputPolicy.sanitize_hostname(f"{clean_base}-{tag}")

            dev_suggestions = [
                format_dev_name(hardware_id),        
                format_dev_name(hardware_id, "camp"),
                format_dev_name(hardware_id, "woc"),   # WORK ON CAMPUS
                format_dev_name(hardware_id, "wfh"), 
                format_dev_name(hostname, "camp"),   
                format_dev_name(hostname, "woc"),      # WORK ON CAMPUS (Hostname)
                format_dev_name(hostname, "wfh"),    
                format_dev_name(hostname)            
            ]
            
            print(f"\n{Style.BOLD}Select Device Context:{Style.RESET}")
            seen = set()
            final_suggestions = []
            for s in dev_suggestions:
                if s not in seen:
                    final_suggestions.append(s)
                    seen.add(s)

            for i, name in enumerate(final_suggestions):
                print(f"  [{Style.CYAN}{i+1}{Style.RESET}] {name}")
            print(f"  [{Style.CYAN}{len(final_suggestions)+1}{Style.RESET}] Custom...")
            
            dev_choice = get_input("Select Option", "1")
            
            device_name = ""
            try:
                idx = int(dev_choice) - 1
                if 0 <= idx < len(final_suggestions):
                    device_name = final_suggestions[idx]
                else:
                     device_name = get_input("Enter Device Name")
            except:
                 device_name = get_input("Enter Device Name")
            
            device_name = InputPolicy.sanitize_hostname(device_name)
            print_success(f"Selected Device: {device_name}")
            # Update loop state
            current_device = device_name

            # --- Action ---
            priv_path = None
            pub_path = None
            
            if choice == "2":
                # IMPORT
                print(f"\n{Style.BOLD}--- Import Workflow ---{Style.RESET}")
                existing_priv = get_input("Path to your existing PRIVATE key").strip()
                existing_priv = existing_priv.replace('"', '').replace("'", "")
                
                if os.path.exists(existing_priv):
                    key_name = f"id_ed25519_{device_name}_{final_user}"
                    new_priv_path = os.path.join(default_dir, key_name)
                    new_pub_path = f"{new_priv_path}.pub"
                    
                    try:
                        cmd = ["ssh-keygen", "-y", "-f", existing_priv]
                        pub_content = subprocess.check_output(cmd).decode().strip()
                        comment = f"{final_user}@{device_name}-{datetime.date.today()}"
                        pub_content_with_comment = f"{pub_content} {comment}"
                        
                        with open(new_pub_path, "w") as f:
                            f.write(pub_content_with_comment + "\n")
                        shutil.copy2(existing_priv, new_priv_path)
                        if os.name != 'nt': os.chmod(new_priv_path, 0o600)
                        
                        print_success(f"Imported: {key_name}")
                        log_action(f"IMPORTED: {key_name}")
                        priv_path, pub_path = new_priv_path, new_pub_path
                    except Exception as e:
                        print_error(f"Import failed: {e}")
                else:
                    print_error("File not found.")
            else:
                # GENERATE
                priv_path, pub_path = generate_key(final_user, device_name, default_dir)

            if priv_path and pub_path:
                # Add to Payload
                payload_path = os.path.join(default_dir, "AuthorizedKeysPayload.txt")
                added = False
                
                print("\n" + f"{Style.BLUE}-{Style.RESET}" * 40)
                add_choice = get_input(f"Add to '{os.path.basename(payload_path)}'? (yes/no)", "yes")
                if add_choice.lower() in ['yes', 'y']:
                    with open(pub_path, 'r') as f: pub_content = f.read().strip()
                    already_present = False
                    if os.path.exists(payload_path):
                         with open(payload_path, 'r') as f: 
                            if pub_content in f.read(): already_present = True
                    
                    if not already_present:
                        with open(payload_path, 'a') as f:
                            f.write(f"\n# Key: {os.path.basename(priv_path)} ({final_user}@{device_name})\n")
                            f.write(pub_content + "\n")
                        added = True
                        print_success("Added to Payload.")
                    else:
                        print(f"{Style.YELLOW}⚠️  Already in payload.{Style.RESET}")
                        added = True
                
                print_report_card(priv_path, pub_path, payload_path, added)
                get_input("Press Enter to return to main menu")


