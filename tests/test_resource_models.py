# -*- coding: utf-8 -*-
"""Resource hub model tests."""
import datetime as dt

import pytest

from launchpad_os.resources.models import ResourceSource

from .factories import ResourceSourceFactory, UserFactory


@pytest.mark.usefixtures("db")
class TestResourceSource:
    """Resource source tests."""

    def test_create_resource_source_for_user(self):
        """Create a resource source connected to a user."""
        user = UserFactory()
        source = ResourceSource.create(
            name="Campus Research Office",
            category="research",
            url="https://example.edu/research",
            user=user,
        )

        assert source.user == user
        assert source in user.resource_sources

    def test_factory(self, db):
        """Test resource source factory."""
        source = ResourceSourceFactory()
        db.session.commit()

        assert source.name
        assert source.url
        assert source.user_id

    def test_timestamps_default_to_datetime(self):
        """Test creation and update dates."""
        source = ResourceSourceFactory()
        source.save()

        assert isinstance(source.created_at, dt.datetime)
        assert isinstance(source.updated_at, dt.datetime)

    def test_category_label_is_human_friendly(self):
        """Category labels can differ from stored values."""
        source = ResourceSource(category="fellowship")

        assert source.category_label == "Fellowships & programs"
