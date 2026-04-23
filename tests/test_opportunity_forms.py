# -*- coding: utf-8 -*-
"""Opportunity form tests."""

from werkzeug.datastructures import MultiDict

from launchpad_os.opportunities.forms import OpportunityCaptureForm, OpportunityForm


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
            contact_name="Recruiter Name",
            contact_role="University Recruiting",
            contact_method="recruiter@example.com",
            outreach_status="contacted",
            outreach_notes="Initial outreach sent.",
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

    def test_status_choices_use_consistent_display_labels(self, db):
        """Status dropdown uses the polished display labels."""
        form = OpportunityForm()

        assert ("planning", "Preparing") in form.status.choices
        assert ("in progress", "In Progress") in form.status.choices

    def test_validate_accepts_contact_url(self, db):
        """Outreach contact field accepts URLs."""
        form = OpportunityForm(
            formdata=MultiDict(
                {
                    "title": "Example",
                    "organization": "Example Co",
                    "category": "internship",
                    "status": "saved",
                    "priority": "medium",
                    "contact_method": "https://example.com/contact",
                    "outreach_status": "follow-up due",
                }
            )
        )

        assert form.validate() is True

    def test_validate_rejects_invalid_contact_method(self, db):
        """Outreach contact field must be an email or URL."""
        form = OpportunityForm(
            formdata=MultiDict(
                {
                    "title": "Example",
                    "organization": "Example Co",
                    "category": "internship",
                    "status": "saved",
                    "priority": "medium",
                    "contact_method": "call me maybe",
                }
            )
        )

        assert form.validate() is False
        assert "Enter a valid email address or URL." in form.contact_method.errors


class TestOpportunityCaptureForm:
    """Quick capture form tests."""

    def test_validate_accepts_rough_details(self, db):
        """Quick capture can start from notes alone."""
        form = OpportunityCaptureForm(details="Research opening shared by advisor.")

        assert form.validate() is True

    def test_validate_requires_at_least_one_detail(self, db):
        """Quick capture rejects empty submissions."""
        form = OpportunityCaptureForm()

        assert form.validate() is False
        assert (
            "Add at least one detail to capture an opportunity." in form.details.errors
        )
