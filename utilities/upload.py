import os
import sys
import yaml
import json
import uuid
import shutil
import iiiflow
import argparse

from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import asnake.logging as logging
from asnake.client import ASnakeClient
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath, PurePosixPath

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
    2. Create thumbnail
    3. OCR or transcription
    4. Create ptifs
    5. Index HOCR for content search
    6. Create manifest
    7. Add digital object record to ASpace
    8. Index record in ArcLight
    """

    av_formats = ["ogg_mp3", "webm"]
    metadata = {}
    metadata["preservation_package"] = args.packageID
    metadata["resource_type"] = args.resource_type
    metadata["license"] = args.license
    if not args.input_format.lower() in av_formats:
        metadata["behavior"] = args.behavior
    if args.rights_statement:
        metadata["rights_statement"] = args.rights_statement
    metadata["date_uploaded"] = datetime.now(ZoneInfo("America/New_York")).isoformat()

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
    metadata["manifest_label"] = BeautifulSoup(manifest_label, "html.parser").get_text()

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

    subpathIsFile = False
    if args.subPath:
        # Normalize for Windows-style paths
        if "\\" in args.subPath:
            win_path = PureWindowsPath(args.subPath)
            sub_path = Path(*win_path.parts)
        else:
            # Normalize and remove leading slash
            subpath = os.path.normpath(args.subPath).lstrip(os.sep)
            sub_path = Path(subpath)
        # Join with masters and derivatives base paths
        masters_path = Path(masters) / sub_path
        derivatives_path = Path(derivatives) / sub_path
        if masters_path.is_file() or derivatives_path.is_file():
            subpathIsFile = True
        else:
            masters = str(masters_path)
            derivatives = str(derivatives_path)

    file_list = []
    if subpathIsFile:
        # Determine the main file
        main_file = None
        if derivatives_path.is_file() and derivatives_path.suffix[1:].lower() in args.input_format.lower():
            main_file = derivatives_path
        elif masters_path.is_file() and masters_path.suffix[1:].lower() in args.input_format.lower():
            main_file = masters_path
        else:
            raise FileNotFoundError(
                f"ERROR: {args.subPath} not found in package {args.packageID} masters or derivatives "
                f"matching {args.input_format}."
            )

        # Handle paired ogg/mp3 audio files
        if main_file.suffix.lower() in ['.ogg', '.mp3']:
            assoc_ext = '.mp3' if main_file.suffix.lower() == '.ogg' else '.ogg'

            if "derivatives" in str(main_file):
                # main_file is in derivatives → check derivatives first, then masters
                assoc_file_der = main_file.with_suffix(assoc_ext)
                assoc_file_mast = Path(masters_path.parent, main_file.stem + assoc_ext)
            else:
                # main_file is in masters → check derivatives first, then masters
                assoc_file_der = Path(derivatives_path.parent, main_file.stem + assoc_ext)
                assoc_file_mast = main_file.with_suffix(assoc_ext)

            if assoc_file_der.is_file():
                file_list.append(assoc_file_der)
            elif assoc_file_mast.is_file():
                file_list.append(assoc_file_mast)
            else:
                raise FileNotFoundError(
                    f"ERROR: Associated file for {main_file.name} with extension {assoc_ext} not found "
                    f"in masters or derivatives. Does {assoc_ext} version exist in the backlog package?"
                )
    else:
        masters_count = 0
        derivatives_count = 0
        if os.path.isdir(derivatives):
            for input_file in os.listdir(derivatives):
                input_file_path = os.path.join(derivatives, input_file)
                if args.input_format.lower() != "ogg_mp3":
                    if os.path.isfile(input_file_path) and input_file.lower().endswith(f".{args.input_format.lower()}"):
                        derivatives_count += 1
                        file_list.append(input_file_path)
                else:
                    if os.path.isfile(input_file_path):
                        if input_file.lower().endswith(".ogg") or input_file.lower().endswith(".mp3"):
                            derivatives_count += 1
                            file_list.append(input_file_path)
        if derivatives_count == 0:
            if os.path.isdir(masters):
                for input_file in os.listdir(masters):
                    input_file_path = os.path.join(masters, input_file)
                    if args.input_format.lower() != "ogg_mp3":
                        if os.path.isfile(input_file_path) and input_file.lower().endswith(f".{args.input_format.lower()}"):
                            masters_count += 1
                            file_list.append(input_file_path)
                    else:
                        if os.path.isfile(input_file_path):
                            if input_file.lower().endswith(".ogg") or input_file.lower().endswith(".mp3"):
                                derivatives_count += 1
                                file_list.append(input_file_path)

        if masters_count == 0 and derivatives_count == 0:
            raise FileNotFoundError(f"ERROR: no {args.input_format.lower()} files found in package {args.packageID} masters or derivatives.")

    # Move access files to SPE_DAO
    for access_file in file_list:
        ext = os.path.splitext(access_file)[1][1:].lower()
        format_path = os.path.join(object_path, ext)
        if not os.path.isdir(format_path):
            os.mkdir(format_path)
        shutil.copy(access_file, format_path)

    # make thumbnail
    print ("Creating thumbnail")
    iiiflow.make_thumbnail(collection_ID, args.refID)

    pdf_formats = ["png", "jpg"]
    if not args.input_format.lower() in av_formats:
        if args.PDF.lower() == "true" and args.input_format.lower() in pdf_formats:
            print ("Creating alternative PDF...")
            iiiflow.create_pdf(collection_ID, args.refID)

    # Create pyramidal tifs
    print ("Creating pyramidal tifs (.ptifs)...")
    iiiflow.create_ptif(collection_ID, args.refID)

    if not args.input_format.lower() in av_formats:
        # OCR
        print ("Recognizing text...")
        iiiflow.create_hocr(collection_ID, args.refID)

        # Index HOCR
        print ("Indexing text for content search...")
        iiiflow.index_hocr_to_solr(collection_ID, args.refID)
    else:
        # Create AV transcription
        print ("Transcribing...")
        iiiflow.create_transcription(collection_ID, args.refID)

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
    new_dao = client.post("repositories/2/digital_objects", json=dao_object)
    if new_dao.status_code == 200:
        dao_uri = new_dao.json()["uri"]
        print (f"Added digital object record {dao_uri}")
    else:
        print (f"Failed digital object record --> {new_dao.status_code}")
        print (json.dumps(dao_object, indent=4))
        print (f"Failed digital object record --> {new_dao.status_code}")
        print (new_dao.reason)
        sys.exit()

    # Attach new digital object instance to archival object
    dao_link = {
        "jsonmodel_type": "instance",
        "digital_object": {"ref": dao_uri},
        "instance_type": "digital_object",
        "is_representative": True,
    }

    # Ensure all other instances are is_representative = False
    for instance in item["instances"]:
        instance["is_representative"] = False
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

    update_item = client.post(item["uri"], json=item)
    if update_item.status_code == 200:
        print (f"Updated archival object record --> {update_item.status_code}")
    else:
        print (f"Failed updating archival object record --> {update_item.status_code}")
        print (json.dumps(item, indent=4))
        print (f"Failed updating archival object record --> {update_item.status_code}")
        print (update_item.reason)
        sys.exit()
    
    print ("Success!")
    print (f"Check out digital object at:")
    #print (f"https://media.archives.albany.edu/test.html?collection={collection_ID}&id={args.refID}")
    print (f"https://media.archives.albany.edu?manifest={dao_url}")

if __name__ == "__main__":
    main()
