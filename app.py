import os
from flask import Flask
from flask import flash, redirect, Markup
from flask import request
from flask import url_for
from markupsafe import escape
from flask import render_template

from forms.ingest import IngestForm
from forms.accession import AccessionForm
from forms.derivatives import DerivativesForm

import subprocess
from datetime import datetime
import asnake.logging as logging
from asnake.client import ASnakeClient

app = Flask(__name__)
app.secret_key = b'_5#y73:F4T8z\n\xec]/'

logging.setup_logging(filename="/logs/aspace-flask.log", filemode="a", level="INFO")
client = ASnakeClient()

available_collections = os.listdir("/ingest")
available_packages = []
for collection_packages in os.listdir("/backlog"):
    available_packages.extend(os.listdir(os.path.join("/backlog", collection_packages)))

@app.route('/')
def index():
    return render_template('root.html')

@app.route('/ingest', methods=['GET', 'POST'])
def ingest():
    error = None
    if request.method == 'POST':
        form = IngestForm(request.form)
        collectionID = form.collectionID.data
        #altPath = form.altPath.data
        if not form.validate():
            error = 'Invalid entry: ' + collectionID
            flash(error, 'error')
        elif not collectionID in available_collections:
            error = f'Error: Nothing to ingest for {collectionID}. No folder in ingest path  \\\\Lincoln\\Library\\SPE_Processing\\ingest\\{collectionID}.'
            flash(error, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-ingest-{collectionID}.log"
            command = f"python /code/utilities/ingest.py {collectionID} &"
            #print ("running command: " + command)
            with open(log_file, 'a') as out:
                ingest = subprocess.Popen(command, shell=True, stdout=out, stderr=out)
            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('ingest'))
    return render_template('ingest.html', error=error)

@app.route('/accession', methods=['GET', 'POST'])
def accession():
    error = None
    if request.method == 'POST':
        form = AccessionForm(request.form)
        accessionID = form.accessionID.data
        collectionID = form.collectionID.data
        #altPath = form.altPath.data
        if not form.validate():
            flash(f'Invalid entry! Accession {accessionID} or Collection {collectionID} is invalid.', 'error')
        elif not collectionID in available_collections:
            error = f'Error: No data to accession for {collectionID}. No folder in ingest path  \\\\Lincoln\\Library\\SPE_Processing\\ingest\\{collectionID}.'
            flash(error, 'error')
        else:
            # check if accession exists in ASpace
            call = "repositories/2/search?page=1&aq={\"query\":{\"field\":\"identifier\", \"value\":\"" + accessionID + "\", \"jsonmodel_type\":\"field_query\"}}"
            accessionResponse = client.get(call).json()
            matches = len(accessionResponse["results"])
            if matches != 1:
                error = f'Error: Could not find accession {accessionID} in ArchivesSpace, found {matches} matching accessions.'
                flash(error, 'error')
            else:
                log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-accession-{collectionID}.log"
                command = f"python /code/utilities/ingest.py {collectionID} -a {accessionID} &"
                #print ("running command: " + command)
                with open(log_file, 'a') as out:
                    accession = subprocess.Popen(command, shell=True, stdout=out, stderr=out)
                success_msg = Markup(f'<div>Success! Packaging accession {accessionID}. Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(success_msg, 'success')
                return redirect(url_for('accession'))
    return render_template('accession.html', error=error)


@app.route('/derivatives', methods=['GET', 'POST'])
def derivatives():
    error = None
    if request.method == 'POST':
        form = DerivativesForm(request.form)
        packageID = form.packageID.data.strip()
        inputFormat = form.inputFormat.data.lower().strip()
        outputFormat = form.outputFormat.data.lower().strip()
        subPath = form.subPath.data

        if not form.validate():
            flash(f'Invalid entry! PackageID {packageID}, input format {inputFormat}, or output format {outputFormat} is invalid.', 'error')
        elif not packageID in available_packages:
            flash(f'Error: Package {packageID} not found in \\\\Lincoln\\Library\\SPE_Processing\\backlog.', 'error')
        else:
            collectionID = packageID.split("_")[0]
            #look for matching files
            ext_match = False
            for root, dirs, files in os.walk(os.path.join("/backlog", collectionID, packageID)):
                for file in files:
                    if file.lower().endswith(inputFormat.lower()):
                        ext_match = True
            if not ext_match:
                flash(f'Error: No {inputFormat} files found in package {packageID}.')
            else:
                log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-convert-{packageID}.log"
                command = f"python /code/utilities/convertImages.py {packageID} -i {inputFormat} -o {outputFormat} &"
                print ("running command: " + command)
                with open(log_file, 'a') as out:
                    convert = subprocess.Popen(command, shell=True, stdout=out, stderr=out)
                
                success_msg = Markup(f'<div>Success! Converting {inputFormat} files in {packageID} to {outputFormat}. Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(f'Success! Creating {outputFormat.upper()}s for SIP {packageID}.', 'success')
                return redirect(url_for('derivatives'))
    return render_template('derivatives.html', error=error)


@app.get('/ocr')
def ocr_get():
    return render_template('ocr.html')

@app.get('/aspace')
def aspace():
    return render_template('aspace.html')

@app.get('/package')
def package_get():
    return render_template('package.html')

@app.get('/logs')
def list_logs():
    log_files = []
    log_dir = "/logs"
    for log_file in os.listdir(log_dir):
        log_files.append(log_file)
    log_files.sort(reverse=True)
    return render_template('list_logs.html', log_files=log_files)

@app.get('/logs/<string:logFilename>')
def view_log(logFilename):
    log_dir = "/logs"
    with open(os.path.join(log_dir, logFilename), "r") as f:
        text = f.read()
        return render_template('view_log.html', logFilename=escape(logFilename), log_text=text)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
