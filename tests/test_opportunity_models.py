# -*- coding: utf-8 -*-
"""Opportunity model tests."""
import datetime as dt

import pytest

from launchpad_os.opportunities.models import (
    Opportunity,
    OpportunityOutreach,
    OpportunityTag,
)

from .factories import (
    OpportunityFactory,
    OpportunityOutreachFactory,
    OpportunityTagFactory,
    UserFactory,
)


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


@pytest.mark.usefixtures("db")
class TestOpportunityOutreach:
    """Opportunity outreach tests."""

    def test_create_outreach_for_opportunity(self):
        """Outreach records belong to a single opportunity."""
        opportunity = OpportunityFactory()
        outreach = OpportunityOutreach.create(
            opportunity=opportunity,
            contact_name="Program Coordinator",
            outreach_status="follow-up due",
        )

        assert outreach.opportunity == opportunity
        assert opportunity.outreach == outreach

    def test_outreach_status_label_is_human_friendly(self):
        """Outreach labels can differ from the stored values."""
        outreach = OpportunityOutreach(outreach_status="follow-up due")

        assert outreach.outreach_status_label == "Follow-up Due"

    def test_outreach_factory(self, db):
        """Test outreach factory."""
        outreach = OpportunityOutreachFactory()
        db.session.commit()

        assert outreach.opportunity_id
        assert outreach.contact_name
        assert outreach.outreach_status == "contacted"


@pytest.mark.usefixtures("db")
class TestOpportunityTag:
    """Opportunity tag tests."""

    def test_tag_belongs_to_user(self):
        """Tags are user-scoped records."""
        user = UserFactory()
        tag = OpportunityTag.create(name="summer 2026", user=user)

        assert tag.user == user
        assert tag in user.opportunity_tags

    def test_tag_factory(self, db):
        """Test opportunity tag factory."""
        tag = OpportunityTagFactory()
        db.session.commit()

        assert tag.name
        assert tag.user_id
