# AI Generation Plan: RedKetchup Clone (Desktop Edition)

## 1. Project Overview
**Goal**: Build a desktop replica of the **RedKetchup Icon Converter** using Python.
**Concept**: A utilitarian, "all-in-one" single-page dashboard for converting any image into a highly compatible Windows ICO, macOS ICNS, or Favicon bundle.
**Key Difference**: Unlike "IconForge" which focuses on *artistic creation*, this tool focuses on *compatibility, conversion conversion, and precise format control*.

## 2. Technical Stack
*   **Language**: Python 3.10+
*   **GUI**: PyQt6 (Scrollable Dashboard Layout)
*   **Core**: Pillow (PIL) for processing, `ico` library or PIL for saving.

## 3. UI/UX Design ("The RedKetchup Flow")
The UI should be a **Single Scrollable Window** divided into clear, numbered sections, mimicking the website's flow:

1.  **Select Image**: Large Drop Zone + Clipboard Paste support.
2.  **Edit Icon**: Crop, Rotate, Flip.
3.  **Style Icon**: Background Color, Rounded Corners (Shape).
4.  **Output Settings**: File Format, Icon Sizes, Color Depth.
5.  **Download**: "Convert & Save" button.

## 4. Feature Requirements (The Prompts)

### Prompt 1: The Scrollable Dashboard
"Create a PyQt6 application with a `QScrollArea` as the central widget. Inside, create a vertical layout containing 4 distinct `QGroupBox` sections: '1. Select', '2. Style', '3. Output', '4. Save'. Apply a clean, flat stylesheet with a distinct header color for each group."

### Prompt 2: Advanced Input & Editing
"Implement the Input Section. Support Drag & Drop AND Paste from Clipboard (`ctrl+v`). Display the loaded image info (Resolution, Type).
Add an 'Edit' toolbar below the preview:
*   **Rotate**: -90, +90 buttons.
*   **Flip**: Horizontal, Vertical.
*   **Crop**: Function to auto-center crop to a square aspect ratio (keeping center content)."

### Prompt 3: Styling (Background & Shape)
"Implement the Styling Section:
1.  **Background Color**: A checkbox to 'Fill Background' and a `QColorDialog` button. If the source is transparent, this layers a solid color behind it.
2.  **Shape / Borders**: A slider (0-100) for 'Rounded Corners'.
    *   0 = Square.
    *   100 = Perfect Circle.
    *   *Implementation*: Create a rounded rectangle mask using `ImageDraw` and apply it to the alpha channel."

### Prompt 4: Advanced Export Grid
"Implement the 'Output Settings' for ICO files:
Create a Grid Layout of checkboxes for specific sizes:
[ ] 16x16  [ ] 24x24  [ ] 32x32  [ ] 48x48
[ ] 64x64  [ ] 96x96  [ ] 128x128 [ ] 256x256 (PNG compressed)

Add a ComboBox for **Color Depth**:
*   32-bit (RGBA) - Default
*   8-bit (256 colors) - For legacy support (requires Quantization).
*   24-bit (No Alpha)."

### Prompt 5: The Converter Engine
"Write the `ConversionEngine` class.
The `convert()` method should:
1.  Take the processed PIL image.
2.  Resize it to ALL checked sizes using `LANCZOS` resampling.
3.  If 8-bit depth is selected, quantize colors to 256 using an adaptive palette.
4.  If 256x256 is selected, ensure it uses PNG compression within the ICO container (Vista+ support).
5.  Save the file to disk."

## 5. Key Algorithms
*   **Circular Crop**:
    ```python
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0,0), (w,h)], radius=w//2, fill=255)
    image.putalpha(mask)
    ```
*   **Legacy 8-bit Support**:
    ```python
    # Quantize to 256 colors
    img = img.quantize(colors=256, method=2, kmeans=1)
    ```
