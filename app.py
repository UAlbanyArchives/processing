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
from forms.ocr import OcrForm
from forms.aspace import AspaceForm

from aspaceDAO import addDAO
from hyrax import addAccession

from datetime import datetime
from subprocess import Popen, PIPE

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
        collectionID = form.collectionID.data
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
        accessionID = form.accessionID.data
        collectionID = form.collectionID.data
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


@app.route('/ocr', methods=['GET', 'POST'])
def ocr():
    error = None
    if request.method == 'POST':
        form = OcrForm(request.form)
        packageID = form.packageID.data
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
        packageID = form.packageID.data
        refID = form.refID.data
        hyraxURI = form.hyraxURI.data

        #validate
        if not form.validate():
            flash(form.errors, 'error')
        else:
            log_file = f"/logs/{datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')}-aspace-{packageID}.log"
            
            #Create digital object record in ASpace
            #addDAO(refID, hyraxURI, log_file)

            #Add package ID to Hyrax if not there?
            addAccession(hyraxURI, packageID, log_file)            

            #Add CSV to package /metadata folder

            success_msg = Markup(f'<div>Success! Checkout the log at <a href="{log_file}">{log_file}</a></div>')
            flash(success_msg, 'success')
            return redirect(url_for('aspace'))
            
    return render_template('aspace.html', error=error)

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
