import os
from flask import Flask
from flask import flash, redirect, Markup
from flask import request
from flask import url_for, send_from_directory
from markupsafe import escape
from flask import render_template

from forms.ingest import IngestForm
from forms.accession import AccessionForm
from forms.derivatives import DerivativesForm
from forms.list import ListForm
from forms.ocr import OcrForm
from forms.aspace import AspaceForm
from forms.package import PackageForm
from forms.bulk import HyraxUploadForm, ASpaceUpdateForm

from utilities.listFiles import listFiles
from aspaceDAO import addDAO
from hyrax import addAccession

import csv
import shutil
from datetime import datetime
from subprocess import Popen, PIPE
import traceback

app = Flask(__name__)
app.secret_key = b'_5#y73:F4T8z\n\xec]/'

@app.route('/')
def index():
    return render_template('root.html')

@app.route('/ingest', methods=['GET', 'POST'])
def ingest():
    error = None
    if request.method == 'POST':
        form = IngestForm(request.form)
        collectionID = form.collectionID.data.strip()
        #altPath = form.altPath.data
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-ingest-{collectionID}.log"
            command = f"python -u /code/utilities/ingest.py {collectionID} >> {log_file} 2>&1 &"
            #print ("running command: " + command)
            ingest = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('ingest'))
    return render_template('ingest.html', error=error)

@app.route('/accession', methods=['GET', 'POST'])
def accession():
    error = None
    if request.method == 'POST':
        form = AccessionForm(request.form)
        accessionID = form.accessionID.data.strip()
        collectionID = form.collectionID.data.strip()
        #altPath = form.altPath.data
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-accession-{collectionID}.log"
            command = f"python /code/utilities/ingest.py {collectionID} -a {accessionID} >> {log_file} 2>&1 &"
            #print ("running command: " + command)
            accession = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

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
        subPath = form.subPath.data.strip()
        resize = form.resize.data.strip()
        density = form.density.data.strip()
        monochrome = form.monochrome.data

        if not form.validate():
            flash(form.errors, 'error')
        else:
            collectionID = packageID.split("_")[0]
            #look for matching files
            ext_match = False
            for root, dirs, files in os.walk(os.path.join("/backlog", collectionID, packageID)):
                for file in files:
                    if file.lower().endswith(inputFormat.lower()):
                        ext_match = True
            if not ext_match:
                flash({"Files": f'Error: No {inputFormat} files found in package {packageID}.'})
            else:
                log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-convert-{packageID}.log"
                command = f"python -u /code/utilities/convertImages.py {packageID} -i {inputFormat} -o {outputFormat}"
                if subPath:
                    command = command + f" -p {subPath}"
                if resize:
                    command = command + f" -r {resize}"
                if density:
                    command = command + f" -r {density}"
                if monochrome:
                    command = command + f" -bw"
                command = command + f" >> {log_file} 2>&1 &"
                
                print ("running command: " + command)
                convert = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

                success_msg = Markup(f'<div>Success! Converting {inputFormat} files in {packageID} to {outputFormat}. Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(success_msg, 'success')
                return redirect(url_for('derivatives'))
    return render_template('derivatives.html', error=error)

@app.route('/list', methods=['GET', 'POST'])
def list():
    error = None
    if request.method == 'POST':
        form = ListForm(request.form)
        packageID = form.packageID.data.strip()
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-list-{packageID}.log"
            colID = packageID.split("_")[0].split("-")[0]
            if log_file:
                with open(log_file, "a") as f:
                    f.write("Copying empty asInventory sheet to metadata directory...\n")
            else:
                print ("Copying empty asInventory sheet to metadata directory...")
            shutil.copy2("/code/static/asInventory.xlsx", f"/backlog/{colID}/{packageID}/metadata")
            listFiles(packageID, True, log_file)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('list'))
    return render_template('list.html', error=error)

@app.route('/sheet', methods=['GET'])
def downloadSheet():
    sheetPath = "/code/static"
    return send_from_directory(sheetPath, "asInventory.xlsx", as_attachment=True)

@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    error = None
    if request.method == 'POST':
        form = OcrForm(request.form)
        packageID = form.packageID.data.strip()
        subPath = form.subPath.data
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-ocr-{packageID}.log"
            command = f"python -u /code/utilities/ocr.py {packageID} >> {log_file} 2>&1 &"
            if subPath:
                command = command.replace(">>", f"-p {subPath} >>")
            #print ("running command: " + command)
            ocr = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('ocr'))
    return render_template('ocr.html', error=error)

@app.route('/aspace', methods=['GET', 'POST'])
def aspace():
    error = None
    if request.method == 'POST':
        form = AspaceForm(request.form)
        packageID = form.packageID.data.strip()
        refID = form.refID.data.strip()
        hyraxURI = form.hyraxURI.data.strip()

        #validate
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-aspace-{packageID}.log"
            packagePath = os.path.join("/backlog", packageID.split("_")[0], packageID)
            if len(os.listdir(os.path.join(packagePath, "derivatives"))) > 0:
                file_name = os.listdir(os.path.join(packagePath, "derivatives"))[0]
            elif len(os.listdir(os.path.join(packagePath, "masters"))) > 0:
                file_name = os.listdir(os.path.join(packagePath, "masters"))[0]
            else:
                error_obj = {"Invalid_package": [f"Package {packageID} has no files in either derivatives or masters."]}
                flash(error_obj, 'error')
 
            #Add package ID to Hyrax if not there?
            hyraxData = addAccession(hyraxURI, packageID, refID, log_file)
            hyraxData[2] = file_name

            #Check to make sure ref_id provided matches whats in Hyrax
            if hyraxData[7] != refID:
                error_obj = {"Invalid_refID": [f"Provided ASpace ref ID {refID} does not match metadata in Hyrax. Object {hyraxURI} instead has ref ID of {hyraxData[7]}."]}
                flash(error_obj, 'error')
            else:
                #Create digital object record in ASpace
                addDAO(refID, hyraxURI, log_file)

                #Add CSV to package /metadata folder
                with open(log_file, "a") as open_log:
                    open_log.write("\nWriting Hyrax metadata to package...")
                    headers = ["Type", "URIs", "File Paths", "Accession", "Collecting Area", "Collection Number", "Collection", \
                    "ArchivesSpace ID", "Record Parents", "Title", "Description", "Date Created", "Resource Type", "License", \
                    "Rights Statement", "Subjects", "Whole/Part", "Processing Activity", "Extent", "Language"]
                    metadataPath = os.path.join(packagePath, "metadata")
                    metadataFile = os.path.join(metadataPath, packageID + ".tsv")
                    if os.path.isfile(metadataFile):
                         flash(form.errors, 'error')
                    else:
                        with open(metadataFile, "w") as f:
                            writer = csv.writer(f, delimiter='\t', lineterminator='\n')
                            writer.writerow(headers)
                            writer.writerow(hyraxData)
                            f.close()
                    open_log.write("\nComplete!")
                    open_log.write(f"\nFinished at {datetime.now()}")
                    open_log.close()

                success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(success_msg, 'success')
                return redirect(url_for('aspace'))
            
    return render_template('aspace.html', error=error)

@app.route('/buildHyraxUpload', methods=['GET', 'POST'])
def buildHyraxUpload():
    error = None
    if request.method == 'POST':
        form = HyraxUploadForm(request.form)
        packageID = form.packageID.data.strip()
        fileLimiter = form.file.data

        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-buildHyraxUpload-{packageID}.log"
            command = f"python -u /code/utilities/buildHyraxUpload.py {packageID}"
            if fileLimiter:
                command = command + f" -f \"{fileLimiter.strip()}\""
            command = command + f" >> {log_file} 2>&1 &"

            #print ("running command: " + command)
            build = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('buildHyraxUpload'))

    return render_template('buildHyraxUpload.html', error=error)

@app.route('/buildASpaceUpdate', methods=['GET', 'POST'])
def buildASpaceUpdate():
    error = None
    if request.method == 'POST':
        form = ASpaceUpdateForm(request.form)
        packageID = form.packageID.data.strip()
        fileLimiter = form.file.data

        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-buildASpaceUpdate-{packageID}.log"
            command = f"python -u /code/utilities/buildASpaceUpdate.py {packageID}"
            if fileLimiter:
                command = command + f" -f \"{fileLimiter.strip()}\""
            command = command + f" >> {log_file} 2>&1 &"

            #print ("running command: " + command)
            build = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('buildASpaceUpdate'))

    return render_template('buildASpaceUpdate.html', error=error)

@app.route('/package', methods=['GET', 'POST'])
def package():
    error = None
    if request.method == 'POST':
        form = PackageForm(request.form)
        packageID = form.packageID.data.strip()
        update = form.update.data
        noderivatives = form.noderivatives.data

        if not form.validate():
            flash(form.errors, 'error')
        else:
            collectionID = packageID.split("_")[0]
            metadata_file = f'/backlog/{collectionID}/{packageID}/metadata/{packageID}.tsv'
            if not os.path.isfile(metadata_file):
                error_obj = {"Cannot package": [f"Package {packageID} does not have a metadata file. You must first update the ASpace digital object. Use the Connect to ASpace form for single files, or Build Hyrax Upload Sheet for large ingests."]}
                flash(error_obj, 'error')
            else:
                log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-package-{packageID}.log"
                command = f"python -u /code/utilities/packageAIP.py {packageID}"
                if update:
                    command = command + " --update"
                if noderivatives:
                    command = command + " --noderivatives"
                command = command + f" >> {log_file} 2>&1 &"

                #print ("running command: " + command)
                finalize = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)

                success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(success_msg, 'success')
                return redirect(url_for('package'))

    return render_template('package.html', error=error)

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

@app.errorhandler(Exception)
def handle_exception(exception):
    error_log = "/logs/error.log"
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    stack_header = (
            "****************************************************************************************************************\n"
            + now
            + " - "
            + repr(exception)
            + "\n****************************************************************************************************************\n"
        )
    stack_trace = stack_header + traceback.format_exc()
    # prepend to log file
    if not os.path.isfile(error_log):
        open(error_log, 'x').close()
    with open(error_log, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(stack_trace + content)
    return f"Internal Server Error\n{repr(exception)}", 500


if __name__ == "__main__":
    app.run(host='0.0.0.0')
