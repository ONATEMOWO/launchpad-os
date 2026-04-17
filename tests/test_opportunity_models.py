# -*- coding: utf-8 -*-
"""Opportunity model tests."""
import datetime as dt

import pytest

from launchpad_os.opportunities.models import Opportunity

from .factories import OpportunityFactory, UserFactory


@pytest.mark.usefixtures("db")
class TestOpportunity:
    """Opportunity tests."""

    def test_create_opportunity_for_user(self):
        """Create an opportunity connected to a user."""
        user = UserFactory()
        opportunity = Opportunity.create(
            title="Summer Research Assistant",
            organization="Campus Lab",
            category="research",
            status="planning",
            priority="high",
            user=user,
        )

        assert opportunity.user == user
        assert opportunity in user.opportunities

    def test_factory(self, db):
        """Test opportunity factory."""
        opportunity = OpportunityFactory()
        db.session.commit()

        assert opportunity.title
        assert opportunity.organization
        assert opportunity.category == "internship"
        assert opportunity.status == "saved"
        assert opportunity.priority == "medium"
        assert opportunity.user_id

    def test_timestamps_default_to_datetime(self):
        """Test creation and update dates."""
        opportunity = OpportunityFactory()
        opportunity.save()

        assert isinstance(opportunity.created_at, dt.datetime)
        assert isinstance(opportunity.updated_at, dt.datetime)

    def test_opportunity_repr(self):
        """Check __repr__ output."""
        opportunity = Opportunity(title="Research Fellowship")

        assert opportunity.__repr__() == "<Opportunity('Research Fellowship')>"

    def test_status_label_uses_student_friendly_wording(self):
        """Status label can differ from the stored value."""
        opportunity = Opportunity(status="planning")

        assert opportunity.status == "planning"
        assert opportunity.status_label == "Preparing"
