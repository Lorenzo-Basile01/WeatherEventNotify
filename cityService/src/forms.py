from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, FieldList,FormField
from wtforms.validators import DataRequired, Optional


class ConstraintForm(FlaskForm):
    city_name = StringField('City Name', validators=[DataRequired()])
    max_temp = IntegerField('Max Temperature', validators=[Optional()])
    min_temp = IntegerField('Min Temperature', validators=[Optional()])
    rain = BooleanField('Rain', validators=[Optional()])
    snow = BooleanField('Snow', validators=[Optional()])

    submit = SubmitField('Submit')


class SubscriptionForm(FlaskForm):
    cities = FieldList(FormField(ConstraintForm), min_entries=1)
    submit = SubmitField('Submit')