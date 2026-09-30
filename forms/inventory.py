from wtforms import Form, RadioField, StringField, validators
from forms.custom_validators import validate_collectionID, validate_refID

def validate_inventoryID(form, field):
    if len(field.data.strip()) == 32:
        validate_refID(form, field)
    else:
        validate_collectionID(form, field)

class InventoryForm(Form):
    inventoryID = StringField('Package ID', [validators.Length(min=5, max=32), validate_inventoryID])
    method = RadioField('Method', choices=[('upload', 'Upload'), ('download', 'Download')])
