from wtforms import Form, StringField, BooleanField, validators
from forms.custom_validators import validate_packageID

def validate_SIP(form, field):
    pass

class PackageForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=26, max=32), validate_packageID, validate_SIP])
    update = BooleanField()
    noderivatives = BooleanField()
