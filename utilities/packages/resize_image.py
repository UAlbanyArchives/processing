import os
import shutil
from PIL import Image

def process_image_for_pdf(image_path, base_tmp_dir="tmp", max_size=1500, quality=85):
    """
    Processes an image (PNG or JPG) for inclusion in a PDF:
    - Resizes to max_size while maintaining aspect ratio.
    - Converts PNG to compressed JPG.
    - Saves both the temp JPG and a corresponding single-page temp PDF in tmp_dir.

    Returns:
        (temp_jpg_path, temp_pdf_path, tmp_dir)
    """
    # Create a unique temp directory inside base_tmp_dir for processed images
    tmp_dir = os.path.join(os.path.dirname(image_path), base_tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # Determine new file paths
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    temp_jpg_path = os.path.join(tmp_dir, base_name + ".jpg")
    temp_pdf_path = os.path.join(tmp_dir, base_name + ".pdf")

    # Open and process image
    image = Image.open(image_path).convert("RGB")  # Convert to RGB to remove transparency if PNG
    image.thumbnail((max_size, max_size))  # Resize while maintaining aspect ratio

    # Save as a compressed JPEG
    image.save(temp_jpg_path, "JPEG", quality=quality)

    # Convert to single-page PDF
    image.save(temp_pdf_path, "PDF")

    return temp_jpg_path, temp_pdf_path, tmp_dir  # Return paths to temp files and directory
