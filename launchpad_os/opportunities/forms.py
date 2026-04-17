# -*- coding: utf-8 -*-
"""Opportunity forms."""
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional

from launchpad_os.opportunities.models import (
    CATEGORY_CHOICES,
    PRIORITY_CHOICES,
    STATUS_CHOICES,
)


class OpportunityForm(FlaskForm):
    """Create opportunity form."""

    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    organization = StringField(
        "Organization", validators=[DataRequired(), Length(max=120)]
    )
    category = SelectField(
        "Category", choices=CATEGORY_CHOICES, validators=[DataRequired()]
    )
    deadline = DateField("Deadline", validators=[Optional()])
    status = SelectField(
        "Status", choices=STATUS_CHOICES, default="saved", validators=[DataRequired()]
    )
    priority = SelectField(
        "Priority",
        choices=PRIORITY_CHOICES,
        default="medium",
        validators=[DataRequired()],
    )
    link = StringField("Link", validators=[Optional(), URL(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])
