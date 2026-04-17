# -*- coding: utf-8 -*-
"""Material forms."""
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

from launchpad_os.materials.models import MATERIAL_TYPE_CHOICES


class MaterialForm(FlaskForm):
    """Create or edit a reusable application material."""

    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    material_type = SelectField(
        "Type", choices=MATERIAL_TYPE_CHOICES, validators=[DataRequired()]
    )
    content = TextAreaField("Content", validators=[DataRequired()])
    link = StringField("Link", validators=[Optional(), URL(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])
