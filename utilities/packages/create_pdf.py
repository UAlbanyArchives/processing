import os
import shutil
from PIL import Image
from pypdf import PdfWriter

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

def create_pdf(object_path, file_list = None):
    pdf_path = os.path.join(object_path, "pdf")
    if not os.path.isdir(pdf_path):
        os.mkdir(pdf_path)
    pdf_file = PdfWriter()
    temp_dirs = set()
    if not file_list:
    	file_list = []
    	img_priorities = ("png", "jpg", "jpeg", "tif")
    	for priority in img_priorities:
    		priority_path = os.path.join(object_path, priority)
    		if os.path.isdir(priority_path) and len(os.listdir(priority_path)) > 0:
    			for priority_file in os.listdir(priority_path):
    				if priority_file.endswith(priority.lower()):
    					file_list.append(os.path.join(priority_path, priority_file))

    for image_file in file_list:
        image_path = os.path.join(object_path, image_file)

        # Process image → returns temp JPG, temp PDF, and temp dir
        _, temp_pdf_path, tmp_dir = process_image_for_pdf(image_path)
        temp_dirs.add(tmp_dir)  # Track temp directory

        # Append temp PDF to final output
        pdf_file.append(temp_pdf_path)

    # Save the final combined PDF
    final_pdf_path = os.path.join(pdf_path, "binder.pdf")
    pdf_file.write(final_pdf_path)
    pdf_file.close()

    # Cleanup: Delete all temp directories
    for tmp_dir in temp_dirs:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"PDF successfully created: {final_pdf_path}")