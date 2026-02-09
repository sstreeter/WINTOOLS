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
        return key_path, pub_key_path
    except subprocess.CalledProcessError as e:
        print_error(f"Error generating key: {e}")
        return None, None
    except FileNotFoundError:
        print_error("ssh-keygen command not found. Please install OpenSSH Client.")
        return None, None

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

def main():
    print_header()
    
    # 0. Mode Selection
    print(f"\n{Style.BOLD}Select Wizard Mode:{Style.RESET}")
    print(f"  [{Style.CYAN}1{Style.RESET}] Generate NEW Ed25519 Key Pair (Recommended)")
    print(f"  [{Style.CYAN}2{Style.RESET}] Import EXISTING Private Key")
    
    wiz_mode = get_input("Select Option", "1")
    
    # 1. Output Directory
    default_dir = os.path.join(os.getcwd(), "AuthorizedKeys")
    output_dir = get_input("Output Directory", default_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Identity Setup (Username & Device) – Common to both modes
    suggestions = get_username_suggestions()
    
    print(f"\n{Style.BOLD}Select a standardized username:{Style.RESET}")
    for i, name in enumerate(suggestions):
        print(f"  [{Style.CYAN}{i+1}{Style.RESET}] {name}")
    print(f"  [{Style.CYAN}{len(suggestions)+1}{Style.RESET}] Custom...")
    
    choice = get_input("Select Option", "1")
    
    final_user = ""
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(suggestions):
            final_user = suggestions[idx]
        else:
            final_user = get_input("Enter Custom Username (a-z0-9._- only)")
    except:
         final_user = get_input("Enter Custom Username (a-z0-9._- only)")
         
    # Validate via Policy
    final_user = InputPolicy.sanitize_username(final_user)
    if len(final_user) < 2:
        print_error("Username too short. Defaulting to 'admin'.")
        final_user = "admin"
        
    print_success(f"Selected Username: {final_user}")

    # 3. Source Device Name (Smart Hardware ID)
    raw_hostname = platform.node().split('.')[0]
    hostname = InputPolicy.sanitize_hostname(raw_hostname)
    hardware_id = get_hardware_id()
    
    def format_dev_name(base, tag=None):
        if not tag:
            return InputPolicy.sanitize_hostname(base)
        
        # If adding a tag, we might need to truncate the base to fit in 15 chars
        # Format: base-tag
        max_base = InputPolicy.MAX_HOSTNAME_LEN - (len(tag) + 1) # +1 for the hyphen
        clean_base = InputPolicy.sanitize_hostname(base)[:max_base].strip('-')
        return InputPolicy.sanitize_hostname(f"{clean_base}-{tag}")

    dev_suggestions = [
        format_dev_name(hardware_id),        # 1. Smart (mba2023)
        format_dev_name(hardware_id, "camp"),# 2. Smart Campus (shortened tag for space)
        format_dev_name(hardware_id, "wfh"), # 3. Smart WFH
        format_dev_name(hostname, "camp"),   # 4. Hostname Campus
        format_dev_name(hostname, "wfh"),    # 5. Hostname WFH
        format_dev_name(hostname)            # 6. Simple
    ]
    
    print(f"\n{Style.BOLD}Select Device Context:{Style.RESET}")
    # Deduplicate while preserving order
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
             device_name = get_input("Enter Device Name (e.g. laptop-win)")
    except:
         device_name = get_input("Enter Device Name (e.g. laptop-win)")
         
    # Strict Hostname Sanitization via Policy
    device_name = InputPolicy.sanitize_hostname(device_name)
    print_success(f"Selected Device: {device_name}")

    priv_path = None
    pub_path = None

    if wiz_mode == "2":
        # --- IMPORT MODE ---
        print(f"\n{Style.BOLD}--- Import Workflow ---{Style.RESET}")
        existing_priv = get_input("Path to your existing PRIVATE key").strip()
        # Remove quotes if user dragged/dropped file
        existing_priv = existing_priv.replace('"', '').replace("'", "")
        
        if not os.path.exists(existing_priv):
            print_error(f"File not found: {existing_priv}")
            return

        # Prepare new names
        key_name = f"id_ed25519_{device_name}_{final_user}"
        new_priv_path = os.path.join(output_dir, key_name)
        new_pub_path = f"{new_priv_path}.pub"

        # Regenerate Public Key (ssh-keygen -y)
        print(f"Regenerating public key for {os.path.basename(existing_priv)}...")
        try:
            # -y flag reads private and outputs public to stdout
            cmd = ["ssh-keygen", "-y", "-f", existing_priv]
            pub_content = subprocess.check_output(cmd).decode().strip()
            
            # Add comment to the public key
            comment = f"{final_user}@{device_name}-{datetime.date.today()}"
            pub_content_with_comment = f"{pub_content} {comment}"

            # Save Public Key
            with open(new_pub_path, "w") as f:
                f.write(pub_content_with_comment + "\n")
            
            # Copy Private Key
            shutil.copy2(existing_priv, new_priv_path)
            # Ensure strict permissions on copy (chmod 600 if not on windows)
            if os.name != 'nt':
                os.chmod(new_priv_path, 0o600)

            print_success(f"Key Imported and Standardized: {key_name}")
            priv_path, pub_path = new_priv_path, new_pub_path

        except subprocess.CalledProcessError:
            print_error("Failed to read private key. Is it password protected? (ssh-keygen requires the password to read it)")
            return
        except Exception as e:
            print_error(f"Unexpected error during import: {e}")
            return

    else:
        # --- GENERATE MODE ---
        priv_path, pub_path = generate_key(final_user, device_name, output_dir)
    
    if priv_path and pub_path:
        # 5. Success & Instructions
        payload_path = os.path.join(output_dir, "AuthorizedKeysPayload.txt")
        added = False
        
        print("\n" + f"{Style.BLUE}-{Style.RESET}" * 40)
        print(f"{Style.BOLD}Deployment Step:{Style.RESET}")
        print("To allow THIS computer to access your servers, we need to add its Public Key")
        print("to the master list 'AuthorizedKeysPayload.txt'.")
        
        add_choice = get_input(f"Add this key to '{os.path.basename(payload_path)}'? (yes/no)", "yes")
        if add_choice.lower() in ['yes', 'y']:
            with open(pub_path, 'r') as f:
                pub_content = f.read().strip()
            
            # Check if already in payload to avoid duplicates
            already_present = False
            if os.path.exists(payload_path):
                with open(payload_path, 'r') as f:
                    if pub_content in f.read():
                        already_present = True
            
            if not already_present:
                with open(payload_path, 'a') as f:
                    f.write(f"\n# Key: {os.path.basename(priv_path)} (User: {final_user}, Device: {device_name})\n")
                    f.write(pub_content + "\n")
                print_success(f"Added to {os.path.basename(payload_path)}")
                added = True
            else:
                print(f"{Style.YELLOW}⚠️  Key already in payload file.{Style.RESET}")
                added = True

        # Final Report
        print_report_card(priv_path, pub_path, payload_path, added)

    print(f"\n{Style.DIM}Wizard Finished. Goodbye 👋{Style.RESET}")

if __name__ == "__main__":
    main()
