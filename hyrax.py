import os
import json
import yaml
import requests
from bs4 import BeautifulSoup

def log(msg, log_file):
    with open(log_file, "a") as f:
        f.write("\n" + msg)

def check_response(session, msg, log_file, postData=None):
    if session.status_code != 200:
        error_msg = f"ERROR: {msg}, HTTP {str(session.status_code)}"
        log(error_msg, log_file)
        if hasattr(session, 'reason'):
            log("REASON: " + str(session.reason), log_file)
        if postData:
            log("DATA: " + str(postData), log_file)
        raise requests.ConnectionError(error_msg)
    else:
        log(f"Success: {msg}", log_file)

def single(field):
    if len(field) == 0:
        return ""
    else:
        return field[0]

def addAccession(hyraxURI, packageID, refID, log_file):
    #print (f"trying {hyraxURI}")
    session = requests.Session()
    r = session.get(hyraxURI + ".json", verify=False)
    #print ("done")
    check_response(r, "Connecting to Hyrax", log_file)

    hyraxJSON = r.json()
    log("Reading metadata from Hyrax...", log_file)
    hyraxData = [
        "Dao", hyraxURI.split("/concern/")[1], "", packageID,
        hyraxJSON["collecting_area"], hyraxJSON["collection_number"],
        hyraxJSON["collection"], hyraxJSON["archivesspace_record"],
        "|".join(hyraxJSON["record_parent"]), single(hyraxJSON["title"]),
        "|".join(hyraxJSON["description"]), single(hyraxJSON["date_created"]),
        single(hyraxJSON["resource_type"]), single(hyraxJSON["license"]),
        single(hyraxJSON["rights_statement"]), "|".join(hyraxJSON["subject"]),
        hyraxJSON["coverage"], "|".join(hyraxJSON["processing_activity"]),
        "|".join(hyraxJSON["extent"]), single(hyraxJSON["language"])
    ]

    #Check to make sure ref_id provided matches whats in Hyrax
    if hyraxJSON["archivesspace_record"] != refID:
        log(f'ERROR: Failed to add accession ID to Hyrax. \n\tProvided ASpace ref ID {refID} does not match metadata in Hyrax. \n\tObject {hyraxURI} instead has ref ID of {hyraxJSON["archivesspace_record"]}.', log_file)
    else:

        if packageID in hyraxJSON["accession"]:
            log("Accession ID already entered in Hyrax.", log_file)
        else:
            #get Hyrax login data
            configFile = os.path.join(os.path.expanduser("~"), ".hyrax.yml")
            with open(configFile, 'r') as stream:
                try:
                    config = yaml.load(stream, Loader=yaml.Loader)
                    log("Read Hyrax config data", log_file)
                except yaml.YAMLError as exc:
                    print(exc)
                    
            loginPage = session.get(config["baseurl"], verify=False)
            check_response(loginPage, "Connecting to Hyrax login page", log_file)

            loginSoup = BeautifulSoup(loginPage.text, 'html.parser')
            token = loginSoup.find("meta",  {"name": "csrf-token"})["content"]
            loginData = {"user[email]": config["username"], "user[password]": config["password"], "authenticity_token" : token}
            signin = session.post(config["baseurl"], data=loginData, verify=False)
            check_response(signin, "Logging into Hyrax", log_file)

            editForm = session.get(hyraxURI + "/edit", headers={'Cache-Control': 'no-cache'}, verify=False)
            check_response(editForm, "Reading Hyrax edit form", log_file)
            
            editSoup = BeautifulSoup(editForm.text, 'html.parser')
            editToken = editSoup.find("meta",  {"name": "csrf-token"})["content"]
            form = editSoup.find("form",  {"class": "edit_dao"})
            submitToken = form.find("input",  {"name": "authenticity_token"}).get("value")
            submitData = {"authenticity_token": submitToken, "dao[accession][]": packageID, '_method': 'patch'}
            
            headers = {'X-CSRF-Token': submitData["authenticity_token"], 'Cache-Control': 'no-cache'}
            submit = session.post(hyraxURI + "?locale=en", headers=headers, data=submitData, verify=False)
            check_response(submit, "Submitting updated accession ID to Hyrax", log_file, submitData)

    return hyraxData
    