from wtforms import Form, BooleanField, StringField, PasswordField, validators

class DerivativesForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=29, max=32)])
    inputFormat = StringField('Input Path', [validators.Length(min=3, max=3)])
    outputFormat = StringField('Output Path', [validators.Length(min=3, max=3)])
    subPath = StringField('Sub Path', [validators.Length(min=0, max=35)])
