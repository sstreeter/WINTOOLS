# WINUSB

Create bootable Windows USB drives on macOS with ease.

## What It Does

WINUSB automates the process of creating bootable Windows USB installation drives on macOS. It handles all the complexity:

- ✅ Detects and formats USB drives (FAT32 with MBR)
- ✅ Validates Windows ISO files
- ✅ Handles large install.wim files (>4GB) automatically
- ✅ Creates UEFI-bootable drives
- ✅ Multiple safety confirmations

## Requirements

- **macOS** (uses diskutil and hdiutil)
- **Python 3.6+**
- **Homebrew** (for wimlib)
- **wimlib** (auto-installed if missing)
- **USB drive** (16GB+ recommended)
- **Windows ISO** (Windows 10 or 11)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/sstreeter/WINTOOLS.git
cd WINTOOLS/WINUSB
```

2. Make the script executable:
```bash
chmod +x winusb.py
```

3. Install wimlib (if not already installed):
```bash
brew install wimlib
```

## Usage

**Basic usage:**
```bash
sudo python3 winusb.py /path/to/Windows11.iso
```

The script will:
1. Validate your Windows ISO
2. Show available USB drives
3. Ask you to select a drive
4. Confirm before erasing (requires typing 'YES')
5. Format the drive as FAT32 with MBR
6. Copy all Windows files
7. Split install.wim if needed (>4GB)
8. Eject the USB when complete

**Example:**
```bash
$ sudo python3 winusb.py ~/Downloads/Win11_24H2_English_x64.iso

============================================================
WINUSB - Windows Bootable USB Creator for macOS
============================================================

ℹ Validating ISO...
✓ Valid Windows ISO detected
ℹ install.wim size: 5.12 GB
⚠ install.wim is >4GB - will need to split for FAT32

============================================================
Available USB Drives
============================================================

1. SanDisk Ultra
   Identifier: disk2
   Size: 32.0 GB

Select drive number (or 'q' to quit): 1

⚠  WARNING: All data on SanDisk Ultra (disk2) will be ERASED!
Type 'YES' to confirm: YES

✓ Selected drive: disk2

============================================================
Step 1: Formatting USB Drive
============================================================

ℹ Formatting /dev/disk2 as FAT32 with MBR...
✓ USB drive formatted successfully

============================================================
Step 2: Copying Windows Files
============================================================

ℹ Mounting Windows ISO...
✓ ISO mounted at: /Volumes/CCCOMA_X64FRE_EN-US_DV9
ℹ Copying Windows files to USB (this may take several minutes)...
✓ Files copied successfully
ℹ Splitting install.wim...
✓ install.wim split successfully

============================================================
✓ Bootable USB Created Successfully!
============================================================

✓ Your Windows bootable USB is ready

Next steps:
1. Safely eject the USB drive
2. Insert it into the target PC
3. Boot from USB (usually F12, F9, F8, or F11 during startup)
4. Follow Windows installation prompts

Note: You may need to disable Secure Boot in BIOS/UEFI
```

## How It Works

1. **ISO Validation**: Checks for `sources/install.wim` to confirm it's a Windows ISO
2. **USB Detection**: Lists external drives using `diskutil list external`
3. **Formatting**: Uses `diskutil eraseDisk` to format as FAT32 with MBR
4. **File Copying**: Uses `rsync` to copy all files from ISO to USB
5. **install.wim Handling**: 
   - If >4GB: Uses `wimlib-imagex split` to create install.swm files
   - If <4GB: Copies directly
6. **Cleanup**: Unmounts ISO and ejects USB

## Troubleshooting

### "wimlib is not installed"
Install it via Homebrew:
```bash
brew install wimlib
```

### "No external USB drives found"
- Ensure USB drive is plugged in
- Try a different USB port
- Check if drive appears in Disk Utility

### "Failed to mount ISO"
- Verify ISO file is not corrupted
- Download ISO again from Microsoft
- Check file permissions

### PC won't boot from USB
- Enter BIOS/UEFI (usually F2, Del, or F12 during startup)
- Disable Secure Boot
- Enable Legacy/CSM boot if needed
- Set USB as first boot device

### "Install.wim is too large" error during Windows install
This shouldn't happen if wimlib splitting worked correctly. If you see this:
- Verify wimlib is installed: `which wimlib-imagex`
- Check USB has install.swm files (not install.wim) in sources folder

## License

Copyright (c) 2026 Spencer Streeter

Licensed under [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE)

**Free for personal and educational use. Commercial use requires permission.**

## Credits

Created by Spencer Streeter

Uses:
- [wimlib](https://wimlib.net/) for handling large Windows image files
- macOS built-in tools (diskutil, hdiutil, rsync)

## Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub Issues.
