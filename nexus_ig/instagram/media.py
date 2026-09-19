"""Instagram Media formatting & download helpers."""
import os
from PIL import Image

def ensure_media_dir(path: str = "data/media"):
    os.makedirs(path, exist_ok=True)

def prepare_dm_image(source_path: str, output_path: str = "data/media/dm_ready.jpg") -> str:
    """Format any image (PNG, WEBP, JPG) into a compliant Instagram DM JPEG format.
    
    Instagram DM photo upload requires:
    - RGB color space (no RGBA alpha channels)
    - Standard JPEG encoding
    - Dimensions within 1080x1350 resolution bounds
    """
    ensure_media_dir()
    try:
        with Image.open(source_path) as img:
            # Convert RGBA / P palette images to RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if dimensions exceed Instagram DM maximum 1080x1350
            max_w, max_h = 1080, 1350
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            img.save(output_path, "JPEG", quality=90)
            return output_path
    except Exception as exc:
        print(f"Image formatting warning: {exc}")
        return source_path
