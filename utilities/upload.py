import os
#import iiiflow
import argparse

def main():
    parser = argparse.ArgumentParser(description="Process digital object upload arguments.")

    parser.add_argument("--packageID", required=True, help="The folder name of the SIP, e.g., apap301_h4fOLPL48CuxFPLpYxTmkL or ua950.009_qUQos7GYhzmB3uL3yjH5uX.")
    parser.add_argument("--input_format", required=True, help="A file extension to look for at the input format.")
    parser.add_argument("--subPath", help="Uploads files in this folder within the /backlog package.")
    parser.add_argument("--refID", required=True, help="A 32-character ArchivesSpace ID, e.g., '855f9efb1fae87fa3b6ef8c8a6e0a28d'.")
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

    args = parser.parse_args()

    print("Uploading Digital Object with the following details:")
    print(f"  Package ID: {args.packageID}")
    print(f"  Input format: {args.input_format}")
    print(f"  Sub Path: {args.subPath if args.subPath else 'N/A'}")
    print(f"  ArchivesSpace ref_id: {args.refID}")
    print(f"  Resource Type: {args.resource_type}")
    print(f"  License: {args.license}")
    print(f"  Rights Statement: {args.rights_statement if args.rights_statement else 'N/A'}")
    print(f"  Behavior: {args.behavior}")

    """
    1. Create SPE_DAO package and write metadata.yml and copy files over
    2. create thumbnail
    3. OCR or transcription
    4. create ptifs
    5. create manifest
    6. Add digital object record to ASpace
    7. Index record in ArcLight
    """

if __name__ == "__main__":
    main()
