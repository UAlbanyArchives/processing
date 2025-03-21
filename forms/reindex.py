from wtforms import Form, BooleanField, StringField, validators
from forms.custom_validators import validate_collectionID

class ReindexForm(Form):
    collectionID = StringField('Collection ID', [validators.Length(min=5, max=9), validate_collectionID])
