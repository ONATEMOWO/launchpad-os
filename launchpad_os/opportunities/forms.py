# -*- coding: utf-8 -*-
"""Opportunity forms."""
import re

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    HiddenField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import URL, DataRequired, Length, Optional, ValidationError

from launchpad_os.opportunities.models import (
    CATEGORY_CHOICES,
    OUTREACH_STATUS_CHOICES,
    PRIORITY_CHOICES,
    STATUS_CHOICES,
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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
    tags = StringField("Tags", validators=[Optional(), Length(max=255)])
    contact_name = StringField("Contact name", validators=[Optional(), Length(max=120)])
    contact_role = StringField(
        "Contact role or office", validators=[Optional(), Length(max=120)]
    )
    contact_method = StringField(
        "Contact email or URL", validators=[Optional(), Length(max=255)]
    )
    outreach_status = SelectField(
        "Outreach status",
        choices=OUTREACH_STATUS_CHOICES,
        default="not contacted",
        validators=[DataRequired()],
    )
    outreach_notes = TextAreaField("Outreach notes", validators=[Optional()])
    create_suggested_checklist = BooleanField("Create suggested checklist")
    suggested_checklist_items = HiddenField()
    link = StringField("Link", validators=[Optional(), URL(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])

    def validate_contact_method(self, field):
        """Allow either an email address or an HTTP(S) URL."""
        value = (field.data or "").strip()
        if not value:
            return

        if value.startswith(("http://", "https://")):
            validator = URL()
            validator(self, field)
            return

        if EMAIL_PATTERN.match(value):
            return

        raise ValidationError("Enter a valid email address or URL.")


class OpportunityCaptureForm(FlaskForm):
    """Quick intake form for pre-filling an opportunity."""

    title = StringField("Rough title", validators=[Optional(), Length(max=120)])
    organization = StringField("Organization", validators=[Optional(), Length(max=120)])
    link = StringField("Application link", validators=[Optional(), Length(max=255)])
    deadline_text = StringField(
        "Deadline text or date", validators=[Optional(), Length(max=80)]
    )
    details = TextAreaField("Description or notes", validators=[Optional()])
    use_ai = BooleanField("Use AI suggestions if available", default=False)

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
