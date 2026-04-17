from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_collectionID

class ReindexForm(Form):
    collectionID = StringField('Collection ID', [validators.Length(min=3, max=50), validate_collectionID])
