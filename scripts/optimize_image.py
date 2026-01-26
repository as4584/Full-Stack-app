import os
import sys
from PIL import Image

def optimize_image(input_path, output_path, quality=80):
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if it's RGBA and we are saving as JPEG (though we'll use WebP)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            
            # Save as WebP
            img.save(output_path, "WEBP", quality=quality, method=6)
            print(f"Optimized {input_path} -> {output_path} ({os.path.getsize(output_path)} bytes)")
    except Exception as e:
        print(f"Error optimizing {input_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python optimize.py <input> <output>")
        sys.exit(1)
    optimize_image(sys.argv[1], sys.argv[2])
