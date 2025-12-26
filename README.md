# Nebulator

A web application for creating transparent sprites from nebula images by converting grayscale values to alpha transparency.

## Features

- **Batch Processing** - Process multiple nebula images at once
- **Global Settings** - Set transparency thresholds for all images
- **Per-Image Overrides** - Customize settings for individual images
- **Live Preview** - See results in real-time before exporting
- **Image Viewer** - Click images to view in popup with customizable background
- **Export** - Save processed images with alpha channel

## Quick Start

1. **Install dependencies:**
   ```bash
   make setup
   ```
   Or use `setup.bat` on Windows.

2. **Place your images:**
   - Add PNG or JPG images to the `input/` folder
   - Images should have black backgrounds (no alpha channel)

3. **Run the app:**
   ```bash
   make run
   ```
   Or use `run.bat` on Windows.

4. **Open in browser:**
   - Navigate to `http://localhost:8000`

## How to Use

### Setting Transparency Thresholds

1. Adjust the **Min Gray** slider (0-255) - pixels at or below this value become fully transparent
2. Adjust the **Max Gray** slider (0-255) - pixels at or above this value become fully opaque
3. Click **Apply Settings** to process all images
4. Values between min and max are interpolated linearly

### Per-Image Customization

- Enable "Use custom settings" for any image
- Adjust min/max gray values for that specific image
- Custom settings override global settings

### Preview & Export

- Click any image to open it in a popup viewer
- Change background color in the popup to preview transparency
- Click **Export All Images** to save processed images to `output/` folder
- Exported files are named `nebula_001.png`, `nebula_002.png`, etc.

## Requirements

- Python 3.8+
- FastAPI
- Pillow (PIL)
- Uvicorn

