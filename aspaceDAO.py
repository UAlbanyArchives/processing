import uuid
import asnake.logging as logging
from asnake.client import ASnakeClient

logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
client = ASnakeClient()

def addDAO(refID, hyraxURI, log_file):

    ref = client.get("repositories/2/find_by_id/archival_objects?ref_id[]=" + refID).json()
    item = client.get(ref["archival_objects"][0]["ref"]).json()

    existingDO = False
    existingRef = ""
    for instance in item["instances"]:
        if instance["instance_type"] == "digital_object":
            doRef = instance["digital_object"]["ref"]
            existingInstance = client.get(doRef).json()
            if existingInstance["file_versions"][0]["file_uri"] == hyraxURI:
                existingDO = True
                existingRef = doRef        
    if existingDO == True:
        with open(log_file, "a") as f:
            f.write("\nFound Existing Digital Object " + existingRef)
    else:
        #make new digital object
        fileVersion = {"jsonmodel_type":"file_version", "publish": True, "is_representative": True, "file_uri": hyraxURI, \
                        "use_statement": "", "xlink_actuate_attribute":"none", "xlink_show_attribute":"embed"}
        daoUUID = str(uuid.uuid4())
        daoTitle = "Online Object Uploaded through Hyrax UI"
        daoObject = {"jsonmodel_type": "digital_object", "publish": True, "external_ids": [], "subjects": [], "linked_events": [], \
                    "extents": [], "dates": [], "external_documents": [], "rights_statements": [], "linked_agents": [], \
                    "file_versions": [fileVersion], "restrictions": False, "notes": [], "linked_instances": [], "title": daoTitle, \
                    "language": "", "digital_object_id": daoUUID}

        #upload new digital object
        newDao = client.post("repositories/2/digital_objects", json=daoObject)
        daoURI = newDao.json()["uri"]
        with open(log_file, "a") as f:
            f.write("\nNew Digital Object " + daoURI + " --> " + str(newDao.status_code))
        
        #attach new digital object instance to archival object
        daoLink = {"jsonmodel_type": "instance", "digital_object": {"ref": daoURI}, "instance_type": "digital_object", \
                    "is_representative": False}                        
        item["instances"].append(daoLink)
        updateItem = client.post(item["uri"], json=item)
        if updateItem.status_code != 200:
            with open(log_file, "a") as f:
                f.write("\nFailed to attach Instance --> " + str(updateItem.status_code))
                f.write("\n" + str(updateItem.text))
        else:
            with open(log_file, "a") as f:
                f.write("\nAttached Instance --> " + str(updateItem.status_code))
        
        #update resource
        resourceURI = item["resource"]["ref"]
        resource = client.get(resourceURI).json()
        resource.pop('system_mtime', None)
        resource.pop('user_mtime', None)
        update = client.post(resourceURI, json=resource)
        with open(log_file, "a") as f:
            f.write("\n" + str(update.status_code) + " --> Updated Resource for Export: " + resourceURI)
            