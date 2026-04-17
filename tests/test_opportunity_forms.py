# -*- coding: utf-8 -*-
"""Opportunity form tests."""

from launchpad_os.opportunities.forms import OpportunityForm


class TestOpportunityForm:
    """Opportunity form tests."""

    def test_validate_success(self, db):
        """Valid opportunity form."""
        form = OpportunityForm(
            title="Software Engineering Internship",
            organization="Example Co",
            category="internship",
            deadline="2026-05-01",
            status="in progress",
            priority="high",
            link="https://example.com/apply",
            notes="Requires resume and short essay.",
        )

        assert form.validate() is True

    def test_validate_requires_title(self, db):
        """Title is required."""
        form = OpportunityForm(
            title="",
            organization="Example Co",
            category="internship",
            status="saved",
            priority="medium",
        )

        assert form.validate() is False
        assert "This field is required." in form.title.errors

    def test_validate_requires_organization(self, db):
        """Organization is required."""
        form = OpportunityForm(
            title="Scholarship Application",
            organization="",
            category="scholarship",
            status="saved",
            priority="medium",
        )

        assert form.validate() is False
        assert "This field is required." in form.organization.errors

    def test_validate_rejects_invalid_category(self, db):
        """Category must be one of the configured choices."""
        form = OpportunityForm(
            title="Example",
            organization="Example Co",
            category="job",
            status="saved",
            priority="medium",
        )

        assert form.validate() is False
        assert "Not a valid choice." in form.category.errors

    def test_validate_rejects_invalid_status(self, db):
        """Status must be one of the configured choices."""
        form = OpportunityForm(
            title="Example",
            organization="Example Co",
            category="internship",
            status="waitlisted",
            priority="medium",
        )

        assert form.validate() is False
        assert "Not a valid choice." in form.status.errors

    def test_validate_accepts_lifecycle_statuses(self, db):
        """Accepted, rejected, and archived are valid statuses."""
        for status in ["accepted", "rejected", "archived"]:
            form = OpportunityForm(
                title="Example",
                organization="Example Co",
                category="internship",
                status=status,
                priority="medium",
            )

            assert form.validate() is True

    def test_validate_rejects_invalid_priority(self, db):
        """Priority must be one of the configured choices."""
        form = OpportunityForm(
            title="Example",
            organization="Example Co",
            category="internship",
            status="saved",
            priority="urgent",
        )

        assert form.validate() is False
        assert "Not a valid choice." in form.priority.errors
