# -*- coding: utf-8 -*-
"""Requirement checklist view tests."""
import pytest
from flask import url_for

from launchpad_os.requirements.models import RequirementItem
from launchpad_os.requirements.views import CHECKLIST_TEMPLATES

from .factories import OpportunityFactory, RequirementItemFactory, UserFactory


def login(testapp, user):
    """Log in a user through the public login form."""
    res = testapp.get(url_for("public.login"))
    form = res.forms["loginForm"]
    form["username"] = user.username
    form["password"] = "myprecious"
    return form.submit().follow()


class TestRequirementViews:
    """Requirement checklist view tests."""

    def test_anonymous_user_cannot_access_new(self, testapp, db):
        """Anonymous users cannot add requirement items."""
        opportunity = OpportunityFactory()
        db.session.commit()

        testapp.get(
            url_for("requirements.new", opportunity_id=opportunity.id), status=401
        )

    def test_owner_can_add_requirement_item(self, user, testapp, db):
        """Owners can add requirement items to their opportunities."""
        opportunity = OpportunityFactory(user=user, title="Research Application")
        db.session.commit()
        old_count = len(RequirementItem.query.all())
        login(testapp, user)
        res = testapp.get(url_for("requirements.new", opportunity_id=opportunity.id))
        form = res.forms[0]
        form["title"] = "Upload resume"
        form["notes"] = "Use the research version."

        res = form.submit().follow()

        assert res.status_code == 200
        assert "Requirement item added." in res
        assert "Upload resume" in res
        assert "Use the research version." in res
        assert len(RequirementItem.query.all()) == old_count + 1
        requirement = RequirementItem.query.filter_by(title="Upload resume").one()
        assert requirement.opportunity == opportunity

    def test_non_owner_cannot_add_requirement_item(self, user, testapp, db):
        """Users cannot add requirements to opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(
            url_for("requirements.new", opportunity_id=opportunity.id), status=404
        )

    def test_owner_can_edit_requirement_item(self, user, testapp, db):
        """Owners can edit their requirement items."""
        opportunity = OpportunityFactory(user=user)
        requirement = RequirementItemFactory(
            opportunity=opportunity,
            title="Old requirement",
            notes="Old notes.",
            is_completed=False,
        )
        db.session.commit()
        login(testapp, user)
        res = testapp.get(url_for("requirements.edit", requirement_id=requirement.id))
        form = res.forms[0]
        form["title"] = "Updated requirement"
        form["notes"] = "Updated notes."
        form["is_completed"].checked = True

        res = form.submit().follow()
        db.session.refresh(requirement)

        assert res.status_code == 200
        assert "Requirement item updated." in res
        assert requirement.title == "Updated requirement"
        assert requirement.notes == "Updated notes."
        assert requirement.is_completed is True

    def test_non_owner_cannot_edit_requirement_item(self, user, testapp, db):
        """Users cannot edit another user's requirement items."""
        other_user = UserFactory(password="myprecious")
        requirement = RequirementItemFactory(opportunity__user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(
            url_for("requirements.edit", requirement_id=requirement.id), status=404
        )

    def test_owner_can_toggle_requirement_item(self, user, testapp, db):
        """Owners can toggle requirement completion."""
        requirement = RequirementItemFactory(opportunity__user=user, is_completed=False)
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("requirements.toggle", requirement_id=requirement.id)
        ).follow()
        db.session.refresh(requirement)

        assert res.status_code == 200
        assert "Requirement marked complete." in res
        assert requirement.is_completed is True

        res = testapp.post(
            url_for("requirements.toggle", requirement_id=requirement.id)
        ).follow()
        db.session.refresh(requirement)

        assert "Requirement marked incomplete." in res
        assert requirement.is_completed is False

    def test_non_owner_cannot_toggle_requirement_item(self, user, testapp, db):
        """Users cannot toggle another user's requirement items."""
        other_user = UserFactory(password="myprecious")
        requirement = RequirementItemFactory(
            opportunity__user=other_user, is_completed=False
        )
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("requirements.toggle", requirement_id=requirement.id),
            status=404,
        )
        db.session.refresh(requirement)

        assert requirement.is_completed is False

    def test_owner_can_delete_requirement_item(self, user, testapp, db):
        """Owners can delete requirement items."""
        requirement = RequirementItemFactory(opportunity__user=user)
        db.session.commit()
        requirement_id = requirement.id
        login(testapp, user)

        res = testapp.post(
            url_for("requirements.delete", requirement_id=requirement.id)
        ).follow()

        assert res.status_code == 200
        assert "Requirement item deleted." in res
        assert RequirementItem.get_by_id(requirement_id) is None

    def test_non_owner_cannot_delete_requirement_item(self, user, testapp, db):
        """Users cannot delete another user's requirement items."""
        other_user = UserFactory(password="myprecious")
        requirement = RequirementItemFactory(opportunity__user=other_user)
        db.session.commit()
        requirement_id = requirement.id
        login(testapp, user)

        testapp.post(
            url_for("requirements.delete", requirement_id=requirement.id),
            status=404,
        )

        assert RequirementItem.get_by_id(requirement_id) == requirement

    def test_checklist_items_appear_on_opportunity_detail(self, user, testapp, db):
        """Opportunity detail page shows checklist items."""
        opportunity = OpportunityFactory(user=user, title="Scholarship Application")
        RequirementItemFactory(
            opportunity=opportunity,
            title="Draft essay",
            notes="Write first draft before advisor meeting.",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Requirement Checklist" in res
        assert "Draft essay" in res
        assert "Write first draft before advisor meeting." in res

    def test_completion_summary_counts_completed_items(self, user, testapp, db):
        """Opportunity detail page summarizes checklist completion."""
        opportunity = OpportunityFactory(user=user)
        RequirementItemFactory(
            opportunity=opportunity, title="Resume", is_completed=True
        )
        RequirementItemFactory(
            opportunity=opportunity, title="Essay", is_completed=True
        )
        RequirementItemFactory(
            opportunity=opportunity, title="Transcript", is_completed=False
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "2 of 3 complete" in res
        assert "67%" in res

    def test_empty_checklist_summary_is_zero(self, user, testapp, db):
        """Opportunity detail page handles opportunities without requirements."""
        opportunity = OpportunityFactory(user=user)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "0 of 0 complete" in res
        assert "No requirements yet." in res

    def test_owner_can_generate_template_checklist_items(self, user, testapp, db):
        """Owners can generate starter checklist items."""
        opportunity = OpportunityFactory(user=user, category="internship")
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("requirements.generate_template", opportunity_id=opportunity.id)
        ).follow()

        assert res.status_code == 200
        assert "Added 5 starter checklist item(s)." in res
        for title in CHECKLIST_TEMPLATES["internship"]:
            assert title in res

    def test_non_owner_cannot_generate_template_checklist_items(
        self, user, testapp, db
    ):
        """Users cannot generate checklist items for opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user, category="scholarship")
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("requirements.generate_template", opportunity_id=opportunity.id),
            status=404,
        )

        assert (
            RequirementItem.query.filter_by(opportunity_id=opportunity.id).count() == 0
        )

    def test_template_generation_does_not_duplicate_existing_titles(
        self, user, testapp, db
    ):
        """Generating a template only adds missing titles."""
        opportunity = OpportunityFactory(user=user, category="internship")
        RequirementItemFactory(
            opportunity=opportunity,
            title="Update resume",
        )
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("requirements.generate_template", opportunity_id=opportunity.id)
        ).follow()
        testapp.post(
            url_for("requirements.generate_template", opportunity_id=opportunity.id)
        ).follow()

        requirements = RequirementItem.query.filter_by(
            opportunity_id=opportunity.id
        ).all()
        titles = [requirement.title for requirement in requirements]

        assert len(requirements) == 5
        assert titles.count("Update resume") == 1

    @pytest.mark.parametrize(
        ("category", "expected_title"),
        [
            ("internship", "Prepare portfolio or GitHub link"),
            ("scholarship", "Request recommendation"),
            ("research", "Draft outreach email"),
        ],
    )
    def test_correct_template_is_used_for_opportunity_category(
        self, user, testapp, db, category, expected_title
    ):
        """Generated items come from the opportunity category template."""
        opportunity = OpportunityFactory(user=user, category=category)
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("requirements.generate_template", opportunity_id=opportunity.id)
        ).follow()

        assert expected_title in res
