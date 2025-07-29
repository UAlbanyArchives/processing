import os
import re
import sys
import yaml
import shutil
import iiiflow
import argparse
from openpyxl import load_workbook
from datetime import datetime, timezone
from pathlib import PureWindowsPath, PurePosixPath

processingDir = "/backlog"
SPE_DAO = "/SPE_DAO"

PREFIXES = ["apap", "ger", "mss", "ua"]
def validate_package_id(col_id: str) -> bool:
    pattern = r'^(apap\d{3}|ger\d{3}|mss\d{3}|ua\d{3}(?:\.\d{3})?)$'
    return bool(re.match(pattern, col_id))

# Validations
ALLOWED_INPUT_FORMATS = {"jpg", "png"}
ALLOWED_RESOURCE_TYPES = {
    "Audio", "Bound Volume", "Dataset", "Document", "Image", "Map",
    "Mixed Materials", "Pamphlet", "Periodical", "Slides", "Video", "Other"
}
ALLOWED_LICENSES = {"CC BY", "CC BY-NC", "Unknown"}
ALLOWED_BEHAVIORS = {"paged", "individuals", "continuous"}

# License and rights lookup
LICENSE_LOOKUP = {
    "CC BY": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-NC-SA": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
}
RIGHTS_FALLBACK = "https://rightsstatements.org/page/InC-EDU/1.0/"

parser = argparse.ArgumentParser()
parser.add_argument("package", help="ID for package you are processing, e.g. 'ua950.012_Xf5xzeim7n4yE6tjKKHqLM'")
parser.add_argument("-s", "--sheet", required=True,
                    help="Path (relative to the package's metadata folder) of the bulk upload spreadsheet. "
                         "Example: sheet.xlsx or sub/folder/sheet.xlsx")

args = parser.parse_args()

if not os.path.isdir(SPE_DAO):
    raise FileNotFoundError("Error: Missing /SPE_DAO mount.")

# Extract base ID from package name
if "_" in args.package:
    ID = args.package.split("_")[0]
elif "-" in args.package:
    ID = args.package.split("-")[0]
else:
    raise Exception(f"Error: {args.package} is not a valid processing package.")

if not validate_col_id(ID):
    raise ValueError(f"Invalid collection ID: {ID}")

# Base metadata path
metadata_path = os.path.join(processingDir, ID, args.package, "metadata")
if not os.path.isdir(metadata_path):
    raise FileNotFoundError(f"Error: missing path {metadata_path}")
derivatives_path = os.path.join(processingDir, ID, args.package, "derivatives")
masters_path = os.path.join(processingDir, ID, args.package, "masters")

# Normalize sheet path (handle Windows-style paths too)
sheet_arg = args.sheet
if "\\" in sheet_arg:
    win_path = PureWindowsPath(sheet_arg)
    sheet_rel = PurePosixPath(*win_path.parts)
else:
    sheet_rel = os.path.normpath(sheet_arg)

sheet_path = os.path.join(metadata_path, sheet_rel)

if not os.path.isfile(sheet_path):
    raise FileNotFoundError(f"Error: sheet file not found at {sheet_path}")

print(f"Reading bulk upload sheet {sheet_path}...")

wb = load_workbook(sheet_path, data_only=True)
ws = wb.active

# Get headers from row 6
headers = [str(cell.value).strip() if cell.value else "" for cell in ws[6]]

required_cols = [
    "ArchivesSpace ID", "Title", "File Paths",
    "Input Format", "Resource Type", "Behavior",
    "License/Rights"
]

for col in required_cols:
    if col not in headers:
        raise ValueError(f"Missing required column: {col}")

col_index = {col: headers.index(col) for col in required_cols}

errors = []
records = []

for row_num, row in enumerate(ws.iter_rows(min_row=7, values_only=True), start=7):
    if all(v is None for v in row):
        continue

    title = str(row[col_index["Title"]]).strip() if row[col_index["Title"]] else ""
    aspace_id = str(row[col_index["ArchivesSpace ID"]]).strip() if row[col_index["ArchivesSpace ID"]] else ""

    if not (title and aspace_id):
        continue  # skip incomplete rows

    # Handle File Paths
    file_paths_raw = row[col_index["File Paths"]]
    file_paths = []
    if file_paths_raw:
        file_paths = [fp.strip() for fp in str(file_paths_raw).split(";") if fp.strip()]
        for fp in file_paths:
            full_path = os.path.normpath(os.path.join(derivatives_path, fp))
            if not os.path.isdir(full_path):
                full_path = os.path.normpath(os.path.join(masters_path, fp))
                if not os.path.isdir(full_path):
                    errors.append(f"Missing path: {full_path} (row {row_num})")

    # Check if SPE_DAO path already exists
    object_path = os.path.join(SPE_DAO, ID, aspace_id)
    if os.path.isdir(aspace_id):
        errors.append(f"SPE_DAO object path '{object_path}' already exists for row {row_num}")

    # Validate controlled vocab fields
    input_fmt = str(row[col_index["Input Format"]]).strip() if row[col_index["Input Format"]] else ""
    if input_fmt and input_fmt not in ALLOWED_INPUT_FORMATS:
        errors.append(f"Invalid Input Format '{input_fmt}' in row {row_num}")

    res_type = str(row[col_index["Resource Type"]]).strip() if row[col_index["Resource Type"]] else ""
    if res_type and res_type not in ALLOWED_RESOURCE_TYPES:
        errors.append(f"Invalid Resource Type '{res_type}' in row {row_num}")

    license_val = str(row[col_index["License/Rights"]]).strip() if row[col_index["License/Rights"]] else ""
    if license_val and license_val not in ALLOWED_LICENSES:
        errors.append(f"Invalid License '{license_val}' in row {row_num}")

    behavior = str(row[col_index["Behavior"]]).strip() if row[col_index["Behavior"]] else ""
    if behavior and behavior not in ALLOWED_BEHAVIORS:
        errors.append(f"Invalid Behavior '{behavior}' in row {row_num}")

    records.append({
        "ArchivesSpace ID": aspace_id,
        "Title": title,
        "File Paths": file_paths,
        "Input Format": input_fmt,
        "Resource Type": res_type,
        "License/Rights": license_val,
        "Behavior": behavior,
    })

if errors:
    print("Validation errors found:")
    for e in errors:
        print(" -", e)
    sys.exit()
else:
    print("All records validated successfully!")

print(f"Parsed {len(records)} valid records.")

# Loop though validated sheet to upload files
for rec in records:
    title = rec["Title"]
    aspace_id = rec["ArchivesSpace ID"]
    file_path = rec["File Paths"]
    original_file = rec["Original file"]
    res_type = rec["Resource Type"]
    license = rec["License/Rights"]
    input_fmt = rec["Input Format"]
    behavior = rec["Behavior"]

    print(f"Processing {title} ({aspace_id})...")

    collectionDir = os.path.join (SPE_DAO, ID)
    if not os.path.isdir(collectionDir):
        os.mkdir(collectionDir)

    object_path = os.path.join(collectionDir, aspace_id)
    if os.path.isdir(aspace_id):
        raise FileExistsError(f"Error: access path {object_path} already present.")
    os.mkdir(object_path)

    # Build metadata.yml
    metadata = {
        "preservation_package": args.package,
        "resource_type": res_type,
        "behavior": behavior,
        "date_uploaded": datetime.now(timezone.utc).isoformat(),
    }
    if len(original_file) > 0:
        metadata["original_file"] = original_file

    lic = license_val.strip() if license_val else ""
    if lic in LICENSE_LOOKUP:
        metadata["license"] = LICENSE_LOOKUP[lic]
    else:
        # Treat "Unknown" or empty as rights statement fallback
        metadata["rights_statement"] = RIGHTS_FALLBACK

    metadata_path = os.path.join(object_path, "metadata.yml")
    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, sort_keys=False, allow_unicode=True)

    print(f"Created metadata.yml at {metadata_path}")

    format_path = os.path.join(object_path, input_fmt.lower())
    os.mkdir(format_path)
    for file in os.scandir(file_path):
        print (f"Moving {file.path} to {format_path}...")
        shutil.copy2(file.path, format_path)

    # make thumbnail
    print ("Creating thumbnail")
    iiiflow.make_thumbnail(ID, aspace_id)

    pdf_formats = ["png", "jpg"]
    if ".pdf" in original_file.lower():

    elif input_fmt in pdf_formats:
        print ("Creating alternative PDF...")
        iiiflow.create_pdf(collection_ID, args.refID)

    # Create pyramidal tifs
    print ("Creating pyramidal tifs (.ptifs)...")
    iiiflow.create_ptif(ID, args.aspace_id)

    # OCR
    print ("Recognizing text...")
    iiiflow.create_hocr(ID, aspace_id)

    # Index HOCR
    print ("Indexing text for content search...")
    iiiflow.index_hocr_to_solr(ID, aspace_id)

    # Create manifest
    print ("Generating IIIF manifest...")
    iiiflow.create_manifest(ID, aspace_id)

    print ("Adding digital object record to ArchivesSpace...")

    # get url root from iiiflow config
    with open("/root/.iiiflow.yml", "r") as config_file:
        config = yaml.safe_load(config_file)
    manifest_url_root = config.get("manifest_url_root")
    dao_url = f"{manifest_url_root}/{collection_ID}/{args.refID}/manifest.json"

    file_version = {
        "jsonmodel_type": "file_version",
        "publish": True,
        "is_representative": True,
        "file_uri": dao_url,
        "use_statement": "",
        "xlink_actuate_attribute": "none",
        "xlink_show_attribute": "embed",
    }
    dao_uuid = str(uuid.uuid4())
    dao_title = "Online object uploaded typically on user request."

    dao_object = {
        "jsonmodel_type": "digital_object",
        "publish": True,
        "is_representative": True,
        "external_ids": [],
        "subjects": [],
        "linked_events": [],
        "extents": [],
        "dates": [],
        "external_documents": [],
        "rights_statements": [],
        "linked_agents": [],
        "file_versions": [file_version],
        "restrictions": False,
        "notes": [],
        "linked_instances": [],
        "title": dao_title,
        "language": "",
        "digital_object_id": dao_uuid,
    }

    # Upload new digital object
    #new_dao = client.post("repositories/2/digital_objects", json=dao_object)
    #dao_uri = new_dao.json()["uri"]
    dao_uri = "blah"
    print (f"Added digital object record {dao_uri}")

    # Attach new digital object instance to archival object
    dao_link = {
        "jsonmodel_type": "instance",
        "digital_object": {"ref": dao_uri},
        "instance_type": "digital_object",
        "is_representative": False,
    }

    item["instances"].append(dao_link)

    if args.processing and len(args.processing) > 0:
        processing_note = {
            "jsonmodel_type": "note_multipart",
            "type": "processinfo",
            "subnotes": [
                {
                    "jsonmodel_type": "note_text",
                    "content": args.processing,
                    "publish": True
                }
            ],
            "publish": True
        }
        item["notes"].append(processing_note)
        print (f"Added processing note.")

    #update_item = client.post(item["uri"], json=item)
    print (f"Updated archival object record --> {update_item.status_code}")

    #print ("Indexing record in ArcLight... (skipping)")
    
    print ("Success!")
    print (f"Check out digital object at:")
    #print (f"https://media.archives.albany.edu/test.html?collection={collection_ID}&id={args.refID}")
    print (f"https://media.archives.albany.edu?manifest={dao_url}")



