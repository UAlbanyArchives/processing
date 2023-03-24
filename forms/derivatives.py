from wtforms import Form, BooleanField, StringField, BooleanField, validators
from forms.custom_validators import validate_packageID

def validate_resize(form, field):
    if field.data:
        if not "x" in field.data.lower():
            raise validators.ValidationError('Invalid resize, must include an "X"')
        elif not field.data.strip().lower().split("x")[0].isdigit() or not field.data.strip().lower().split("x")[1].isdigit():
            raise validators.ValidationError('Invalid resize, must be two numbers, such as "1200x1200"')

def validate_density(form, field):
    if field.data:
        if not field.data.strip().isdigit():
            raise validators.ValidationError('Invalid density, must a number for dpi, such as "300"')

class DerivativesForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    inputFormat = StringField('Input Path', [validators.Length(min=3, max=3)])
    outputFormat = StringField('Output Path', [validators.Length(min=3, max=3)])
    subPath = StringField('Sub Path', [validators.Length(min=0, max=35)])
    resize = StringField('Resize', [validators.Length(min=0, max=13), validate_resize])
    density = StringField('Density', [validators.Length(min=0, max=6), validate_density])
    monochrome = BooleanField()
