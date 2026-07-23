import os, json
from wtforms import validators
import asnake.logging as logging
from asnake.client import ASnakeClient
from utilities.id_normalization import normalize_collection_id

logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
client = ASnakeClient()

def validate_collectionID(form, field):
    collection_id = normalize_collection_id(field.data)
    field.data = collection_id
    r = client.get(f"repositories/2/find_by_id/resources", params={"identifier[]": json.dumps([collection_id])})
    if r.status_code != 200:
        raise validators.ValidationError(f'Invalid ID or ASpace request. \"{collection_id}\" returns HTTP {str(r.status_code)}')
    elif len(r.json()['resources']) != 1:
        raise validators.ValidationError(f'Invalid ref ID. Found {str(len(r.json()["resources"]))} matching resources with that ID?.')

def validate_collectionID_ingest(form, field):
    collection_id = normalize_collection_id(field.data)
    field.data = collection_id
    available_collections = os.listdir("/ingest")
    if not collection_id in available_collections:
        raise validators.ValidationError(f'Error: Nothing to ingest for {collection_id}. No folder in ingest path  \\\\Lincoln\\Library\\SPE_Processing\\ingest\\{collection_id}.')

def validate_collectionID_DAO(form, field):
    collection_id = normalize_collection_id(field.data)
    field.data = collection_id
    available_collections = os.listdir("/SPE_DAO")
    if not collection_id in available_collections:
        raise validators.ValidationError(f'Error: No Digital Object for {collection_id}. No folder in SPE_DAO path  \\\\Lincoln\\Library\\SPE_DAO\\{collection_id}.')

def validate_accessionID(form, field):
    # check if accession exists in ASpace
    call = "repositories/2/search?page=1&aq={\"query\":{\"field\":\"identifier\", \"value\":\"" + field.data.strip() + "\", \"jsonmodel_type\":\"field_query\"}}"
    accessionResponse = client.get(call).json()
    matches = len(accessionResponse["results"])
    if matches != 1:
        raise validators.ValidationError(f'Error: Could not find accession {field.data.strip()} in ArchivesSpace, found {matches} matching accessions.')

def validate_packageID(form, field):
    available_packages = []
    for collection_packages in os.listdir("/backlog"): 
        if os.path.isdir(os.path.join("/backlog", collection_packages)):
            available_packages.extend(os.listdir(os.path.join("/backlog", collection_packages)))
    
    if not "_" in field.data:
        raise validators.ValidationError('Invalid package ID.')
    elif not field.data.startswith(("apap", "ger", "mss", "ua", "rareitem", "mathes", "etd")):
        raise validators.ValidationError('Invalid package ID. Does not start with an allowed ID prefix (apap, ger, mss, ua, rareitem, mathes, etd).')
    elif not field.data.strip() in available_packages:
        raise validators.ValidationError(f'Error: Package {field.data.strip()} not found in \\\\Lincoln\\Library\\SPE_Processing\\backlog.')
    packageDirs = os.listdir(os.path.join("/backlog", field.data.split("_")[0], field.data.strip()))
    subfolders = ["derivatives", "masters", "metadata"]
    for subfolder in subfolders:
        if not subfolder in packageDirs:
            raise validators.ValidationError(f'Invalid package. Missing {subfolder} directory.')

def _matches_input_format(file_name, input_format):
    fmt = input_format.lower().strip().lstrip(".")
    lowered = file_name.lower()
    if fmt == "ogg_mp3":
        return lowered.endswith(".ogg") or lowered.endswith(".mp3")
    if fmt == "warc":
        return lowered.endswith(".warc") or lowered.endswith(".warc.gz")
    return lowered.endswith(f".{fmt}")

def _has_matching_files(search_root, input_format):
    if not os.path.isdir(search_root):
        return False
    for _, _, files in os.walk(search_root):
        for name in files:
            if _matches_input_format(name, input_format):
                return True
    return False

def validate_input_format_exists(form, field):
    package_id = form.packageID.data.strip() if getattr(form, "packageID", None) and form.packageID.data else ""
    input_format = field.data.strip() if field.data else ""

    # Let other validators report missing/invalid package and format values.
    if not package_id or not input_format or "_" not in package_id:
        return

    collection_id = package_id.split("_")[0]
    package_path = os.path.join("/backlog", collection_id, package_id)
    masters = os.path.join(package_path, "masters")
    derivatives = os.path.join(package_path, "derivatives")

    if not os.path.isdir(package_path):
        return

    sub_path = form.subPath.data.strip() if getattr(form, "subPath", None) and form.subPath.data else ""

    if sub_path:
        normalized_sub_path = os.path.normpath(sub_path.replace("\\", os.sep)).lstrip(os.sep)
        masters_target = os.path.join(masters, normalized_sub_path)
        derivatives_target = os.path.join(derivatives, normalized_sub_path)

        for target in [derivatives_target, masters_target]:
            if os.path.isfile(target):
                if _matches_input_format(os.path.basename(target), input_format):
                    return
            elif _has_matching_files(target, input_format):
                return

        raise validators.ValidationError(
            f'No {input_format} files were found at sub path "{sub_path}" in package {package_id}.'
        )

    if _has_matching_files(derivatives, input_format) or _has_matching_files(masters, input_format):
        return

    raise validators.ValidationError(
        f'No {input_format} files were found in package {package_id} under derivatives or masters.'
    )

def validate_refID(form, field):
    package_id = form.packageID.data.strip() if getattr(form, "packageID", None) and form.packageID.data else ""
    ref_id = field.data.strip()

    if package_id.startswith(("mathes_", "rareitem_")):
        return

    if package_id.startswith(("etd_", "ead_")):
        if len(ref_id) >= 5 and ref_id[:4].isdigit() and ref_id[4] == "-":
            year = int(ref_id[:4])
            if 1914 <= year <= 2050:
                return
        raise validators.ValidationError(
            'Invalid ref ID. For ETD packages, ref ID must start with a 4-digit year between 1914 and 2050 followed by "-" (example: 1977-Rinaldi).'
        )

    r = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + ref_id)
    if r.status_code != 200:
        raise validators.ValidationError(f'Invalid ASpace request. \"{ref_id}\" returns HTTP {str(r.status_code)}')
    elif len(r.json()['archival_objects']) != 1:
        raise validators.ValidationError(f'Invalid ref ID. Found {str(len(r.json()["archival_objects"]))} matching archival objects.')

def validate_refID_recreate(form, field):
    ref_id = field.data.strip()
    r = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + ref_id)
    if r.status_code == 200 and len(r.json().get('archival_objects', [])) == 1:
        return

    # Fallback for collections using non-ASpace identifiers.
    dao_root = "/SPE_DAO"
    fallback_collections = ["etd", "mathes", "rareitem"]
    for collection_id in fallback_collections:
        if os.path.isdir(os.path.join(dao_root, collection_id, ref_id)):
            return

    raise validators.ValidationError(
        f'Invalid ref ID. "{ref_id}" was not found in ArchivesSpace or in DAO fallback collections ({", ".join(fallback_collections)}).'
    )
