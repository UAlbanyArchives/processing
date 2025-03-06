from wtforms import Form, StringField, SelectField, validators
from forms.custom_validators import validate_refID

class AddItemsForm(Form):
    refID = StringField('Ref ID', [validators.Length(min=32, max=32), validate_refID])
    title_1 = StringField('Title 1', [validators.Length(min=3, max=50)])
    display_date_1 = StringField('Display Date 1', [validators.Length(min=4, max=50)])
    normal_date_1 = StringField('Normal Date 1', [validators.Length(min=4, max=21)])
    title_2 = StringField('Title 2', [validators.Length(min=4, max=50)])
    display_date_2 = StringField('Display Date 2', [validators.Length(min=4, max=50)])
    normal_date_2 = StringField('Normal Date 2', [validators.Length(min=4, max=21)])
