from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_packageID, validate_refID
import os
import urllib.request
from urllib.parse import urlsplit, urlunsplit

def strip_params(data):
    # strip params and hashes, such as "?locale=en"
    try:
        return urlunsplit(urlsplit(data.strip())._replace(query="", fragment=""))
    except:
        raise validators.ValidationError(f'Invalid Hyrax URI. Not a valid URL.')


def validate_hyraxURI(form, field):
    if not field.data.lower().startswith("https://archives.albany.edu/concern/daos/"):
        raise validators.ValidationError(f'Invalid Hyrax URI. Is not a UAlbany Hyrax URL.')

def validate_singleFile(form, field):
    packagePath = os.path.join("/backlog", field.data.strip().split("_")[0], field.data.strip())
    files = os.listdir(os.path.join(packagePath, "derivatives"))
    if len(files) != 1:
        raise validators.ValidationError(f'Expected single file in the derivatives directory. This step is for single file uploads only.')

class AspaceForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID, validate_singleFile])
    refID = StringField('Ref ID', [validators.Length(min=32, max=32), validate_refID])
    hyraxURI = StringField('Hyrax URI', [validators.Length(min=50, max=100), validate_hyraxURI], [strip_params])
