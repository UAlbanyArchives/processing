from wtforms import Form, StringField, SelectField, TextAreaField, BooleanField, validators
from wtforms.validators import DataRequired, AnyOf
from forms.custom_validators import validate_packageID, validate_refID

class UploadForm(Form):
    packageID = StringField('Package ID', [validators.Length(min=28, max=32), validate_packageID])
    inputFormat = StringField('Input Path', [validators.Length(min=3, max=3)])
    subPath = StringField('Sub Path', [validators.Length(min=0, max=99)])
    refID = StringField('Ref ID', [validators.Length(min=32, max=32), validate_refID])
    createPDF = BooleanField("Include PDF", default=True)
    content_warning = TextAreaField("Content Warning")

    resource_type = SelectField(
        "Resource Type",
        choices=[
            ("Document", "Document"),
            ("Audio", "Audio"),
            ("Bound Volume", "Bound Volume"),
            ("Dataset", "Dataset"),
            ("Image", "Image"),
            ("Map", "Map"),
            ("Mixed Materials", "Mixed Materials (avoid)"),
            ("Pamphlet", "Pamphlet"),
            ("Periodical", "Periodical"),
            ("Slides", "Slides"),
            ("Video", "Video"),
            ("Other", "Other (avoid)"),
        ],
        validators=[DataRequired(), AnyOf(["Document", "Audio", "Bound Volume", "Dataset", "Image", "Map", "Mixed Materials", "Pamphlet", "Periodical", "Slides", "Video", "Other"])],
    )

    license = SelectField(
        "License",
        choices=[
            ("https://creativecommons.org/licenses/by-nc-sa/4.0/", "CC BY-NC-SA"),
            ("https://creativecommons.org/licenses/by/4.0/", "CC BY"),
            ("https://creativecommons.org/publicdomain/zero/1.0/", "Public Domain"),
            ("Unknown", "Unknown"),
        ],
        validators=[DataRequired(), AnyOf(["https://creativecommons.org/licenses/by-nc-sa/4.0/", "https://creativecommons.org/licenses/by/4.0/", "https://creativecommons.org/publicdomain/zero/1.0/", "Unknown"])],
    )

    rights_statement = SelectField(
        "Rights Statement",
        choices=[
            ("", "None"),
            ("https://rightsstatements.org/page/InC-EDU/1.0/", "In Copyright - Educational Use Permitted"),
        ],
        validators=[AnyOf(["", "https://rightsstatements.org/page/InC-EDU/1.0/"])],
    )

    behavior = SelectField(
        "Behavior",
        choices=[
            ("paged", "paged"),
            ("individuals", "individuals"),
        ],
        validators=[DataRequired(), AnyOf(["paged", "individuals"])],
    )
