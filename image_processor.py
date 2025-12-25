"""
Image processor for converting grayscale values to alpha transparency.
"""
from PIL import Image


def rgb_to_gray(r, g, b):
    """
    Convert RGB values to grayscale using luminance formula.
    
    Args:
        r: Red channel (0-255)
        g: Green channel (0-255)
        b: Blue channel (0-255)
    
    Returns:
        Grayscale value (0-255)
    """
    return int(0.299 * r + 0.587 * g + 0.114 * b)


def calculate_alpha(gray_value, min_gray, max_gray):
    """
    Calculate alpha value based on grayscale value and thresholds.
    
    Args:
        gray_value: Grayscale value of the pixel (0-255)
        min_gray: Gray value that maps to alpha=0 (fully transparent)
        max_gray: Gray value that maps to alpha=255 (fully opaque)
    
    Returns:
        Alpha value (0-255)
    """
    if min_gray >= max_gray:
        # Edge case: if min >= max, treat everything as opaque
        return 255 if gray_value >= min_gray else 0
    
    if gray_value <= min_gray:
        return 0  # Fully transparent
    elif gray_value >= max_gray:
        return 255  # Fully opaque
    else:
        # Linear interpolation
        return int(255 * (gray_value - min_gray) / (max_gray - min_gray))


def process_image(image_path, min_gray, max_gray):
    """
    Process an image to add alpha channel based on grayscale values.
    
    Args:
        image_path: Path to the input image file
        min_gray: Gray value that maps to alpha=0 (0-255)
        max_gray: Gray value that maps to alpha=255 (0-255)
    
    Returns:
        PIL Image with RGBA mode
    """
    # Open the image
    img = Image.open(image_path)
    
    # Convert to RGB if needed (in case it's grayscale or has alpha already)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get image dimensions
    width, height = img.size
    
    # Create new image with RGBA mode
    result = Image.new('RGBA', (width, height))
    
    # Process each pixel
    pixels = img.load()
    result_pixels = result.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Calculate grayscale value
            gray = rgb_to_gray(r, g, b)
            
            # Calculate alpha value
            alpha = calculate_alpha(gray, min_gray, max_gray)
            
            # Set RGBA pixel
            result_pixels[x, y] = (r, g, b, alpha)
    
    return result


def save_processed_image(image, output_path):
    """
    Save a processed RGBA image to a file.
    
    Args:
        image: PIL Image with RGBA mode
        output_path: Path where to save the image
    """
    image.save(output_path, 'PNG')

