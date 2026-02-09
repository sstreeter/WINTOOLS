# 🎨 WINTOOLS: IconForge
Professional icon creation utility with advanced masking and edge processing.

## 📋 Overview
**IconForge** (formerly IconForge) is a powerful desktop application for creating professional system icons. It handles the heavy lifting of background removal, edge cleanup, and multi-format export so your system shortcuts and tools look their best.

### Core Features
- **Pro Masking**: Magic wand color removal and auto-cropping.
- **Edge Precision**: "Defringe" halos and "Clean Edges" to remove pixel debris.
- **Multi-Format**: Generates Windows ICO (full/binary alpha), Mac ICNS, and PNG sets.
- **Batch Metadata**: Automatically organizes outputs with `metadata.json`.

## 🛠️ Requirements
- **Python 3.8+**
- **Dependencies**:
  ```bash
  pip install PyQt6 Pillow numpy
  ```
- **macOS (Optional)**: Required for `.icns` export via `iconutil`.

## 🚀 Usage
Run the application from the `IconForge` directory:
```bash
python IconForge.py
```

### Quick Workflow
1. **Load**: Drag an image into the workspace.
2. **Refine**: Use "Advanced Edge Processing" to clean up halos or stray pixels.
3. **Format**: Select your target outputs (ICO, ICNS, PNG).
4. **Generate**: Click "Generate Icons" to create a structured output folder.

## 📁 Structure
- `IconForge.py`: Main application entry point.
- `ui/`: PyQt6 interface components.
- `core/`: Processing engines (Masking, Composition, Export).
- `history/`: Log of previous icon generation tasks.

- ❌ **Commercial use prohibited** without permission

---
## 📜 Credits & Licensing
This module uses several professional open-source projects:
- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)**: Used for the graphical user interface (GPLv3).
- **[Pillow (PIL)](https://python-pillow.org/)**: Used for image processing (HPND).
- **[NumPy](https://numpy.org/)**: Used for high-performance array operations (BSD).
- **[SciPy](https://scipy.org/)**: Used for advanced multi-dimensional filtering (BSD).

*All trademarks belong to their respective owners.*
