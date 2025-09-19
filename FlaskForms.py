from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ScrapeForm(FlaskForm):
    name = StringField('Search for a new item', validators=[DataRequired()])
    submit = SubmitField('Start Scraping')
