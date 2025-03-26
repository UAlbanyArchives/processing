import os
import yaml
import uuid
import shutil
import iiiflow
import argparse

from zoneinfo import ZoneInfo
import asnake.logging as logging
from asnake.client import ASnakeClient
from datetime import datetime, timezone
from pathlib import PureWindowsPath, PurePosixPath

def main():
    parser = argparse.ArgumentParser(description="Process digital object upload arguments.")

    parser.add_argument("--packageID", required=True, help="The folder name of the SIP, e.g., apap301_h4fOLPL48CuxFPLpYxTmkL or ua950.009_qUQos7GYhzmB3uL3yjH5uX.")
    parser.add_argument("--input_format", required=True, help="A file extension to look for at the input format.")
    parser.add_argument("--subPath", help="Uploads files in this folder within the /backlog package.")
    parser.add_argument("--refID", required=True, help="A 32-character ArchivesSpace ID, e.g., '855f9efb1fae87fa3b6ef8c8a6e0a28d'.")
    parser.add_argument("--PDF", required=True, help="Option to create a PDF alternative rendering.")
    parser.add_argument("--resource_type", required=True, choices=[
        "Document", "Audio", "Bound Volume", "Dataset", "Image", "Map", 
        "Mixed Materials", "Pamphlet", "Periodical", "Slides", "Video", "Other"
    ], help="The type of resource being uploaded.")
    parser.add_argument("--license", required=True, choices=[
        "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "https://creativecommons.org/licenses/by/4.0/",
        "https://creativecommons.org/publicdomain/zero/1.0/", 
        "Unknown"
    ], help="License type for the resource.")
    parser.add_argument("--rights_statement", choices=[
        "", "https://rightsstatements.org/page/InC-EDU/1.0/"
    ], help="Rights statement for the resource.")
    parser.add_argument("--behavior", required=True, choices=[
        "paged",
        "individuals"
    ], help="Paging behavior for the IIIF object.")
    parser.add_argument("--processing", help="Option to create a PDF alternative rendering.")

    args = parser.parse_args()
    processingDir = "/backlog"

    print("Uploading Digital Object with the following entries:")
    print(f"  Package ID: {args.packageID}")
    print(f"  Input format: {args.input_format}")
    print(f"  Sub Path: {args.subPath if args.subPath else 'N/A'}")
    print(f"  ArchivesSpace ref_id: {args.refID}")
    print(f"  PDF: {args.PDF}")
    print(f"  Resource Type: {args.resource_type}")
    print(f"  License: {args.license}")
    print(f"  Rights Statement: {args.rights_statement if args.rights_statement else 'N/A'}")
    print(f"  Behavior: {args.behavior}")
    print(f"  Processing: {args.processing}")

    """
    1. Create SPE_DAO package and write metadata.yml and copy files over
    2. create thumbnail
    3. OCR or transcription
    4. create ptifs
    5. create manifest
    6. Add digital object record to ASpace
    7. Index record in ArcLight
    """

    metadata = {}
    metadata["preservation_package"] = args.packageID
    metadata["resource_type"] = args.resource_type
    metadata["license"] = args.license
    metadata["behavior"] = args.behavior
    if args.rights_statement:
        metadata["rights_statement"] = args.rights_statement
    metadata["date_published"] = datetime.now(ZoneInfo("America/New_York")).isoformat()

    logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
    client = ASnakeClient()

    ref = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + args.refID).json()
    item = client.get(ref["archival_objects"][0]["ref"]).json()

    resourceURI = item["resource"]["ref"]
    resource = client.get(resourceURI).json()

    collection_ID = resource["id_0"]
    if collection_ID != args.packageID.split("_")[0]:
        raise ValueError(f"ERROR: Collection ID in package ID does not match the collection linked to this ArchivesSpace ref_id.")

    manifest_label = item["title"]
    for date in item["dates"]:
        manifest_label = manifest_label + f", {date['expression']}"
    metadata["manifest_label"] = manifest_label

    collection_path = os.path.join("/SPE_DAO", collection_ID)
    object_path = os.path.join(collection_path, args.refID)
    metadata_path = os.path.join(object_path, "metadata.yml")

    if not os.path.isdir(collection_path):
        os.mkdir(collection_path)
    if not os.path.isdir(object_path):
        os.mkdir(object_path)

    with open(metadata_path, "w", encoding="utf-8") as metadata_file:
        yaml.dump(metadata, metadata_file)

    package_path = os.path.join(processingDir, collection_ID, args.packageID)
    masters = os.path.join(package_path, "masters")
    derivatives = os.path.join(package_path, "derivatives")
    metadata = os.path.join(package_path, "metadata")
    dirList = [package_path, masters, derivatives, metadata]
    for path in dirList:
        if not os.path.isdir(path):
            raise Exception("ERROR: " + str(args.packageID) + " is not a valid processing package.")

    if args.subPath:
        if "\\" in args.subPath:
            winPath = PureWindowsPath(args.subPath)
            masters = str(PurePosixPath(masters, *winPath.parts))
            derivatives = str(PurePosixPath(derivatives, *winPath.parts))
        else:
            masters = os.path.join(masters, os.path.normpath(args.subPath))
            derivatives = os.path.join(derivatives, os.path.normpath(args.subPath))

    masters_count = 0
    derivatives_count = 0
    file_list = []
    for input_file in os.listdir(masters):
        input_file_path = os.path.join(masters, input_file)
        if os.path.isfile(input_file_path) and input_file.endswith(f".{args.input_format.lower()}"):
            masters_count += 1
            file_list.append(input_file_path)
    if masters_count == 0:
        for input_file in os.listdir(derivatives):
            input_file_path = os.path.join(derivatives, input_file)
            if os.path.isfile(input_file_path) and input_file.endswith(f".{args.input_format.lower()}"):
                derivatives_count += 1
                file_list.append(input_file_path)

    if masters_count == 0 and derivatives_count == 0:
        raise FileNotFoundError(f"ERROR: no {args.input_format.lower()} files found in package {args.packageID} masters or derivatives.")

    # Move access files to SPE_DAO
    format_path = os.path.join(object_path, args.input_format.lower())
    if not os.path.isdir(format_path):
        os.mkdir(format_path)
    for image_file in file_list:
        shutil.copy(image_file, format_path)

    # make thumbnail
    print ("Creating thumbnail")
    iiiflow.make_thumbnail(collection_ID, args.refID)

    pdf_formats = ["png", "jpg"]
    if args.PDF.lower() == "true" and args.input_format.lower() in pdf_formats:
        print ("Creating alternative PDF...")
        iiiflow.create_pdf(collection_ID, args.refID)

    # Create pyramidal tifs
    print ("Creating pyramidal tifs (.ptifs)...")
    iiiflow.create_ptif(collection_ID, args.refID)

    # OCR
    print ("Recognizing text...")
    iiiflow.create_hocr(collection_ID, args.refID)

    # Create manifest
    print ("Generating IIIF manifest...")
    iiiflow.create_manifest(collection_ID, args.refID)

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

    #item["instances"].append(dao_link)
    #update_item = client.post(item["uri"], json=item)

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
    #print (f"Updated archival object record --> {update_item.status_code}")

    print ("Indexing record in ArcLight... (skipping)")
    
    print ("Success!")
    print (f"Check out digital object at:")
    #print (f"https://media.archives.albany.edu/test.html?collection={collection_ID}&id={args.refID}")
    print (f"https://media.archives.albany.edu/test.html?manifest={dao_url}")

if __name__ == "__main__":
    main()
