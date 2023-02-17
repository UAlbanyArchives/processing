import os
from flask import Flask
from flask import flash, redirect
from flask import request
from flask import url_for
from markupsafe import escape
from flask import render_template

from forms.ingest import IngestForm
from forms.accession import AccessionForm
from forms.derivatives import DerivativesForm

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
        altPath = form.altPath.data
        if not form.validate():
            error = 'Invalid entry: ' + collectionID
            flash(error, 'error')
        else:
            flash('Success! ' + collectionID, 'success')
            return redirect(url_for('ingest'))
    return render_template('ingest.html', error=error)

@app.route('/accession', methods=['GET', 'POST'])
def accession():
    error = None
    if request.method == 'POST':
        form = AccessionForm(request.form)
        accessionID = form.accessionID.data
        collectionID = form.collectionID.data
        altPath = form.altPath.data
        if not form.validate():
            flash(f'Invalid entry! Accession {accessionID} or Collection {collectionID} is invalid.', 'error')
        else:
            flash(f'Success! Packaging accession {accessionID}.', 'success')
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
        else:
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
    log_dir = "logs"
    for log_file in os.listdir(log_dir):
        log_files.append(log_file)
    log_files.sort(reverse=True)
    return render_template('list_logs.html', log_files=log_files)

@app.get('/logs/<string:logFilename>')
def view_log(logFilename):
    log_dir = "logs"
    with open(os.path.join(log_dir, logFilename), "r") as f:
        text = f.read()
        return render_template('view_log.html', logFilename=escape(logFilename), log_text=text)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
