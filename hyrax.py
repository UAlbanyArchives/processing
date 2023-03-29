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

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


def addAccession(hyraxURI, packageID, log_file):
    print (f"trying {hyraxURI}")
    session = requests.Session()
    r = session.get(hyraxURI + ".json")
    print ("done")
    check_response(r, "Connecting to Hyrax", log_file)

    
    if packageID not in r.json()["accession"]:
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

        editForm = session.get(hyraxURI + "/edit", headers={'Cache-Control': 'no-cache'})
        check_response(editForm, "Reading Hyrax edit form", log_file)
        
        editSoup = BeautifulSoup(editForm.text, 'html.parser')
        editToken = editSoup.find("meta",  {"name": "csrf-token"})["content"]
        form = editSoup.find("form",  {"class": "edit_dao"})
        #submitToken = form.attrs.find("input",  {"name": "authenticity_token"}).get("value")
        #submitData = {"dao[collection]": "NAACP Albany (New York) Branch Records"}
        submitData = {}
        
        for i in form.find_all("input"):
            #print (i.attrs.get("name"))
            #print ("\t" + str(i.attrs.get("value")))
            submitData[i.attrs.get("name")] = i.attrs.get("value")
            if i.attrs.get("name") == "authenticity_token":
                this = i.attrs.get("value")
                print ("-->" + str(this))
                print (type(this))
        for s in form.find_all("select"):
            #print (s.attrs.get("name"))
            for option in s.find_all('option', selected=True):
                #print ("\t" + str(option.get("value")))
                submitData[s.attrs.get("name")] = option.get("value")
        
        #for t in form.find_all("textarea"):
        #    print (t.attrs.get("name"))
        #    print ("\t" + str(t.contents))
        #    submitData[i.attrs.get("name")] = t.contents
        #submitData['dao[accession][]'] = packageID
        #print (submitData['dao[accession][]'])
        #submitData["authenticity_token"] = editToken
        #jsonData = json.dumps(submitData)
        #submitData["new_group_name_skel"] = "Select a group"
        #submitData["new_group_permission_skel"] = "none"
        #submitData["new_user_permission_skel"] = "none"
        print (editToken)
        print (submitData["authenticity_token"])
        print (token)
        newData = {"authenticity_token": this, "dao[accession][]": packageID, '_method': 'patch'}
        submitData["authenticity_token"] = this
        print (type(submitData["authenticity_token"]))
        h = {'X-CSRF-Token': submitData["authenticity_token"], 'Cache-Control': 'no-cache'}
        submit = session.post(hyraxURI + "?locale=en", headers=h, data=newData, verify=False)
        #submit = requests.Request('POST', hyraxURI, headers={'Cache-Control': 'no-cache', 'Content-Disposition': 'form-data'}, data=submitData)
        #prepared = submit.prepare()
        #pretty_print_POST(prepared)
        #res = session.send(prepared)
        check_response(submit, "Submitting updated accession ID to Hyrax", log_file, submitData)
    
    