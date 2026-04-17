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
    elif not field.data.startswith(("apap", "ger", "mss", "ua", "rare_book", "mathes", "etd")):
        raise validators.ValidationError('Invalid package ID. Does not start with an allowed ID prefix (apap, ger, mss, ua, rare_book, mathes, etd).')
    elif not field.data.strip() in available_packages:
        raise validators.ValidationError(f'Error: Package {field.data.strip()} not found in \\\\Lincoln\\Library\\SPE_Processing\\backlog.')
    packageDirs = os.listdir(os.path.join("/backlog", field.data.split("_")[0], field.data.strip()))
    subfolders = ["derivatives", "masters", "metadata"]
    for subfolder in subfolders:
        if not subfolder in packageDirs:
            raise validators.ValidationError(f'Invalid package. Missing {subfolder} directory.')

def validate_refID(form, field):
    package_id = form.packageID.data.strip() if getattr(form, "packageID", None) and form.packageID.data else ""
    if package_id.startswith(("mathes", "etd", "rare_book")):
        return

    r = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + field.data.strip())
    if r.status_code != 200:
        raise validators.ValidationError(f'Invalid ASpace request. \"{field.data.strip()}\" returns HTTP {str(r.status_code)}')
    elif len(r.json()['archival_objects']) != 1:
        raise validators.ValidationError(f'Invalid ref ID. Found {str(len(r.json()["archival_objects"]))} matching archival objects.')

def validate_refID_recreate(form, field):
    ref_id = field.data.strip()
    r = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + ref_id)
    if r.status_code == 200 and len(r.json().get('archival_objects', [])) == 1:
        return

    # Fallback for collections using non-ASpace identifiers.
    dao_root = "/SPE_DAO"
    fallback_collections = ["etd", "mathes", "rare_book"]
    for collection_id in fallback_collections:
        if os.path.isdir(os.path.join(dao_root, collection_id, ref_id)):
            return

    raise validators.ValidationError(
        f'Invalid ref ID. "{ref_id}" was not found in ArchivesSpace or in DAO fallback collections ({", ".join(fallback_collections)}).'
    )
