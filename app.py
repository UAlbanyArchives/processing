import os
import shlex
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
from forms.upload import UploadForm
from forms.aspace import AspaceForm
from forms.package import PackageForm
from forms.reindex import ReindexForm
from forms.add_items import AddItemsForm
from forms.recreate import RecreateForm
from forms.bulk import HyraxUploadForm, ASpaceUpdateForm

from utilities.listFiles import listFiles
from aspaceDAO import addDAO
from add_items import add_aspace_items
from hyrax import addAccession

import csv
import shutil
from datetime import datetime
from dotenv import load_dotenv
from subprocess import Popen, PIPE
import traceback

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")

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
            command = [
                "python", "-u", "/code/utilities/ingest.py", 
                shlex.quote(collectionID)
            ]
            safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            ingest = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

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
            command = [
                "python", "/code/utilities/ingest.py", 
                shlex.quote(collectionID), 
                "-a", shlex.quote(accessionID)
            ]
            safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            accession = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

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
                command = [
                    "python", "-u", "/code/utilities/convertImages.py", 
                    shlex.quote(packageID), 
                    "-i", shlex.quote(inputFormat),
                    "-o", shlex.quote(outputFormat)
                ]
                
                if subPath:
                    command.extend(["-p", shlex.quote(subPath)])
                if resize:
                    command.extend(["-r", shlex.quote(resize)])
                if density:
                    command.extend(["-r", shlex.quote(density)])
                if monochrome:
                    command.append("-bw")
                
                # Add log file redirection
                safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"
                
                print ("running command: " + safe_command)
                convert = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

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
            command = [
                "python", "-u", "/code/utilities/ocr.py", 
                shlex.quote(packageID)
            ]

            if subPath:
                command.extend(["-p", shlex.quote(subPath)])
            
            # Add log file redirection
            safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            ocr = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('ocr'))
    return render_template('ocr.html', error=error)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    error = None
    if request.method == 'POST':
        form = UploadForm(request.form)
        packageID = form.packageID.data.strip()
        inputFormat = form.inputFormat.data.lower().strip()
        collectionID = packageID.split("_")[0]
        subPath = form.subPath.data.strip() if form.subPath.data else None
        refID = form.refID.data.strip()
        resource_type = form.resource_type.data.strip()
        license = form.license.data.strip()
        rights_statement = form.rights_statement.data.strip()
        behavior = form.behavior.data.strip()
        createPDF = str(form.createPDF.data)
        content_warning = form.content_warning.data.strip() if form.content_warning.data else ""

        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-upload-{packageID}.log"

            # Base command
            command = [
                "python", "-u", "/code/utilities/upload.py",
                "--packageID", packageID,
                "--input_format", inputFormat,
                "--refID", refID,
                "--PDF", createPDF,
                "--resource_type", resource_type,
                "--behavior", behavior
            ]

            # Add optional arguments
            if subPath:
                command.append("--subPath")
                command.append(subPath)
            if license:
                command.append("--license")
                command.append(license)
            if rights_statement:
                command.append("--rights_statement")
                command.append(rights_statement)
            if content_warning:
                command.append("--processing")
                command.append(content_warning)

            safe_command = " ".join(shlex.quote(arg) for arg in command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            upload = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('upload'))
    return render_template('upload.html', error=error)

@app.route('/add_items', methods=['GET', 'POST'])
def add_items():
    error = None
    if request.method == 'POST':
        form = AddItemsForm(request.form)
        
        # Prevent AttributeError by ensuring `.data` isn't None
        refID = form.refID.data.strip() if form.refID.data else ''
        title_1 = form.title_1.data.strip() if form.title_1.data else ''
        display_date_1 = form.display_date_1.data.strip() if form.display_date_1.data else ''
        normal_date_1 = form.normal_date_1.data.strip() if form.normal_date_1.data else ''
        title_2 = form.title_2.data.strip() if form.title_2.data else ''
        display_date_2 = form.display_date_2.data.strip() if form.display_date_2.data else ''
        normal_date_2 = form.normal_date_2.data.strip() if form.normal_date_2.data else ''

        # Validate form
        if not form.validate():
            flash(str(form.errors), 'error')
        else:
            res1, res2 = add_aspace_items(refID, title_1, display_date_1, normal_date_1, title_2, display_date_2, normal_date_2)

            errors = []
            success_messages = []

            # Handle res1
            if res1.status_code == 200:
                item1_id = res1.json().get('id', 'Unknown ID')
                success_messages.append(f"Item 1 added successfully with ID: {item1_id}")
            else:
                error_message = res1.json().get('error', 'Unknown error')
                errors.append(f"Item 1 failed: {error_message} (Status {res1.status_code})")

            # Handle res2
            if res2.status_code == 200:
                item2_id = res2.json().get('id', 'Unknown ID')
                success_messages.append(f"Item 2 added successfully with ID: {item2_id}")
            else:
                error_message = res2.json().get('error', 'Unknown error')
                errors.append(f"Item 2 failed: {error_message} (Status {res2.status_code})")
            
            # Flash errors and success messages
            if errors:
                e_obj = {}
                e_count = 0
                for e in errors:
                    e_obj[e] = e
                    e_count += 1
                flash(e_obj, 'error')

            if success_messages:
                flash(Markup("<br>".join(success_messages)), 'success')

        return redirect(url_for('add_items'))

    return render_template('add_items.html', error=error)


@app.route('/recreate', methods=['GET', 'POST'])
def recreate():
    error = None
    if request.method == 'POST':
        form = RecreateForm(request.form)
        mode = form.mode.data
        #collectionID = form.collectionID.data.strip()
        refID = form.refID.data.strip()
        from aspaceDAO import getCollectionID
        collectionID = getCollectionID(refID)
        print (f"CollectionID: {collectionID}")

        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-recreate-{mode}-{collectionID}-{refID}.log"

            command = [
                "python", "-u", "/code/utilities/recreate.py",
                mode,
                "--collectionID", collectionID,
                "--refID", refID
            ]

            safe_command = " ".join(shlex.quote(arg) for arg in command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            thumbnail = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
        
        return redirect(url_for('recreate'))
    return render_template('recreate.html', error=error)

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    error = None
    if request.method == 'POST':
        return redirect(url_for('bulk_upload'))
    return render_template('bulk_upload.html', error=error)

@app.route('/aspace', methods=['GET', 'POST'])
def aspace():
    error = None
    if request.method == 'POST':
        form = AspaceForm(request.form)
        packageID = form.packageID.data.strip()
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
            hyraxData = addAccession(hyraxURI, packageID, log_file)
            hyraxData[2] = file_name

            #Create digital object record in ASpace
            refID = hyraxData[7]
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
                    #append to existing .tsv
                    with open(metadataFile, "a") as f:
                        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
                        writer.writerow(hyraxData)
                        f.close()
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
        combine_multiple = form.combine_multiple.data

        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-buildHyraxUpload-{packageID}.log"
            command = [
                "python", "-u", "/code/utilities/buildHyraxUpload.py",
                shlex.quote(packageID)
            ]

            if fileLimiter:
                command.extend(["-f", shlex.quote(fileLimiter.strip())])
            if combine_multiple:
                command.append("-c")

            # Add log file redirection
            safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"

            # Execute the command
            build = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

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
            command = [
                "python", "-u", "/code/utilities/buildASpaceUpdate.py",
                shlex.quote(packageID)
            ]

            if fileLimiter:
                command.extend(["-f", shlex.quote(fileLimiter.strip())])

            # Add log file redirection
            safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"

            # Execute the command
            build = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

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
                command = [
                    "python", "-u", "/code/utilities/packageAIP.py",
                    shlex.quote(packageID)
                ]

                if update:
                    command.append("--update")
                if noderivatives:
                    command.append("--noderivatives")

                # Add log file redirection
                safe_command = " ".join(command) + f" >> {shlex.quote(log_file)} 2>&1 &"

                # Execute the command
                finalize = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

                success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
                flash(success_msg, 'success')
                return redirect(url_for('package'))

    return render_template('package.html', error=error)

@app.route('/reindex', methods=['GET', 'POST'])
def reindex():
    error = None
    if request.method == 'POST':
        form = ReindexForm(request.form)
        collectionID = form.collectionID.data.strip().lower()
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-reindex-{collectionID}.log"

            # Base command
            command = [
                "python", "-u", "/code/utilities/reindex.py",
                "--id", collectionID
            ]

            safe_command = " ".join(shlex.quote(arg) for arg in command) + f" >> {shlex.quote(log_file)} 2>&1 &"
            #print ("running command: " + safe_command)
            reindex = Popen(safe_command, shell=True, stdout=PIPE, stderr=PIPE)

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('reindex'))
    return render_template('reindex.html', error=error)

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
