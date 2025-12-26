"""
Script to clean artifacts from images in a specified folder.

The artifact is:
- Gray colored (128, 128, 128) with +/-5 threshold
- Positioned in the right 3rd of the image
- Around 64px in size (50-70px range)
"""
import argparse
from pathlib import Path
from PIL import Image


def is_gray_color(r, g, b, target=(128, 128, 128), threshold=5):
    """
    Check if a pixel matches the target gray color within threshold.
    Uses two checks:
    1. All channels are close to target (within threshold)
    2. All channels are similar to each other (is actually gray)
    
    Args:
        r, g, b: RGB values
        target: Target RGB color tuple
        threshold: Color difference threshold
    
    Returns:
        True if pixel matches the gray color
    """
    # Check if all channels are close to target
    close_to_target = (abs(r - target[0]) <= threshold and 
                       abs(g - target[1]) <= threshold and 
                       abs(b - target[2]) <= threshold)
    
    # Also check if it's actually gray (all channels similar to each other)
    # This handles cases where the color might be slightly off but still gray
    is_gray = (abs(r - g) <= threshold and 
               abs(g - b) <= threshold and 
               abs(r - b) <= threshold)
    
    # Check if average is close to target gray value
    avg = (r + g + b) // 3
    avg_close = abs(avg - target[0]) <= threshold
    
    return close_to_target or (is_gray and avg_close)


def find_bounding_boxes(image, target_color=(128, 128, 128), threshold=5):
    """
    Find all bounding boxes containing pixels matching the target gray color.
    
    Args:
        image: PIL Image object
        target_color: Target RGB color tuple
        threshold: Color difference threshold
    
    Returns:
        List of bounding boxes as (x_min, y_min, x_max, y_max)
    """
    width, height = image.size
    pixels = image.load()
    
    # Create a mask of matching pixels
    mask = [[False for _ in range(width)] for _ in range(height)]
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            if is_gray_color(r, g, b, target_color, threshold):
                mask[y][x] = True
    
    # Find connected components and their bounding boxes
    boxes = []
    visited = [[False for _ in range(width)] for _ in range(height)]
    
    def flood_fill(start_x, start_y):
        """Flood fill to find connected component and its bounding box"""
        if visited[start_y][start_x] or not mask[start_y][start_x]:
            return None
        
        stack = [(start_x, start_y)]
        x_min, y_min = start_x, start_y
        x_max, y_max = start_x, start_y
        
        while stack:
            x, y = stack.pop()
            if visited[y][x] or not mask[y][x]:
                continue
            
            visited[y][x] = True
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)
            
            # Check neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if not visited[ny][nx] and mask[ny][nx]:
                        stack.append((nx, ny))
        
        return (x_min, y_min, x_max + 1, y_max + 1)
    
    # Find all connected components
    for y in range(height):
        for x in range(width):
            if mask[y][x] and not visited[y][x]:
                box = flood_fill(x, y)
                if box:
                    boxes.append(box)
    
    return boxes


def filter_boxes_by_size_and_position(boxes, width, height, min_size=50, max_size=70, debug=False):
    """
    Filter bounding boxes by size and position (right 3rd of image).
    
    Args:
        boxes: List of bounding boxes
        width: Image width
        height: Image height
        min_size: Minimum box dimension
        max_size: Maximum box dimension
        debug: If True, print debug information
    
    Returns:
        Filtered list of boxes
    """
    right_third_start = width * 2 // 3
    filtered = []
    
    if debug:
        print(f"  Image size: {width}x{height}, Right third starts at x={right_third_start}")
        print(f"  Found {len(boxes)} gray boxes total")
    
    for x_min, y_min, x_max, y_max in boxes:
        box_width = x_max - x_min
        box_height = y_max - y_min
        
        # Check if box overlaps with right third of image (more flexible)
        box_center_x = (x_min + x_max) // 2
        overlaps_right_third = x_max >= right_third_start or box_center_x >= right_third_start
        
        # Check size constraint (allow some flexibility - at least one dimension should be in range)
        size_ok = ((min_size <= box_width <= max_size and min_size <= box_height <= max_size) or
                   (min_size * 0.8 <= box_width <= max_size * 1.2 and 
                    min_size * 0.8 <= box_height <= max_size * 1.2))
        
        if debug:
            print(f"    Box: ({x_min}, {y_min}, {x_max}, {y_max}) "
                  f"size={box_width}x{box_height}, "
                  f"center_x={box_center_x}, "
                  f"overlaps_right={overlaps_right_third}, "
                  f"size_ok={size_ok}")
        
        if size_ok and overlaps_right_third:
            filtered.append((x_min, y_min, x_max, y_max))
    
    if debug:
        print(f"  After filtering: {len(filtered)} boxes match criteria")
    
    return filtered


def select_rightmost_bottom_box(boxes):
    """
    Select the box that is most right and bottom.
    
    Args:
        boxes: List of bounding boxes
    
    Returns:
        Selected box or None
    """
    if not boxes:
        return None
    
    # Sort by x_max (rightmost) first, then by y_max (bottommost)
    return max(boxes, key=lambda box: (box[2], box[3]))


def calculate_average_color_around_box(image, box, padding=10):
    """
    Calculate average color of pixels around the bounding box.
    
    Args:
        image: PIL Image object
        box: Bounding box (x_min, y_min, x_max, y_max)
        padding: Padding around box to sample from
    
    Returns:
        Average RGB color tuple
    """
    width, height = image.size
    x_min, y_min, x_max, y_max = box
    pixels = image.load()
    
    # Define sampling region (around the box with padding)
    sample_x_min = max(0, x_min - padding)
    sample_y_min = max(0, y_min - padding)
    sample_x_max = min(width, x_max + padding)
    sample_y_max = min(height, y_max + padding)
    
    # Collect pixels from around the box (excluding the box itself)
    r_sum, g_sum, b_sum = 0, 0, 0
    count = 0
    
    for y in range(sample_y_min, sample_y_max):
        for x in range(sample_x_min, sample_x_max):
            # Skip pixels inside the box
            if x_min <= x < x_max and y_min <= y < y_max:
                continue
            
            r, g, b = pixels[x, y]
            r_sum += r
            g_sum += g
            b_sum += b
            count += 1
    
    if count == 0:
        # Fallback: use pixels from the edges of the image
        return (128, 128, 128)
    
    return (int(r_sum / count), int(g_sum / count), int(b_sum / count))


def remove_artifact(image_path, output_path=None, target_color=(128, 128, 128), 
                        threshold=5, min_size=50, max_size=70, expand_box=2, debug=False):
    """
    Remove artifact from an image.
    
    Args:
        image_path: Path to input image
        output_path: Path to save cleaned image (if None, overwrites original)
        target_color: Target gray color RGB tuple
        threshold: Color matching threshold
        min_size: Minimum artifact size
        max_size: Maximum artifact size
        expand_box: Number of pixels to expand the bounding box (default: 2)
        debug: If True, print debug information
    
    Returns:
        True if artifact was found and removed, False otherwise
    """
    # Open image
    img = Image.open(image_path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    
    if debug:
        print(f"\nProcessing {image_path} ({width}x{height})")
    
    # Find all bounding boxes with gray color
    boxes = find_bounding_boxes(img, target_color, threshold)
    
    if not boxes:
        print(f"No gray boxes found in {image_path}")
        if debug:
            # Try to find what gray colors are actually in the image
            pixels = img.load()
            gray_samples = []
            # Sample right third of image
            right_third_start = width * 2 // 3
            for y in range(height - 100, height, 10):
                for x in range(right_third_start, width, 10):
                    r, g, b = pixels[x, y]
                    if abs(r - g) < 10 and abs(g - b) < 10:  # Approximately gray
                        gray_samples.append((r, g, b))
            if gray_samples:
                print(f"  Found gray-like colors in right area: {set(gray_samples[:10])}")
        return False
    
    # Filter boxes by size and position
    filtered_boxes = filter_boxes_by_size_and_position(boxes, width, height, min_size, max_size, debug)
    
    if not filtered_boxes:
        print(f"No matching boxes found in {image_path}")
        if debug:
            print(f"  All {len(boxes)} boxes were filtered out. Showing first few:")
            for i, (x_min, y_min, x_max, y_max) in enumerate(boxes[:5]):
                box_width = x_max - x_min
                box_height = y_max - y_min
                print(f"    Box {i+1}: ({x_min}, {y_min}, {x_max}, {y_max}) "
                      f"size={box_width}x{box_height}")
        return False
    
    # Select the rightmost and bottommost box
    selected_box = select_rightmost_bottom_box(filtered_boxes)
    
    if not selected_box:
        print(f"No suitable box selected in {image_path}")
        return False
    
    print(f"Found artifact at {selected_box} in {image_path}")
    
    # Expand the bounding box to capture edge pixels
    x_min, y_min, x_max, y_max = selected_box
    x_min = max(0, x_min - expand_box)
    y_min = max(0, y_min - expand_box)
    x_max = min(width, x_max + expand_box)
    y_max = min(height, y_max + expand_box)
    expanded_box = (x_min, y_min, x_max, y_max)
    
    if debug:
        print(f"  Expanded box from {selected_box} to {expanded_box}")
    
    # Calculate average color around the original box (before expansion)
    avg_color = calculate_average_color_around_box(img, selected_box)
    
    # Replace pixels in the expanded box with average color
    pixels = img.load()
    
    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            pixels[x, y] = avg_color
    
    # Save the cleaned image
    if output_path is None:
        output_path = image_path
    
    img.save(output_path, 'PNG')
    print(f"Cleaned image saved to {output_path}")
    return True


def clean_folder(folder_path, output_folder=None, target_color=(128, 128, 128), 
                 threshold=5, min_size=50, max_size=70, expand_box=2, debug=False):
    """
    Clean all images in a folder from artifacts.
    
    Args:
        folder_path: Path to folder containing images
        output_folder: Path to output folder (if None, overwrites originals)
        target_color: Target gray color RGB tuple
        threshold: Color matching threshold
        min_size: Minimum artifact size
        max_size: Maximum artifact size
        expand_box: Number of pixels to expand the bounding box (default: 2)
        debug: If True, print debug information
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: Folder {folder_path} does not exist")
        return
    
    # Find all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
    image_files = [f for f in folder.iterdir() 
                   if f.is_file() and f.suffix in image_extensions]
    
    if not image_files:
        print(f"No image files found in {folder_path}")
        return
    
    print(f"Found {len(image_files)} image(s) to process")
    
    # Create output folder if specified
    if output_folder:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each image
    cleaned_count = 0
    for image_file in image_files:
        try:
            if output_folder:
                output_file = Path(output_folder) / image_file.name
            else:
                output_file = None
            
            if remove_artifact(str(image_file), str(output_file) if output_file else None,
                                  target_color, threshold, min_size, max_size, expand_box, debug):
                cleaned_count += 1
        except Exception as e:
            print(f"Error processing {image_file}: {e}")
    
    print(f"\nProcessing complete. Cleaned {cleaned_count} out of {len(image_files)} image(s)")


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Remove artifacts from images in a folder'
    )
    parser.add_argument(
        'folder',
        type=str,
        help='Path to folder containing images to clean'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output folder (if not specified, overwrites original images)'
    )
    parser.add_argument(
        '-t', '--threshold',
        type=int,
        default=5,
        help='Color matching threshold (default: 5)'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=50,
        help='Minimum artifact size in pixels (default: 50)'
    )
    parser.add_argument(
        '--max-size',
        type=int,
        default=70,
        help='Maximum artifact size in pixels (default: 70)'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug output'
    )
    parser.add_argument(
        '--expand-box',
        type=int,
        default=2,
        help='Number of pixels to expand the bounding box (default: 2)'
    )
    
    args = parser.parse_args()
    
    clean_folder(
        args.folder,
        args.output,
        threshold=args.threshold,
        min_size=args.min_size,
        max_size=args.max_size,
        expand_box=args.expand_box,
        debug=args.debug
    )


if __name__ == '__main__':
    main()

