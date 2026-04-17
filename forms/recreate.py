from wtforms import Form, StringField, SelectField, validators
from wtforms.validators import DataRequired, AnyOf
from forms.custom_validators import validate_refID_recreate

class RecreateForm(Form):
    refID = StringField('Ref ID', [validators.Length(min=3, max=128), validate_refID_recreate])
    mode = SelectField(
        "Mode",
        choices=[
            ("manifest", "Rebuild Manifest"),
            ("thumbnail", "Create Thumbnail"),
            ("pdf", "Create PDF"),
            ("ptif", "Create PTIFs"),
            ("ocr", "Recognize Text (OCR)"),
            ("index", "Index OCR text (for content search)"),
            ("transcribe", "Transcribe AV"),
            ("all", "Rebuild Entire IIIF Object"),
            ("all-no-pdf", "Rebuild Entire IIIF Object (skipping PDF)"),
        ],
        validators=[DataRequired(), AnyOf(["thumbnail", "ptif", "ocr", "manifest", "pdf", "index", "transcribe", "all", "all-no-pdf"])],
    )
