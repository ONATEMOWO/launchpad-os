# -*- coding: utf-8 -*-
"""Requirement checklist forms."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class RequirementItemForm(FlaskForm):
    """Create or edit an opportunity checklist item."""

    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    is_completed = BooleanField("Completed")
    notes = TextAreaField("Notes", validators=[Optional()])
