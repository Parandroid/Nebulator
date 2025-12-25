"""
FastAPI application for Nebulator - Nebula Sprite Transparency Generator
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict
import os
from pathlib import Path
from PIL import Image
import io

from image_processor import process_image, save_processed_image

app = FastAPI(title="Nebulator")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration
INPUT_FOLDER = Path("input")
OUTPUT_FOLDER = Path("output")

# Ensure folders exist
INPUT_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Global state
global_min_gray = 0
global_max_gray = 255
image_overrides: Dict[str, Dict[str, int]] = {}  # {filename: {"min_gray": int, "max_gray": int}}


class SettingsModel(BaseModel):
    min_gray: int
    max_gray: int


class ImageSettingsModel(BaseModel):
    min_gray: Optional[int] = None
    max_gray: Optional[int] = None


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    html_path = Path("static/index.html")
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse("<h1>Nebulator</h1><p>Please create static/index.html</p>")


@app.get("/api/images")
async def list_images():
    """List all PNG images in the input folder"""
    try:
        image_files = []
        for file in INPUT_FOLDER.iterdir():
            if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                image_files.append(file.name)
        return {"images": sorted(image_files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/preview/{filename}")
async def get_preview(
    filename: str,
    min_gray: Optional[int] = Query(None, ge=0, le=255),
    max_gray: Optional[int] = Query(None, ge=0, le=255)
):
    """
    Get processed preview image with alpha channel.
    Uses per-image override if exists, otherwise uses provided params or global defaults.
    """
    try:
        image_path = INPUT_FOLDER / filename
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Determine which parameters to use
        if filename in image_overrides:
            # Use per-image override
            override = image_overrides[filename]
            use_min_gray = override.get("min_gray", global_min_gray)
            use_max_gray = override.get("max_gray", global_max_gray)
        elif min_gray is not None and max_gray is not None:
            # Use provided query parameters
            use_min_gray = min_gray
            use_max_gray = max_gray
        else:
            # Use global defaults
            use_min_gray = global_min_gray
            use_max_gray = global_max_gray
        
        # Process the image
        processed_img = process_image(str(image_path), use_min_gray, use_max_gray)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        processed_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return Response(
            content=img_bytes.getvalue(),
            media_type="image/png"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error processing preview for {filename}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_global_settings(settings: SettingsModel):
    """Update global gray value settings"""
    global global_min_gray, global_max_gray
    
    if settings.min_gray < 0 or settings.min_gray > 255:
        raise HTTPException(status_code=400, detail="min_gray must be between 0 and 255")
    if settings.max_gray < 0 or settings.max_gray > 255:
        raise HTTPException(status_code=400, detail="max_gray must be between 0 and 255")
    
    global_min_gray = settings.min_gray
    global_max_gray = settings.max_gray
    
    return {
        "min_gray": global_min_gray,
        "max_gray": global_max_gray,
        "message": "Global settings updated"
    }


@app.get("/api/settings")
async def get_global_settings():
    """Get current global settings"""
    return {
        "min_gray": global_min_gray,
        "max_gray": global_max_gray
    }


@app.post("/api/settings/{filename}")
async def set_image_override(filename: str, settings: ImageSettingsModel):
    """Set per-image override settings"""
    image_path = INPUT_FOLDER / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    if filename not in image_overrides:
        image_overrides[filename] = {}
    
    if settings.min_gray is not None:
        if settings.min_gray < 0 or settings.min_gray > 255:
            raise HTTPException(status_code=400, detail="min_gray must be between 0 and 255")
        image_overrides[filename]["min_gray"] = settings.min_gray
    
    if settings.max_gray is not None:
        if settings.max_gray < 0 or settings.max_gray > 255:
            raise HTTPException(status_code=400, detail="max_gray must be between 0 and 255")
        image_overrides[filename]["max_gray"] = settings.max_gray
    
    return {
        "filename": filename,
        "settings": image_overrides[filename],
        "message": "Image override updated"
    }


@app.delete("/api/settings/{filename}")
async def remove_image_override(filename: str):
    """Remove per-image override (revert to global settings)"""
    if filename in image_overrides:
        del image_overrides[filename]
        return {"message": f"Override removed for {filename}"}
    return {"message": f"No override found for {filename}"}


@app.get("/api/settings/{filename}")
async def get_image_settings(filename: str):
    """Get settings for a specific image (override if exists, otherwise global)"""
    image_path = INPUT_FOLDER / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    if filename in image_overrides:
        return {
            "filename": filename,
            "min_gray": image_overrides[filename].get("min_gray", global_min_gray),
            "max_gray": image_overrides[filename].get("max_gray", global_max_gray),
            "is_override": True
        }
    else:
        return {
            "filename": filename,
            "min_gray": global_min_gray,
            "max_gray": global_max_gray,
            "is_override": False
        }


@app.post("/api/export")
async def export_images():
    """Export all processed images to the output folder"""
    try:
        exported_files = []
        counter = 1
        
        # Get all image files
        image_files = []
        for file in INPUT_FOLDER.iterdir():
            if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                image_files.append(file.name)
        
        if not image_files:
            return {"message": "No images to export", "exported": []}
        
        # Process and export each image
        for filename in sorted(image_files):
            image_path = INPUT_FOLDER / filename
            
            # Determine parameters for this image
            if filename in image_overrides:
                override = image_overrides[filename]
                use_min_gray = override.get("min_gray", global_min_gray)
                use_max_gray = override.get("max_gray", global_max_gray)
            else:
                use_min_gray = global_min_gray
                use_max_gray = global_max_gray
            
            # Process the image
            processed_img = process_image(str(image_path), use_min_gray, use_max_gray)
            
            # Generate output filename
            output_filename = f"nebula_{counter:03d}.png"
            output_path = OUTPUT_FOLDER / output_filename
            
            # Save the processed image
            save_processed_image(processed_img, str(output_path))
            exported_files.append(output_filename)
            
            counter += 1
        
        return {
            "message": f"Exported {len(exported_files)} images",
            "exported": exported_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

