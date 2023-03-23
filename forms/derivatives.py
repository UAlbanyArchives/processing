from wtforms import Form, BooleanField, StringField, PasswordField, validators

def validate_packageID(form, field):
    if not "_" in field.data:
        raise validators.ValidationError('Invalid package ID.')
    elif not field.data.startswith(("apap", "ger", "mss", "ua")):
        raise validators.ValidationError('Invalid package ID.')

class DerivativesForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    inputFormat = StringField('Input Path', [validators.Length(min=3, max=3)])
    outputFormat = StringField('Output Path', [validators.Length(min=3, max=3)])
    subPath = StringField('Sub Path', [validators.Length(min=0, max=35)])
