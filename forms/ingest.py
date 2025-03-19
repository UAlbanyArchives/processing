from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_collectionID_ingest

class IngestForm(Form):
    collectionID = StringField('Collection ID', [validators.Length(min=5, max=9), validate_collectionID_ingest])
    #altPath = StringField('Alternative Path', [validators.Length(min=0, max=35)])
