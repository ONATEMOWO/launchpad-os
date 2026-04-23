# -*- coding: utf-8 -*-
"""Resource hub form tests."""

from launchpad_os.resources.forms import ResourceSourceForm


class TestResourceSourceForm:
    """Resource source form tests."""

    def test_validate_success(self, db):
        """Valid personal resource source form."""
        form = ResourceSourceForm(
            name="Campus Fellowship Office",
            category="fellowship",
            url="https://example.edu/fellowships",
            notes="Check monthly for program updates.",
        )

        assert form.validate() is True

    def test_validate_requires_name(self, db):
        """Source name is required."""
        form = ResourceSourceForm(
            name="",
            category="research",
            url="https://example.edu/research",
        )

        assert form.validate() is False
        assert "This field is required." in form.name.errors
