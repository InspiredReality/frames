"""Image processing utilities for walls and pictures."""
import os
from PIL import Image

THUMBNAIL_SIZE = (400, 400)
MAX_IMAGE_SIZE = (2048, 2048)


def process_wall_image(image_path, output_folder):
    """
    Process a wall image and create a thumbnail.

    Args:
        image_path: Path to the original image
        output_folder: Folder to save processed images

    Returns:
        Path to the thumbnail image
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize if too large
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                img.save(image_path, quality=90)

            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            thumb_filename = f"{name}_thumb{ext}"
            thumb_path = os.path.join(output_folder, thumb_filename)
            thumb.save(thumb_path, quality=85)

            return thumb_path

    except Exception as e:
        print(f"Error processing wall image: {e}")
        return None


def process_picture_image(image_path, output_folder):
    """
    Process a picture image, extract dimensions, and create a thumbnail.

    Args:
        image_path: Path to the original image
        output_folder: Folder to save processed images

    Returns:
        Dictionary with width, height, and thumbnail_path
    """
    result = {
        'width': None,
        'height': None,
        'thumbnail_path': None
    }

    try:
        with Image.open(image_path) as img:
            # Store original dimensions
            result['width'] = img.size[0]
            result['height'] = img.size[1]

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                rgb_img = img.convert('RGB')
            else:
                rgb_img = img

            # Resize if too large (but keep original dimensions recorded)
            if rgb_img.size[0] > MAX_IMAGE_SIZE[0] or rgb_img.size[1] > MAX_IMAGE_SIZE[1]:
                rgb_img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                rgb_img.save(image_path, quality=90)

            # Create thumbnail
            thumb = rgb_img.copy()
            thumb.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            thumb_filename = f"{name}_thumb{ext}"
            thumb_path = os.path.join(output_folder, thumb_filename)
            thumb.save(thumb_path, quality=85)

            result['thumbnail_path'] = thumb_path

    except Exception as e:
        print(f"Error processing picture image: {e}")

    return result


def extract_dominant_colors(image_path, num_colors=5):
    """
    Extract dominant colors from an image for styling suggestions.

    Args:
        image_path: Path to the image
        num_colors: Number of dominant colors to extract

    Returns:
        List of RGB tuples
    """
    try:
        with Image.open(image_path) as img:
            # Resize for faster processing
            img = img.copy()
            img.thumbnail((150, 150))

            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Get colors
            colors = img.getcolors(maxcolors=10000)
            if colors:
                # Sort by frequency
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                return [color[1] for color in sorted_colors[:num_colors]]

    except Exception as e:
        print(f"Error extracting colors: {e}")

    return []
