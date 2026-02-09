# IconForge - Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - REBRAND - 2026-02-06
**The Iconfactory Rebrand**: Application renamed to **IconForge** to respect trademarks.

### Added
- **Icon Doctor (Audit Module)**:
  - New "Check Icon" button in main interface
  - Analyzes resolution, aspect ratio, edge quality, and cleanliness
  - Provides a "Report Card" with traffic-light status (Pass/Warn/Fail)
  - One-click "Auto-Fix All" button for detected issues

- **Smart Edge Reconstruction (Vector Power)**:
  - New `smart_cleanup` algorithm using 4x Super-Sampling
  - Synthesizes sharp, vector-like edges from jagged pixel inputs
  - Hard thresholding + Median Denoising + Soft AA Blur
  - Replaces simple blur for "Auto-Fix" operations

### Changed
- **Renamed Application** from "IconForge" to "IconForge"
- Window title updated to "IconForge - Professional Edition"
- Updated all documentation to reflect new identity

## [1.0.5] - 2026-02-06

### Changed
- **Clean by Default Philosophy** - Quality enhancement now ALWAYS applies
  - Clean Edges is now always-on (cannot be disabled)
  - Ensures professional, artifact-free icons by default
  - Edge threshold still adjustable for fine-tuning (0-50 alpha)
  - Philosophy: "If output is garbage, it's user choice, not app failure"
  
### UI Updates
- Updated "Advanced Edge Processing" to "Advanced Options"
- Clean Edges checkbox now shows "✓ Clean Edges (Always Applied)" and is disabled
- Defringe and Mask Adjust remain optional advanced features

## [1.0.4] - 2026-02-06

### Added
- **Auto-Crop After Masking**: New checkbox to automatically crop to tight bounds after color/border masking
  - Enabled by default for clean, professional results
  - Solves issue with 2-color graphics having unwanted transparent padding
  - Users can uncheck to preserve padding if desired
  - Works with both "Remove Color (Entire Image)" and "Remove Color (Borders Only)" modes

### Changed
- Improved masking mode labels for better clarity:
  - "None (Keep Original)"
  - "Auto-Crop (Detect Content)"
  - "Remove Color (Entire Image)"
  - "Remove Color (Borders Only)"

## [1.0.3] - 2026-02-06

### Added
- **Editable Icon Name Field**: Users can now customize the output icon name instead of being forced to use the source filename
  - Field auto-populates with source filename as a sensible default
  - Fully editable - type any name you want
  - Falls back to source filename if left empty
  - Clear placeholder text: "Enter icon name (defaults to source filename)"

- **100px PNG Size**: Added 100×100 pixel PNG to standard export sizes
  - Perfect for web forms and applications
  - Meets common form requirements (square, PNG, ≤100px)
  - Included in all PNG set exports

### Changed
- Updated README with new features documentation
- Improved user experience with clearer naming control

## [1.0.0] - 2026-02-06

### Initial Release
- Professional icon creation utility with Mac-like interface
- PyQt6 GUI with drag-and-drop support
- Multiple masking modes:
  - Auto-Crop: Intelligent content detection
  - Color Mask: Remove specific background colors
  - Border Only (Magic Wand): Remove colors from edges
- Advanced edge processing:
  - Defringe: Remove color halos
  - Clean Edges: Remove pixel debris (enabled by default)
  - Mask Adjust: Expand/contract transparency (-3 to +3 pixels)
- Multi-format export:
  - Windows ICO (3 variants: full alpha, binary alpha, with glow)
  - Mac ICNS (native iconutil support)
  - PNG set (16, 32, 48, 64, 128, 256, 512, 1024px)
- Organized output with metadata
- Optional ZIP archive creation
- Real-time preview with background options
- Licensed under CC BY-NC 4.0 (Attribution-NonCommercial)

---

## Version History

- **1.0.3** - Editable icon names + 100px PNG
- **1.0.0** - Initial release

## Git Commit History

To see detailed commit history:
```bash
git log --oneline
```

To revert to a specific version:
```bash
git checkout <commit-hash>
```

To see what changed in a specific commit:
```bash
git show <commit-hash>
```
