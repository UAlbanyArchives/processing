import os
import shutil
import img2pdf
import argparse
from datetime import datetime
from subprocess import run, PIPE
from pathlib import PureWindowsPath, PurePosixPath

# Base processing directory
PROCESSING_DIR = "/backlog"

# Commands vary by OS
if os.name == 'nt':
    IMAGEMAGICK_CMD = "magick"
    PDF_MERGE_CMD = ["pdftk"]
else:
    IMAGEMAGICK_CMD = "convert"
    PDF_MERGE_CMD = ["pdfunite"]

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print("Running:", " ".join(cmd))
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result

def extract_from_pdf(filepath, outprefix, fmt):
    """Convert PDF pages to images using pdftoppm."""
    cmd = ["pdftoppm", filepath, outprefix]
    if fmt == "jpg":
        cmd.append("-jpeg")
    elif fmt == "png":
        cmd.append("-png")
    else:
        raise ValueError(f"Unsupported output format {fmt}")
    run_command(cmd)

def convert_images_to_pdf(input_files, output_pdf):
    """Convert image files to a single PDF."""
    print(f"Converting {len(input_files)} images to {output_pdf}")
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert(input_files))

def convert_image(infile, outfile, resize=None, density=None, monochrome=False):
    """Convert a single image to another format."""
    cmd = [IMAGEMAGICK_CMD, infile]
    if resize:
        cmd += ["-resize", resize]
    if density:
        cmd += ["-density", str(density)]
    if monochrome:
        cmd.append("-monochrome")
    cmd.append(outfile)
    run_command(cmd)

def convert_office_to_pdf(infile, outdir):
    """Convert Office docs to PDF using LibreOffice in headless mode."""
    cmd = [
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", outdir, infile
    ]
    run_command(cmd)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("package", help="Package ID (e.g. ua950.012_Xf5xzeim7n4yE6tjKKHqLM).")
    parser.add_argument("-i", "--input", required=True, help="Input format (tiff, jpg, png, pdf, docx, etc).")
    parser.add_argument("-o", "--output", required=True, help="Output format (jpg, png, pdf).")
    parser.add_argument("-p", "--path", help="Subpath relative to masters directory.", default=None)
    parser.add_argument("-r", "--resize", help="Resize max pixels, e.g. '1000x1000'.")
    parser.add_argument("-d", "--density", help="Set resolution, e.g. '300'.")
    parser.add_argument("-bw", "--monochrome", help="Convert to monochrome", action="store_true")
    return parser.parse_args()

def main():
    args = parse_args()

    # Normalize package paths
    if "_" in args.package:
        ID = args.package.split("_")[0]
    elif "-" in args.package:
        ID = args.package.split("-")[0]
    else:
        raise ValueError(f"Invalid package name {args.package}")

    package = os.path.join(PROCESSING_DIR, ID, args.package)
    masters = os.path.join(package, "masters")
    derivatives = os.path.join(package, "derivatives")
    metadata = os.path.join(package, "metadata")

    for path in [package, masters, derivatives, metadata]:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Invalid package: {args.package}")

    # Handle optional subpath
    if args.path:
        if "\\" in args.path:
            winPath = PureWindowsPath(args.path)
            masters = str(PurePosixPath(masters, *winPath.parts))
        else:
            masters = os.path.join(masters, os.path.normpath(args.path))
        if not os.path.isdir(masters):
            print ("Directory not found.")
            if os.path.isfile(masters):
                print ("Path takes a folder not individual files.")
            raise FileNotFoundError(f"Invalid subpath {args.path}")

    input_exts = [f".{args.input.lower()}"]
    if args.input.lower() in ("tif", "tiff"):
        input_exts = [".tif", ".tiff"]
    if args.input.lower() in ("jpg", "jpeg"):
        input_exts = [".jpg", ".jpeg"]

    # Conversion logic
    if args.output.lower() == "pdf":
        # Images -> PDF
        for root, _, files in os.walk(masters):
            imgs = [os.path.join(root, f) for f in sorted(files) if os.path.splitext(f)[1].lower() in input_exts]
            if imgs:
                rel_root = os.path.relpath(root, masters)
                out_dir = os.path.join(derivatives, rel_root)
                os.makedirs(out_dir, exist_ok=True)
                out_pdf = os.path.join(out_dir, os.path.basename(root) + ".pdf")
                convert_images_to_pdf(imgs, out_pdf)
    else:
        # PDF or images -> images
        for root, _, files in os.walk(masters):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in input_exts:
                    continue

                infile = os.path.join(root, file)
                rel_root = os.path.relpath(root, masters)
                out_dir = os.path.join(derivatives, rel_root)
                os.makedirs(out_dir, exist_ok=True)

                base_name = os.path.splitext(file)[0]
                # for PDF/Office, create a subfolder with the filename
                if args.input.lower() in ("pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv"):
                    doc_out_dir = os.path.join(out_dir, base_name)
                    os.makedirs(doc_out_dir, exist_ok=True)
                    outprefix = os.path.join(doc_out_dir, base_name)
                else:
                    doc_out_dir = out_dir
                    outprefix = os.path.join(doc_out_dir, base_name)

                if args.input.lower() == "pdf":
                    extract_from_pdf(infile, outprefix, args.output.lower())
                elif args.input.lower() in ("doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv"):
                    tmp_pdf_dir = os.path.join(package, "tmp_pdf")
                    os.makedirs(tmp_pdf_dir, exist_ok=True)
                    convert_office_to_pdf(infile, tmp_pdf_dir)
                    tmp_pdf = os.path.join(tmp_pdf_dir, f"{base_name}.pdf")
                    extract_from_pdf(tmp_pdf, outprefix, args.output.lower())
                    try:
                        shutil.rmtree(tmp_pdf_dir)
                        print(f"Temporary directory {tmp_pdf_dir} removed.")
                    except Exception as e:
                        print(f"Warning: could not remove temporary directory {tmp_pdf_dir}: {e}")
                else:
                    out_file = f"{outprefix}.{args.output}"
                    convert_image(infile, out_file, args.resize, args.density, args.monochrome)

    print("Complete!")
    print(f"Finished at {datetime.now()}")

if __name__ == "__main__":
    main()
