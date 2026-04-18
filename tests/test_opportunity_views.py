# -*- coding: utf-8 -*-
"""Opportunity view tests."""
from flask import url_for

from launchpad_os.opportunities.models import Opportunity

from .factories import (
    MaterialFactory,
    OpportunityFactory,
    RequirementItemFactory,
    UserFactory,
)


def login(testapp, user):
    """Log in a user through the public login form."""
    res = testapp.get(url_for("public.login"))
    form = res.forms["loginForm"]
    form["username"] = user.username
    form["password"] = "myprecious"
    return form.submit().follow()


class TestOpportunityViews:
    """Opportunity view tests."""

    def test_anonymous_user_cannot_access_index(self, testapp):
        """Anonymous users cannot view opportunities."""
        testapp.get(url_for("opportunities.index"), status=401)

    def test_logged_in_user_can_access_index(self, user, testapp):
        """Logged-in users can view their opportunity list."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.index"))

        assert res.status_code == 200
        assert "Opportunities" in res

    def test_workspace_redirects_to_opportunities(self, user, testapp):
        """The old workspace page redirects to the dashboard."""
        login(testapp, user)
        res = testapp.get(url_for("user.members"))

        assert res.status_code == 302
        assert res.location.endswith(url_for("workspace.index"))

    def test_logged_in_user_can_access_new(self, user, testapp):
        """Logged-in users can view the create form."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.new"))

        assert res.status_code == 200
        assert "Add opportunity" in res

    def test_logged_in_user_can_create_opportunity(self, user, testapp):
        """Logged-in users can create an opportunity."""
        old_count = len(Opportunity.query.all())
        login(testapp, user)
        res = testapp.get(url_for("opportunities.new"))
        form = res.forms[0]
        form["title"] = "Campus Research Assistant"
        form["organization"] = "Biology Lab"
        form["category"] = "research"
        form["deadline"] = "2026-05-15"
        form["status"] = "planning"
        form["priority"] = "high"
        form["link"] = "https://example.com/research"
        form["notes"] = "Ask professor about recommendation."

        res = form.submit().follow()

        assert res.status_code == 200
        assert "Opportunity added." in res
        assert "Campus Research Assistant" in res
        assert len(Opportunity.query.all()) == old_count + 1
        opportunity = Opportunity.query.filter_by(
            title="Campus Research Assistant"
        ).one()
        assert opportunity.user == user

    def test_user_only_sees_own_opportunities(self, user, testapp, db):
        """Users only see opportunities connected to their account."""
        other_user = UserFactory(password="myprecious")
        own_opportunity = OpportunityFactory(
            user=user, title="My Internship", organization="My Company"
        )
        other_opportunity = OpportunityFactory(
            user=other_user, title="Other Scholarship", organization="Other Fund"
        )
        db.session.commit()

        login(testapp, user)
        res = testapp.get(url_for("opportunities.index"))

        assert own_opportunity.title in res
        assert other_opportunity.title not in res

    def test_owner_can_view_detail_page(self, user, testapp, db):
        """Owners can view full opportunity details."""
        opportunity = OpportunityFactory(
            user=user,
            title="Research Fellowship",
            organization="Science Center",
            category="research",
            status="planning",
            priority="high",
            link="https://example.com/fellowship",
            notes="Draft essay and request transcript.",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert res.status_code == 200
        assert "Research Fellowship" in res
        assert "Science Center" in res
        assert "Draft essay and request transcript." in res
        assert "https://example.com/fellowship" in res

    def test_non_owner_cannot_view_detail_page(self, user, testapp, db):
        """Users cannot view opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id), status=404
        )

    def test_detail_page_shows_empty_notes_message(self, user, testapp, db):
        """Detail page explains when notes are empty."""
        opportunity = OpportunityFactory(user=user, notes=None)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "No notes yet." in res

    def test_archived_opportunities_are_separated(self, user, testapp, db):
        """Archived opportunities render in the archived section."""
        OpportunityFactory(user=user, title="Active Internship", status="submitted")
        OpportunityFactory(user=user, title="Archived Scholarship", status="archived")
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index"))
        active_section = res.html.select_one("#active-opportunities")
        archived_section = res.html.select_one("#archived-opportunities")

        assert active_section is not None
        assert archived_section is not None
        assert "Active Internship" in active_section.text
        assert "Archived Scholarship" not in active_section.text
        assert "Archived Scholarship" in archived_section.text
        assert "Active Internship" not in archived_section.text

    def test_owner_can_edit_opportunity(self, user, testapp, db):
        """Owners can update their opportunities."""
        opportunity = OpportunityFactory(
            user=user,
            title="Old Title",
            organization="Old Org",
            status="saved",
            priority="low",
        )
        db.session.commit()
        login(testapp, user)
        res = testapp.get(url_for("opportunities.edit", opportunity_id=opportunity.id))
        form = res.forms[0]
        form["title"] = "Updated Internship"
        form["organization"] = "Updated Org"
        form["category"] = "internship"
        form["deadline"] = "2026-06-01"
        form["status"] = "accepted"
        form["priority"] = "high"
        form["link"] = "https://example.com/updated"
        form["notes"] = "Accepted after interview."

        res = form.submit().follow()
        db.session.refresh(opportunity)

        assert res.status_code == 200
        assert "Opportunity updated." in res
        assert opportunity.title == "Updated Internship"
        assert opportunity.organization == "Updated Org"
        assert opportunity.status == "accepted"
        assert opportunity.priority == "high"

    def test_non_owner_cannot_edit_opportunity(self, user, testapp, db):
        """Users cannot edit opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(
            url_for("opportunities.edit", opportunity_id=opportunity.id), status=404
        )

    def test_archive_action_sets_archived_status(self, user, testapp, db):
        """Archive action keeps the row and updates status."""
        opportunity = OpportunityFactory(user=user, status="submitted")
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("opportunities.archive", opportunity_id=opportunity.id)
        ).follow()
        db.session.refresh(opportunity)

        assert res.status_code == 200
        assert "Opportunity archived." in res
        assert opportunity.status == "archived"
        assert Opportunity.get_by_id(opportunity.id) == opportunity

    def test_non_owner_cannot_archive_opportunity(self, user, testapp, db):
        """Users cannot archive opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user, status="submitted")
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("opportunities.archive", opportunity_id=opportunity.id),
            status=404,
        )
        db.session.refresh(opportunity)

        assert opportunity.status == "submitted"

    def test_restore_action_sets_planning_status(self, user, testapp, db):
        """Restore action moves archived opportunities back to planning."""
        opportunity = OpportunityFactory(user=user, status="archived")
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("opportunities.restore", opportunity_id=opportunity.id)
        ).follow()
        db.session.refresh(opportunity)

        assert res.status_code == 200
        assert "Opportunity restored." in res
        assert opportunity.status == "planning"

    def test_non_owner_cannot_restore_opportunity(self, user, testapp, db):
        """Users cannot restore opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user, status="archived")
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("opportunities.restore", opportunity_id=opportunity.id),
            status=404,
        )
        db.session.refresh(opportunity)

        assert opportunity.status == "archived"

    def test_owner_can_link_material_to_opportunity(self, user, testapp, db):
        """Owners can link their saved materials to their opportunities."""
        opportunity = OpportunityFactory(user=user, title="Research Internship")
        material = MaterialFactory(user=user, title="Research Resume")
        db.session.commit()
        login(testapp, user)
        res = testapp.get(
            url_for("opportunities.link_material", opportunity_id=opportunity.id)
        )
        form = res.forms["linkMaterialForm"]
        form["material_id"] = str(material.id)

        res = form.submit().follow()
        db.session.expire_all()
        updated_opportunity = Opportunity.get_by_id(opportunity.id)

        assert res.status_code == 200
        assert "Material linked." in res
        assert "Research Resume" in res
        assert material in updated_opportunity.materials

    def test_owner_can_unlink_material_from_opportunity(self, user, testapp, db):
        """Owners can unlink materials from their opportunities."""
        opportunity = OpportunityFactory(user=user)
        material = MaterialFactory(user=user, title="Essay Notes")
        opportunity.materials.append(material)
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for(
                "opportunities.unlink_material",
                opportunity_id=opportunity.id,
                material_id=material.id,
            )
        ).follow()
        db.session.expire_all()
        updated_opportunity = Opportunity.get_by_id(opportunity.id)

        assert res.status_code == 200
        assert "Material unlinked." in res
        assert material not in updated_opportunity.materials

    def test_non_owner_cannot_link_material_to_opportunity(self, user, testapp, db):
        """Users cannot link materials to opportunities they do not own."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user)
        material = MaterialFactory(user=user)
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for("opportunities.link_material", opportunity_id=opportunity.id),
            {"material_id": material.id},
            status=404,
        )

    def test_user_cannot_link_another_users_material(self, user, testapp, db):
        """Users cannot link another user's materials to their opportunity."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=user)
        material = MaterialFactory(user=other_user, title="Other Resume")
        db.session.commit()
        login(testapp, user)

        res = testapp.post(
            url_for("opportunities.link_material", opportunity_id=opportunity.id),
            {"material_id": material.id},
        )
        db.session.expire_all()
        updated_opportunity = Opportunity.get_by_id(opportunity.id)

        assert res.status_code == 200
        assert material not in updated_opportunity.materials

    def test_non_owner_cannot_unlink_material(self, user, testapp, db):
        """Users cannot unlink materials from another user's opportunity."""
        other_user = UserFactory(password="myprecious")
        opportunity = OpportunityFactory(user=other_user)
        material = MaterialFactory(user=other_user)
        opportunity.materials.append(material)
        db.session.commit()
        login(testapp, user)

        testapp.post(
            url_for(
                "opportunities.unlink_material",
                opportunity_id=opportunity.id,
                material_id=material.id,
            ),
            status=404,
        )
        db.session.expire_all()
        updated_opportunity = Opportunity.get_by_id(opportunity.id)

        assert material in updated_opportunity.materials

    def test_related_materials_appear_on_detail_page(self, user, testapp, db):
        """Opportunity detail shows linked materials."""
        opportunity = OpportunityFactory(user=user, title="Scholarship Application")
        material = MaterialFactory(
            user=user,
            title="Scholarship Essay Draft",
            material_type="essay",
        )
        opportunity.materials.append(material)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Related Materials" in res
        assert "Scholarship Essay Draft" in res
        assert "Essay" in res
        assert url_for("materials.detail", material_id=material.id) in res

    def test_readiness_summary_lists_missing_items(self, user, testapp, db):
        """Opportunity detail summarizes incomplete requirement work."""
        opportunity = OpportunityFactory(user=user)
        RequirementItemFactory(
            opportunity=opportunity,
            title="Upload transcript",
            is_completed=False,
        )
        RequirementItemFactory(
            opportunity=opportunity,
            title="Review resume",
            is_completed=True,
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Next step: complete 1 remaining requirement." in res
        assert "Still needs attention:" in res
        assert "Upload transcript" in res
