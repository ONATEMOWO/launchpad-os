# -*- coding: utf-8 -*-
"""Requirement checklist form tests."""

from launchpad_os.requirements.forms import RequirementItemForm


class TestRequirementItemForm:
    """Requirement item form tests."""

    def test_validate_success(self, db):
        """Valid requirement item form."""
        form = RequirementItemForm(
            title="Upload resume",
            is_completed=False,
            notes="Use the one-page version.",
        )

        assert form.validate() is True

    def test_validate_requires_title(self, db):
        """Title is required."""
        form = RequirementItemForm(title="", notes="Missing title.")

        assert form.validate() is False
        assert "This field is required." in form.title.errors

    def test_validate_accepts_completed_flag(self, db):
        """Completed flag can be set on the form."""
        form = RequirementItemForm(title="Request recommendation", is_completed=True)

        assert form.validate() is True
        assert form.is_completed.data is True
