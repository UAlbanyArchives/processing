import os, json
from wtforms import validators
import asnake.logging as logging
from asnake.client import ASnakeClient

logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
client = ASnakeClient()

def validate_collectionID(form, field):
    r = client.get(f"repositories/2/find_by_id/resources", params={"identifier[]": json.dumps([field.data.strip()])})
    if r.status_code != 200:
        raise validators.ValidationError(f'Invalid ID or ASpace request. \"{field.data.strip()}\" returns HTTP {str(r.status_code)}')
    elif len(r.json()['resources']) != 1:
        raise validators.ValidationError(f'Invalid ref ID. Found {str(len(r.json()["resources"]))} matching resources with that ID?.')

def validate_collectionID_ingest(form, field):
    available_collections = os.listdir("/ingest")
    if not field.data.strip() in available_collections:
        raise validators.ValidationError(f'Error: Nothing to ingest for {field.data.strip()}. No folder in ingest path  \\\\Lincoln\\Library\\SPE_Processing\\ingest\\{field.data.strip()}.')

def validate_collectionID_DAO(form, field):
    available_collections = os.listdir("/SPE_DAO")
    if not field.data.strip() in available_collections:
        raise validators.ValidationError(f'Error: No Digital Object for {field.data.strip()}. No folder in SPE_DAO path  \\\\Lincoln\\Library\\SPE_DAO\\{field.data.strip()}.')

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
    elif not field.data.startswith(("apap", "ger", "mss", "ua")):
        raise validators.ValidationError('Invalid package ID. Does not start with UAlbany mss ID (apap, ger, mss, ua).')
    elif not field.data.strip() in available_packages:
        raise validators.ValidationError(f'Error: Package {field.data.strip()} not found in \\\\Lincoln\\Library\\SPE_Processing\\backlog.')
    packageDirs = os.listdir(os.path.join("/backlog", field.data.split("_")[0], field.data.strip()))
    subfolders = ["derivatives", "masters", "metadata"]
    for subfolder in subfolders:
        if not subfolder in packageDirs:
            raise validators.ValidationError(f'Invalid package. Missing {subfolder} directory.')

def validate_refID(form, field):
    r = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + field.data.strip())
    if r.status_code != 200:
        raise validators.ValidationError(f'Invalid ASpace request. \"{field.data.strip()}\" returns HTTP {str(r.status_code)}')
    elif len(r.json()['archival_objects']) != 1:
        raise validators.ValidationError(f'Invalid ref ID. Found {str(len(r.json()["archival_objects"]))} matching archival objects.')
