from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_packageID

class HyraxUploadForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    file = StringField('File', [validators.Length(min=0, max=100)])
    combine_multiple = BooleanField()

class ASpaceUpdateForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    file = StringField('File', [validators.Length(min=0, max=100)])
