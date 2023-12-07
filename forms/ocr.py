from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_packageID

class OcrForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    subPath = StringField('Subpath', [validators.Length(min=0, max=99)])
