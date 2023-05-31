import os
import argparse
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from datetime import datetime
from subprocess import Popen, PIPE

processingDir = "/backlog"

parser = argparse.ArgumentParser()
parser.add_argument("package", help="ID for package you are processing, i.e. 'ua950.012_Xf5xzeim7n4yE6tjKKHqLM'.")
parser.add_argument("-p", "--path", help="Subpath, relative to derivatives directory which will only convert files there.", default=None)

args = parser.parse_args()

if "_" in args.package:
    ID = args.package.split("_")[0]
elif "-" in args.package:
    ID = args.package.split("-")[0]
else:
    raise Exception("ERROR: " + str(args.package) + " is not a valid processing package.")
    
package = os.path.join(processingDir, ID, args.package)
masters = os.path.join(package, "masters")
derivatives = os.path.join(package, "derivatives")
metadata = os.path.join(package, "metadata")

def process(cmd):
    #p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if len(stdout) > 0:
        print (stdout.decode())
    if len(stderr) > 0:
        print (stderr.decode())
    return p.returncode


if args.path:
    ocrPath = os.path.join(derivatives, os.path.normpath(args.path))
    if not os.path.isdir(derivatives):
        raise Exception("ERROR: subpath " + args.path + " relative to derivatives is not a valid path.")
else:
    ocrPath = derivatives

# Check if there are any files
fileTotal = 0
for root, dirs, files in os.walk(ocrPath):
    for file in files:
        if file.lower().endswith(".pdf"):
            fileTotal += 1
if fileTotal == 0:
    raise ValueError(f"Error: No PDF files found in derivatives folder in package {args.package}")

# Set up temp folder to extract images to
convertDir = os.path.join(package, "converting-ocr")
if not os.path.isdir(convertDir):
    os.mkdir(convertDir)

fileCount = 0
for root, dirs, files in os.walk(ocrPath):
    for file in files:
        if file.lower().endswith(".pdf"):
            fileCount += 1
            filepath = os.path.join(root, file)
            print (f"Processing {file} (file {fileCount} of {fileTotal})...")

            # convert to images
            pageOrder = []
            pdf_reader = PdfReader(filepath)
            page_count = 0
            page_total = len(pdf_reader.pages)
            for page in pdf_reader.pages:
                page_count += 1
                if len(page.images) != 1:
                    raise ValueError(f"ERROR: During OCR prep, PDF page number {page_count} has multiple images.")
                page_rotation = page.get('/Rotate')
                for image in page.images:
                    ext = os.path.splitext(image.name)[1]
                    image_path = os.path.join(convertDir, f"{os.path.splitext(file)[0]}-{page_count}{ext}")
                    if os.path.isfile(image_path):
                        raise ValueError(f"ERROR: In extracting images for OCR, file already exists: {image_path}.")
                    with open(image_path, "wb") as fp:
                        fp.write(image.data)
                    #address image rotation
                    if page_rotation:
                        print ("\tFixing image rotation...")
                        img = Image.open(image_path)
                        img_rotate = img.rotate(-abs(page_rotation), expand=1)
                        img_rotate.save(image_path)

                    page_file = os.path.join(convertDir, f"{os.path.splitext(file)[0]}-{page_count}")
                    pageOrder.append(page_file + ".pdf")
                    cmd = ["tesseract", image_path, page_file, "pdf"]
                    print (f"\t--> reading page {page_count} of {page_total}, {image_path}...")
                    resp = process(cmd)
                    if resp != 0:
                        raise ValueError(f'Error processing file {file}')
                    # delete temporary image
                    os.remove(image_path)

            # Merge back to single PDF
            print (f"Merging back to {file}...")
            os.rename(filepath, os.path.join(root, "." + file))
            merger = PdfWriter()
            for pdf_page in pageOrder:
                merger.append(pdf_page)
            merger.write(filepath)
            merger.close()
            if os.path.isfile(filepath) and os.stat(filepath).st_size:
                os.remove(os.path.join(root, "." + file))
                # delete temporary pdf
                for pdf_page in pageOrder:
                    os.remove(pdf_page) 

print ("Cleaning temporary directory...")
if len(os.listdir(convertDir)) == 0:
    os.rmdir(convertDir)
else:
    raise ValueError(f"ERROR: temporary directory {convertDir} is not empty, cannot cleanup.")


print ("Complete!")
print (f"Finished at {datetime.now()}")
