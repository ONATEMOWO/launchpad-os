# -*- coding: utf-8 -*-
"""Resource hub forms."""
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

from launchpad_os.resources.models import RESOURCE_CATEGORY_CHOICES


class ResourceSourceForm(FlaskForm):
    """Save a personal resource source link."""

    name = StringField("Source name", validators=[DataRequired(), Length(max=120)])
    category = SelectField(
        "Category", choices=RESOURCE_CATEGORY_CHOICES, validators=[DataRequired()]
    )
    url = StringField("URL", validators=[DataRequired(), URL(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])
