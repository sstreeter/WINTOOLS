# AI Generation Plan: IconForge (Professional Icon Studio)

## 1. Project Overview
**Name**: IconForge
**Goal**: Create a professional-grade, desktop GUI application for generating application icons (macOS `.icns`, Windows `.ico`, and PNG sets) from a single source image.
**Target Audience**: Developers and Designers who need to quickly produce production-ready icons with advanced post-processing (masking, borders, effects).

## 2. Technical Stack
*   **Language**: Python 3.10+
*   **GUI Framework**: PyQt6
    *   *Why*: Native look and feel, high performance for image rendering, robust widget set (Splitters, ScrollAreas).
*   **Image Processing**: Pillow (PIL)
    *   *Why*: Removing backgrounds, resizing, filters (Gaussian Blur, Unsharp Mask), Alpha compositing.
*   **Data Science (Optional)**: NumPy / SciPy
    *   *Why*: Fast pixel-level manipulation (chroma keying), advanced filters (Laplacian variance for sharpness detection).
*   **Vector Support (Optional)**: svglib, reportlab (or Cairo)
    *   *Why*: To support SVG input and rasterize firmly to high-res PNG.

## 3. Core Architecture
The application should follow a modular "Pipeline" architecture.

### Directory Structure
```
IconForge/
├── IconForge.py           # Entry point
├── ui/
│   ├── main_window.py     # Main GUI Logic & Layout
│   ├── audit_dialog.py    # "Icon Doctor" Report Dialog
│   └── styles.py          # Dark Theme CSS (QSS)
├── core/
│   ├── image_processor.py # State machine for the image pipeline
│   ├── masking.py         # Background removal (Chroma Key, Magic Wand)
│   ├── cropping.py        # Auto-cropping logic
│   ├── stroke.py          # Border generation & Liquid Polish
│   ├── filters.py         # Color filters (Sepia, Grayscale)
│   ├── geometry.py        # Resizing, Rounding
│   ├── icon_audit.py      # Quality assurance (Audit)
│   └── export.py          # .ico / .icns saving logic
└── utils/                 # Helpers (Archive, File I/O)
```

## 4. Feature Requirements (The "Prompt")

### Phase 1: The Canvas & Input
*   **Split View UI**: Implementing a `QSplitter` with the Control Panel on the Left (resizable) and a "Sticky" Artboard on the Right.
*   **Input Handling**: Drag-and-drop support for PNG, JPG, SVG, WEBP.
*   **Compact Info**: Display filename, resolution, and basic file stats.

### Phase 2: The Pipeline (Processing Steps)
The application must process the image in this specific order (The "Render Loop"):
1.  **Input**: Load Source.
2.  **Masking**:
    *   *Chroma Key*: Remove specific background color (with tolerance).
    *   *Magic Wand*: Flood fill transparency from corners.
    *   *Refine*: Erode/Dilate mask to choke edges.
3.  **Cropping**: Auto-crop transparent borders.
4.  **Composition**:
    *   Canvas resize (e.g., 1024x1024).
    *   Padding/Margins.
5.  **Geometry**:
    *   Rounding corners (Radius slider 0-50%).
6.  **Effects**:
    *   *Stroke (Border)*: Outside/Center/Inside alignment + Color.
    *   *Shadow*: Drop shadow opacity/blur.
    *   *Glow*: Outer glow.
7.  **Output**: Render final preview.

### Phase 3: "Icon Doctor" (Audit System)
*   **Start**: Button to "Audit" the current icon.
*   **Checks**:
    *   Resolution < 512px? (Warning)
    *   Non-Square aspect ratio? (Error)
    *   Jagged Edges (Aliasing)? (Using Alpha channel histogram/variance).
    *   Stray Pixels (Dirty alpha)?
*   **Comparison Mode**:
    *   Load a "Gold Standard" reference image.
    *   Calculate Deltas: Sharpness (Gradient Mag), Contrast, Complexity.
    *   Display "Yours vs Ref" in the report.

## 5. UI/UX Design Guidelines ("The Vibe")
*   **Theme**: Dark Mode (VS Code style). Dark greys (`#1e1e1e`, `#252526`), Blue accents (`#007acc`).
*   **Layout**:
    *   *Left Panel*: Vertical Stack of collapsible groups (Input -> Masking -> Geometry -> Effects -> Export).
    *   *Right Panel*: Zoomable, pannable viewport. Checkerboard background for transparency.
*   **Interactivity**:
    *   Sliders should auto-update the preview (Debounced if heavy).
    *   "Compare" slider to wipe between Source and Result (or Ref and Result).

## 6. Implementation Steps for AI
If asking an AI to build this, break it down:

**Prompt 1**: "Set up the basic PyQt6 GUI with a dark theme. Create a Split Layout: Left Control Panel (Placeholder), Right Artboard (with Checkerboard background). Handle Drag & Drop of an image file to display it on the Artboard."

**Prompt 2**: "Implement the `ImageProcessor` class using Pillow. It should take the source image, resize it to 1024x1024, and apply a simple 'Round Corners' filter. Connect a Slider in the Left Panel to control the Corner Radius."

**Prompt 3**: "Add the 'Background Removal' module. Add a color picker to the UI to select a 'Key Color'. Implement `core/masking.py` using NumPy to set all pixels matching that color (within tolerance) to Transparent."

**Prompt 4**: "Implement the 'Stroke Engine'. Add a 'Border' group to the UI with Color, Width, and Alignment (Inside/Center/Outside) controls. The stroke must be drawn on the alpha mask of the image."

**Prompt 5**: "Add the Export functionality. Generate `icns` (Mac), `ico` (Windows), and a folder of PNGs (16x16 to 1024x1024). Use threads (`QThread`) to keep the UI responsive during export."

## 7. Key Algorithms (Secrets)
*   **Liquid Polish**: Upscale 4x -> Gaussian Blur -> Threshold (Levels) -> Downscale. This smooths jagged vector edges.
*   **Stroke Alignment**:
    *   *Outside*: Dilate Mask - Original Mask.
    *   *Inside*: Original Mask - Eroded Mask.
