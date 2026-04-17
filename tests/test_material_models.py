# -*- coding: utf-8 -*-
"""Material model tests."""
import datetime as dt

import pytest

from launchpad_os.materials.models import Material

from .factories import MaterialFactory, UserFactory


@pytest.mark.usefixtures("db")
class TestMaterial:
    """Material tests."""

    def test_create_material_for_user(self):
        """Create a material connected to a user."""
        user = UserFactory()
        material = Material.create(
            title="Resume Draft",
            material_type="resume",
            content="Education, projects, and experience notes.",
            user=user,
        )

        assert material.user == user
        assert material in user.materials

    def test_factory(self, db):
        """Test material factory."""
        material = MaterialFactory()
        db.session.commit()

        assert material.title
        assert material.material_type == "resume"
        assert material.content
        assert material.user_id

    def test_timestamps_default_to_datetime(self):
        """Test creation and update dates."""
        material = MaterialFactory()
        material.save()

        assert isinstance(material.created_at, dt.datetime)
        assert isinstance(material.updated_at, dt.datetime)

    def test_material_repr(self):
        """Check __repr__ output."""
        material = Material(title="Cover Letter Draft")

        assert material.__repr__() == "<Material('Cover Letter Draft')>"
