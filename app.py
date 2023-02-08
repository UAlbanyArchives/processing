from flask import Flask
from flask import request
#from flask import url_for
#from markupsafe import escape
from flask import render_template

from forms.ingest import IngestForm

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('root.html')

@app.get('/ingest')
def ingest_get():
    return render_template('ingest.html')

@app.post('/ingest')
def ingest_post():
    form = IngestForm(request.form)
    if form.validate():

        collectionID = form.collectionID.data
        altPath = form.altPath.data

        print (collectionID)
        print (altPath)
        return render_template('root.html')
    return render_template('ingest.html', form=form)

@app.get('/accession')
def accession_get():
    return render_template('accession.html')

@app.get('/derivatives')
def derivatives_get():
    return render_template('derivatives.html')

@app.get('/ocr')
def ocr_get():
    return render_template('ocr.html')

@app.get('/package')
def package_get():
    return render_template('package.html')

