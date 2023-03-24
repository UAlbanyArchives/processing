from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_packageID, validate_refID
import urllib.request
from urllib.parse import urlsplit, urlunsplit

def validate_hyraxURI(form, field):
    # strip params and such
    try:
        field.data = urlunsplit(urlsplit(field.data.strip())._replace(query="", fragment=""))
    except:
        raise validators.ValidationError(f'Invalid Hyrax URI. Not a valid URL.')
    if not field.data.lower().startswith("https://archives.albany.edu/concern/daos/"):
        raise validators.ValidationError(f'Invalid Hyrax URI. Is not a UAlbany Hyrax URL.')
    else:
        try:
            resp = urllib.request.urlopen(field.data).getcode()
            if not resp == 200:
                raise validators.ValidationError(f'Invalid Hyrax URI. {field.data} returns HTTP {str(resp)}')
        except urllib.error.HTTPError as e:
            raise validators.ValidationError(f'Invalid Hyrax URI. {field.data} returns {str(e)}')

class AspaceForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    refID = StringField('Ref ID', [validators.Length(min=32, max=32), validate_refID])
    hyraxURI = StringField('Hyrax URI', [validators.Length(min=50, max=60), validate_hyraxURI])
