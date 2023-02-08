from wtforms import Form, BooleanField, StringField, PasswordField, validators

class IngestForm(Form):
    collectionID = StringField('Collection ID', [validators.Length(min=5, max=9)])
    altPath = StringField('Alternative Path', [validators.Length(min=0, max=35)])
