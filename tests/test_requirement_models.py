# -*- coding: utf-8 -*-
"""Requirement checklist model tests."""
import datetime as dt

import pytest

from launchpad_os.requirements.models import RequirementItem

from .factories import OpportunityFactory, RequirementItemFactory


@pytest.mark.usefixtures("db")
class TestRequirementItem:
    """Requirement item tests."""

    def test_create_requirement_for_opportunity(self):
        """Create a requirement connected to an opportunity."""
        opportunity = OpportunityFactory()
        requirement = RequirementItem.create(
            title="Submit transcript",
            notes="Upload unofficial transcript PDF.",
            opportunity=opportunity,
        )

        assert requirement.opportunity == opportunity
        assert requirement in opportunity.requirement_items
        assert requirement.is_completed is False

    def test_factory(self, db):
        """Test requirement item factory."""
        requirement = RequirementItemFactory()
        db.session.commit()

        assert requirement.title
        assert requirement.opportunity_id
        assert requirement.is_completed is False

    def test_timestamps_default_to_datetime(self):
        """Test creation and update dates."""
        requirement = RequirementItemFactory()
        requirement.save()

        assert isinstance(requirement.created_at, dt.datetime)
        assert isinstance(requirement.updated_at, dt.datetime)

    def test_requirement_repr(self):
        """Check __repr__ output."""
        requirement = RequirementItem(title="Recommendation request")

        assert requirement.__repr__() == "<RequirementItem('Recommendation request')>"
