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


class OpportunityCaptureForm(FlaskForm):
    """Quick intake form for pre-filling an opportunity."""

    title = StringField("Rough title", validators=[Optional(), Length(max=120)])
    organization = StringField("Organization", validators=[Optional(), Length(max=120)])
    link = StringField("Application link", validators=[Optional(), Length(max=255)])
    deadline_text = StringField(
        "Deadline text or date", validators=[Optional(), Length(max=80)]
    )
    details = TextAreaField("Description or notes", validators=[Optional()])

    def validate(self, extra_validators=None):
        """Require at least one field so the capture step is useful."""
        is_valid = super().validate(extra_validators=extra_validators)
        if not is_valid:
            return False

        has_input = any(
            [
                (self.title.data or "").strip(),
                (self.organization.data or "").strip(),
                (self.link.data or "").strip(),
                (self.deadline_text.data or "").strip(),
                (self.details.data or "").strip(),
            ]
        )
        if has_input:
            return True

        self.details.errors.append("Add at least one detail to capture an opportunity.")
        return False


class MaterialLinkForm(FlaskForm):
    """Link an existing material to an opportunity."""

    material_id = SelectField(
        "Material", coerce=int, validators=[DataRequired()], choices=[]
    )
