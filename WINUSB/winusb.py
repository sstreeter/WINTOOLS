#!/usr/bin/env python3
"""
WINUSB - Create Bootable Windows USB on macOS

A utility to create bootable Windows USB drives on macOS, handling large
install.wim files and ensuring compatibility with UEFI boot.

Copyright (c) 2026 Spencer Streeter
Licensed under CC BY-NC 4.0 (Attribution-NonCommercial)
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def run_command(cmd: List[str], check: bool = True, capture: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command and arguments as list
        check: Raise exception on non-zero exit
        capture: Capture stdout/stderr
        
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        if capture:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, check=check)
            return result.returncode, "", ""
    except subprocess.CalledProcessError as e:
        if capture:
            return e.returncode, e.stdout if e.stdout else "", e.stderr if e.stderr else ""
        return e.returncode, "", ""


def check_macos() -> bool:
    """Check if running on macOS."""
    if sys.platform != 'darwin':
        print_error("This tool only works on macOS")
        return False
    return True


def check_root() -> bool:
    """Check if running with root privileges."""
    if os.geteuid() != 0:
        print_warning("This tool requires administrator privileges")
        print_info("Please run with sudo: sudo python3 winusb.py")
        return False
    return True


def check_wimlib() -> bool:
    """Check if wimlib is installed."""
    returncode, _, _ = run_command(['which', 'wimlib-imagex'], check=False)
    return returncode == 0


def install_wimlib() -> bool:
    """Offer to install wimlib via Homebrew."""
    print_warning("wimlib is not installed (required for handling large install.wim files)")
    print_info("wimlib can be installed via Homebrew")
    
    # Check if Homebrew is installed
    returncode, _, _ = run_command(['which', 'brew'], check=False)
    if returncode != 0:
        print_error("Homebrew is not installed")
        print_info("Install Homebrew from: https://brew.sh")
        return False
    
    response = input(f"\n{Colors.CYAN}Install wimlib now? (y/n): {Colors.END}").strip().lower()
    if response == 'y':
        print_info("Installing wimlib...")
        returncode, stdout, stderr = run_command(['brew', 'install', 'wimlib'], check=False, capture=False)
        if returncode == 0:
            print_success("wimlib installed successfully")
            return True
        else:
            print_error("Failed to install wimlib")
            return False
    return False


def list_usb_drives() -> List[Dict[str, str]]:
    """
    List all external USB drives.
    
    Returns:
        List of dicts with drive info (identifier, name, size)
    """
    returncode, stdout, stderr = run_command(['diskutil', 'list', '-plist', 'external'])
    if returncode != 0:
        print_error("Failed to list drives")
        return []
    
    # Parse diskutil output
    returncode, stdout, stderr = run_command(['diskutil', 'list', 'external'])
    
    drives = []
    current_disk = None
    
    for line in stdout.split('\n'):
        # Match disk identifier lines like "/dev/disk2 (external, physical):"
        disk_match = re.match(r'/dev/(disk\d+)\s+\(external', line)
        if disk_match:
            current_disk = disk_match.group(1)
            continue
        
        # Get disk info
        if current_disk:
            returncode, info_out, _ = run_command(['diskutil', 'info', current_disk], check=False)
            if returncode == 0:
                name = ""
                size = ""
                for info_line in info_out.split('\n'):
                    if 'Volume Name:' in info_line or 'Device / Media Name:' in info_line:
                        name = info_line.split(':', 1)[1].strip()
                    elif 'Disk Size:' in info_line:
                        size = info_line.split(':', 1)[1].strip().split('(')[0].strip()
                
                if size:  # Only add if we got size info
                    drives.append({
                        'identifier': current_disk,
                        'name': name if name else 'Unnamed',
                        'size': size
                    })
            current_disk = None
    
    return drives


def select_usb_drive(drives: List[Dict[str, str]]) -> Optional[str]:
    """
    Interactive USB drive selection.
    
    Args:
        drives: List of available drives
        
    Returns:
        Selected disk identifier or None
    """
    if not drives:
        print_error("No external USB drives found")
        print_info("Please insert a USB drive and try again")
        return None
    
    print_header("Available USB Drives")
    for i, drive in enumerate(drives, 1):
        print(f"{i}. {drive['name']}")
        print(f"   Identifier: {drive['identifier']}")
        print(f"   Size: {drive['size']}\n")
    
    while True:
        try:
            choice = input(f"{Colors.CYAN}Select drive number (or 'q' to quit): {Colors.END}").strip()
            if choice.lower() == 'q':
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(drives):
                selected = drives[index]
                
                # Confirmation
                print_warning(f"\n⚠️  WARNING: All data on {selected['name']} ({selected['identifier']}) will be ERASED!")
                confirm = input(f"{Colors.YELLOW}Type 'YES' to confirm: {Colors.END}").strip()
                
                if confirm == 'YES':
                    return selected['identifier']
                else:
                    print_info("Cancelled")
                    return None
            else:
                print_error("Invalid selection")
        except ValueError:
            print_error("Please enter a number")


def validate_iso(iso_path: str) -> bool:
    """
    Validate that the file is a Windows ISO.
    
    Args:
        iso_path: Path to ISO file
        
    Returns:
        True if valid Windows ISO
    """
    path = Path(iso_path)
    
    # Check file exists
    if not path.exists():
        print_error(f"ISO file not found: {iso_path}")
        return False
    
    # Check file is readable
    if not path.is_file():
        print_error(f"Not a file: {iso_path}")
        return False
    
    # Mount ISO temporarily to check contents
    print_info("Validating ISO...")
    returncode, stdout, stderr = run_command(['hdiutil', 'attach', '-noverify', '-nobrowse', '-mountpoint', '/tmp/winusb_iso_check', str(path)], check=False)
    
    if returncode != 0:
        print_error("Failed to mount ISO")
        return False
    
    # Check for Windows-specific files
    mount_point = Path('/tmp/winusb_iso_check')
    is_valid = False
    
    if (mount_point / 'sources' / 'install.wim').exists() or \
       (mount_point / 'sources' / 'install.esd').exists():
        is_valid = True
        print_success("Valid Windows ISO detected")
        
        # Try to detect Windows version
        if (mount_point / 'sources' / 'install.wim').exists():
            wim_size = (mount_point / 'sources' / 'install.wim').stat().st_size
            wim_size_gb = wim_size / (1024 ** 3)
            print_info(f"install.wim size: {wim_size_gb:.2f} GB")
            if wim_size > 4 * 1024 ** 3:
                print_warning("install.wim is >4GB - will need to split for FAT32")
    else:
        print_error("Not a valid Windows ISO (missing install.wim/install.esd)")
    
    # Unmount
    run_command(['hdiutil', 'detach', '/tmp/winusb_iso_check'], check=False)
    
    return is_valid


def main():
    """Main entry point."""
    print_header("WINUSB - Windows Bootable USB Creator for macOS")
    print(f"{Colors.CYAN}Copyright (c) 2026 Spencer Streeter{Colors.END}")
    print(f"{Colors.CYAN}Licensed under CC BY-NC 4.0{Colors.END}\n")
    
    # Check prerequisites
    if not check_macos():
        sys.exit(1)
    
    if not check_root():
        sys.exit(1)
    
    if not check_wimlib():
        if not install_wimlib():
            print_error("wimlib is required but not installed")
            sys.exit(1)
    
    # Get ISO path
    if len(sys.argv) < 2:
        print_error("Usage: sudo python3 winusb.py <path-to-windows.iso>")
        sys.exit(1)
    
    iso_path = sys.argv[1]
    
    # Validate ISO
    if not validate_iso(iso_path):
        sys.exit(1)
    
    # List and select USB drive
    drives = list_usb_drives()
    disk_id = select_usb_drive(drives)
    
    if not disk_id:
        print_info("Operation cancelled")
        sys.exit(0)
    
    print_success(f"Selected drive: {disk_id}")
    
    # Format the USB drive
    print_header("Step 1: Formatting USB Drive")
    if not format_usb_drive(disk_id):
        print_error("Failed to format USB drive")
        sys.exit(1)
    
    # Mount ISO and copy files
    print_header("Step 2: Copying Windows Files")
    if not copy_windows_files(iso_path, disk_id):
        print_error("Failed to copy Windows files")
        sys.exit(1)
    
    # Success!
    print_header("✓ Bootable USB Created Successfully!")
    print_success("Your Windows bootable USB is ready")
    print_info("\nNext steps:")
    print_info("1. Safely eject the USB drive")
    print_info("2. Insert it into the target PC")
    print_info("3. Boot from USB (usually F12, F9, F8, or F11 during startup)")
    print_info("4. Follow Windows installation prompts")
    print_info("\nNote: You may need to disable Secure Boot in BIOS/UEFI")


def format_usb_drive(disk_id: str) -> bool:
    """
    Format USB drive as FAT32 with MBR.
    
    Args:
        disk_id: Disk identifier (e.g., 'disk2')
        
    Returns:
        True if successful
    """
    print_info(f"Formatting /dev/{disk_id} as FAT32 with MBR...")
    print_warning("This will erase all data on the drive!")
    
    # Unmount any mounted volumes first
    run_command(['diskutil', 'unmountDisk', f'/dev/{disk_id}'], check=False)
    
    # Format as MS-DOS (FAT32) with MBR
    cmd = [
        'diskutil', 'eraseDisk',
        'MS-DOS', 'WINDOWS11',
        'MBR', f'/dev/{disk_id}'
    ]
    
    returncode, stdout, stderr = run_command(cmd, check=False, capture=False)
    
    if returncode != 0:
        print_error("Formatting failed")
        return False
    
    print_success("USB drive formatted successfully")
    return True


def copy_windows_files(iso_path: str, disk_id: str) -> bool:
    """
    Mount ISO and copy all files to USB, handling large install.wim.
    
    Args:
        iso_path: Path to Windows ISO
        disk_id: Disk identifier
        
    Returns:
        True if successful
    """
    # Mount the ISO
    print_info("Mounting Windows ISO...")
    returncode, stdout, stderr = run_command(['hdiutil', 'attach', '-noverify', '-nobrowse', iso_path], check=False)
    
    if returncode != 0:
        print_error("Failed to mount ISO")
        return False
    
    # Find mount point from output
    mount_point = None
    for line in stdout.split('\n'):
        if '/Volumes/' in line:
            parts = line.split('\t')
            if len(parts) >= 3:
                mount_point = parts[-1].strip()
                break
    
    if not mount_point:
        print_error("Could not determine ISO mount point")
        return False
    
    print_success(f"ISO mounted at: {mount_point}")
    
    # Check install.wim size
    wim_path = Path(mount_point) / 'sources' / 'install.wim'
    needs_split = False
    
    if wim_path.exists():
        wim_size = wim_path.stat().st_size
        wim_size_gb = wim_size / (1024 ** 3)
        
        if wim_size > 4 * 1024 ** 3:
            print_warning(f"install.wim is {wim_size_gb:.2f} GB (>4GB limit for FAT32)")
            print_info("Will split install.wim using wimlib")
            needs_split = True
    
    # Copy all files except install.wim
    print_info("Copying Windows files to USB (this may take several minutes)...")
    usb_mount = f'/Volumes/WINDOWS11'
    
    # Use rsync to copy files
    exclude_args = ['--exclude=sources/install.wim'] if needs_split else []
    cmd = ['rsync', '-avh', '--progress'] + exclude_args + [f'{mount_point}/', usb_mount]
    
    returncode, stdout, stderr = run_command(cmd, check=False, capture=False)
    
    if returncode != 0:
        print_error("Failed to copy files")
        run_command(['hdiutil', 'detach', mount_point], check=False)
        return False
    
    print_success("Files copied successfully")
    
    # Handle install.wim if needed
    if needs_split:
        print_info("Splitting install.wim...")
        
        # Create sources directory if it doesn't exist
        sources_dir = Path(usb_mount) / 'sources'
        sources_dir.mkdir(exist_ok=True)
        
        # Split using wimlib (3800MB chunks to stay under 4GB)
        cmd = [
            'wimlib-imagex', 'split',
            str(wim_path),
            str(sources_dir / 'install.swm'),
            '3800'
        ]
        
        returncode, stdout, stderr = run_command(cmd, check=False, capture=False)
        
        if returncode != 0:
            print_error("Failed to split install.wim")
            run_command(['hdiutil', 'detach', mount_point], check=False)
            return False
        
        print_success("install.wim split successfully")
    
    # Unmount ISO
    print_info("Unmounting ISO...")
    run_command(['hdiutil', 'detach', mount_point], check=False)
    
    # Eject USB
    print_info("Ejecting USB drive...")
    run_command(['diskutil', 'eject', f'/dev/{disk_id}'], check=False)
    
    return True


if __name__ == '__main__':
    main()
