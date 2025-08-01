import os
from pathlib import PureWindowsPath, PurePosixPath
from wtforms import Form, StringField, validators
from wtforms.validators import ValidationError
from forms.custom_validators import validate_packageID

BACKLOG = "/backlog"

def validate_sheetFile(form, field):
    sheet_arg = field.data.strip()
    packageID = form.packageID.data.strip() if form.packageID.data else ""

    if not packageID:
        raise ValidationError("Package ID is required before validating the sheet file.")

    # Require .xlsx extension (case-insensitive)
    if not sheet_arg.lower().endswith(".xlsx"):
        raise ValidationError("Sheet filename must end with .xlsx")

    # Normalize Windows or POSIX style paths
    if "\\" in sheet_arg:
        win_path = PureWindowsPath(sheet_arg)
        sheet_rel = PurePosixPath(*win_path.parts)
    else:
        sheet_rel = os.path.normpath(sheet_arg)

    # Build paths
    col_ID = packageID.split("_")[0]
    package_path = os.path.join(BACKLOG, col_ID, packageID)
    metadata_path = os.path.join(package_path, "metadata")
    candidate_path = os.path.normpath(os.path.join(metadata_path, sheet_rel))

    # Ensure the final path is still under metadata_path
    if not candidate_path.startswith(os.path.abspath(metadata_path)):
        raise ValidationError(f"Invalid path: must be within {metadata_path}.")

    # Ensure the file exists
    if not os.path.isfile(candidate_path):
        raise ValidationError(f"File '{sheet_rel}' not found in '{metadata_path}'.")

class BulkForm(Form):
    packageID = StringField('Package ID', [
        validators.Length(min=28, max=32),
        validate_packageID
    ])
    sheetFile = StringField('Sheet filename', [
        validators.Length(min=5, max=255),
        validate_sheetFile
    ])
