from wtforms import Form, StringField, SelectField, validators
from wtforms.validators import DataRequired, AnyOf
from forms.custom_validators import validate_collectionID_DAO, validate_refID

class RecreateForm(Form):
    collectionID = StringField('Collection ID', [validators.Length(min=5, max=9), validate_collectionID_DAO])
    refID = StringField('Ref ID', [validators.Length(min=32, max=32), validate_refID])
    mode = SelectField(
        "Mode",
        choices=[
            ("thumbnail", "Create Thumbnail"),
            ("ptif", "Create PTIFs"),
            ("ocr", "Recognize Text (OCR)"),
            ("manifest", "Rebuild Manifest"),
        ],
        validators=[DataRequired(), AnyOf(["thumbnail", "ptif", "ocr", "manifest"])],
    )
