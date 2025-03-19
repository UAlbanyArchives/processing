from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_collectionID_ingest, validate_accessionID

class AccessionForm(Form):
    accessionID = StringField('Accession ID', [validators.Length(min=8, max=8), validate_accessionID])
    collectionID = StringField('Collection ID', [validators.Length(min=5, max=9), validate_collectionID_ingest])
    #altPath = StringField('Alternative Path', [validators.Length(min=0, max=35)])
