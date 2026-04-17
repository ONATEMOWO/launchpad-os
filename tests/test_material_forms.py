# -*- coding: utf-8 -*-
"""Material form tests."""
from werkzeug.datastructures import MultiDict

from launchpad_os.materials.forms import MaterialForm


class TestMaterialForm:
    """Material form tests."""

    def test_validate_success(self, db):
        """Valid material form."""
        form = MaterialForm(
            title="Resume Draft",
            material_type="resume",
            content="Projects, experience, and leadership bullets.",
            link="https://example.com/resume",
            notes="Update after spring research project.",
        )

        assert form.validate() is True

    def test_validate_requires_title(self, db):
        """Title is required."""
        form = MaterialForm(
            title="",
            material_type="resume",
            content="Resume content.",
        )

        assert form.validate() is False
        assert "This field is required." in form.title.errors

    def test_validate_requires_material_type(self, db):
        """Material type is required."""
        form = MaterialForm(
            title="Essay Draft",
            material_type="",
            content="Essay content.",
        )

        assert form.validate() is False
        assert "This field is required." in form.material_type.errors

    def test_validate_rejects_invalid_material_type(self, db):
        """Material type must be one of the configured choices."""
        form = MaterialForm(
            title="Portfolio",
            material_type="portfolio",
            content="Portfolio notes.",
        )

        assert form.validate() is False
        assert "Not a valid choice." in form.material_type.errors

    def test_validate_requires_content(self, db):
        """Content is required."""
        form = MaterialForm(
            title="Recommendation Notes",
            material_type="recommendation",
            content="",
        )

        assert form.validate() is False
        assert "This field is required." in form.content.errors

    def test_validate_rejects_invalid_link(self, db):
        """Link must be a valid URL when present."""
        form = MaterialForm(
            formdata=MultiDict(
                {
                    "title": "Transcript Link",
                    "material_type": "transcript",
                    "content": "Unofficial transcript notes.",
                    "link": "not a url",
                }
            )
        )

        assert form.validate() is False
        assert "Invalid URL." in form.link.errors
