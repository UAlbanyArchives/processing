from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_packageID

class ListForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
