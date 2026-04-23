# -*- coding: utf-8 -*-
"""Workspace dashboard view tests."""
import datetime as dt

from flask import url_for

from .factories import (
    MaterialFactory,
    OpportunityFactory,
    OpportunityOutreachFactory,
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


class TestWorkspaceViews:
    """Workspace dashboard tests."""

    def test_anonymous_user_cannot_access_workspace(self, testapp):
        """Anonymous users cannot view the workspace dashboard."""
        testapp.get(url_for("workspace.index"), status=401)

    def test_authenticated_user_can_access_workspace(self, user, testapp):
        """Logged-in users can view the workspace dashboard."""
        login(testapp, user)
        res = testapp.get(url_for("workspace.index"))

        assert res.status_code == 200
        assert "Application Workspace" in res
        assert "Active opportunity progress" in res
        assert "This week priorities" in res
        assert "Readiness snapshot" in res

    def test_login_redirects_to_workspace(self, user, testapp):
        """Default login destination is the workspace dashboard."""
        res = testapp.get(url_for("public.login"))
        form = res.forms["loginForm"]
        form["username"] = user.username
        form["password"] = "myprecious"

        res = form.submit()

        assert res.status_code == 302
        assert res.location.endswith(url_for("workspace.index"))

    def test_workspace_only_shows_current_users_data(self, user, testapp, db):
        """Dashboard summaries and lists are scoped to the current user."""
        today = dt.date.today()
        other_user = UserFactory(password="myprecious")
        own_opportunity = OpportunityFactory(
            user=user,
            title="My Internship",
            organization="My Company",
            deadline=today + dt.timedelta(days=7),
            status="planning",
        )
        archived_opportunity = OpportunityFactory(
            user=user,
            title="My Archived Scholarship",
            status="archived",
        )
        other_opportunity = OpportunityFactory(
            user=other_user,
            title="Other User Internship",
            organization="Other Company",
            deadline=today + dt.timedelta(days=3),
            status="planning",
        )
        MaterialFactory(user=user, title="My Resume")
        MaterialFactory(user=other_user, title="Other Resume")
        RequirementItemFactory(
            opportunity=own_opportunity, title="Draft essay", is_completed=False
        )
        RequirementItemFactory(
            opportunity=other_opportunity,
            title="Other user requirement",
            is_completed=False,
        )
        db.session.commit()

        login(testapp, user)
        res = testapp.get(url_for("workspace.index"))

        assert res.html.select_one("#activeOpportunitiesCount").text.strip() == "1"
        assert res.html.select_one("#archivedOpportunitiesCount").text.strip() == "1"
        assert res.html.select_one("#materialsCount").text.strip() == "1"
        assert res.html.select_one("#incompleteOpportunitiesCount").text.strip() == "1"
        assert own_opportunity.title in res
        assert archived_opportunity.title not in res
        assert other_opportunity.title not in res
        assert "Other Resume" not in res
        assert "Other user requirement" not in res

    def test_workspace_shows_due_soon_and_checklist_work(self, user, testapp, db):
        """Dashboard digest and progress grid surface due-soon and checklist data."""
        today = dt.date.today()
        opportunity = OpportunityFactory(
            user=user,
            title="Research Fellowship",
            organization="Campus Lab",
            deadline=today + dt.timedelta(days=10),
            status="in progress",
        )
        RequirementItemFactory(
            opportunity=opportunity, title="Resume", is_completed=True
        )
        RequirementItemFactory(
            opportunity=opportunity, title="Research statement", is_completed=False
        )
        db.session.commit()

        login(testapp, user)
        res = testapp.get(url_for("workspace.index"))
        digest_due_soon = res.html.select_one("#digestDueSoon")
        progress_section = res.html.select_one("#activeProgressSection")

        assert digest_due_soon is not None
        assert progress_section is not None
        assert "Research Fellowship" in digest_due_soon.text
        assert "Due in 10 days" in digest_due_soon.text
        assert "1 of 2 requirements" in progress_section.text
        assert "50%" in progress_section.text

    def test_workspace_basic_summary_sections_present(self, user, testapp):
        """Dashboard renders its major summary sections for empty accounts."""
        login(testapp, user)
        res = testapp.get(url_for("workspace.index"))

        assert "What needs attention next" in res
        assert "Action Digest" in res
        assert "No active opportunities yet." in res
        assert "Add opportunity" in res
        assert "Open materials vault" in res
        assert "No urgent priorities right now." in res

    def test_workspace_action_digest_surfaces_key_attention_items(
        self, user, testapp, db
    ):
        """Dashboard digest highlights overdue, due-soon, low-readiness, and follow-up work."""
        today = dt.date.today()
        OpportunityFactory(
            user=user,
            title="Overdue Application",
            deadline=today - dt.timedelta(days=2),
            priority="medium",
        )
        due_soon = OpportunityFactory(
            user=user,
            title="Due Soon Application",
            deadline=today + dt.timedelta(days=7),
            priority="medium",
        )
        high_priority = OpportunityFactory(
            user=user,
            title="High Priority Application",
            deadline=today + dt.timedelta(days=20),
            priority="high",
        )
        follow_up = OpportunityFactory(
            user=user,
            title="Follow-up Opportunity",
            deadline=today + dt.timedelta(days=12),
        )
        RequirementItemFactory(
            opportunity=due_soon,
            title="Resume review",
            is_completed=False,
        )
        RequirementItemFactory(
            opportunity=high_priority,
            title="Draft essay",
            is_completed=False,
        )
        OpportunityOutreachFactory(
            opportunity=follow_up,
            outreach_status="follow-up due",
            contact_name="Program Advisor",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("workspace.index"))
        digest_section = res.html.select_one("#actionDigestSection")
        missing_checklist_section = res.html.select_one("#digestMissingChecklist")
        missing_materials_section = res.html.select_one("#digestMissingMaterials")

        assert digest_section is not None
        assert missing_checklist_section is not None
        assert missing_materials_section is not None
        assert "Overdue Application" in digest_section.text
        assert "Due Soon Application" in digest_section.text
        assert "High Priority Application" in digest_section.text
        assert "Follow-up Opportunity" in digest_section.text
        assert "Generate or add a starter checklist." in missing_checklist_section.text
        assert (
            "Link supporting materials from the vault."
            in missing_materials_section.text
        )
        assert "Review now" in digest_section.text

    def test_workspace_hero_surfaces_readiness_snapshot_and_priority_counts(
        self, user, testapp, db
    ):
        """Hero panels surface readiness distribution and setup gaps."""
        today = dt.date.today()
        ready = OpportunityFactory(
            user=user,
            title="Ready Application",
            deadline=today + dt.timedelta(days=20),
        )
        in_progress = OpportunityFactory(
            user=user,
            title="In Progress Application",
            deadline=today + dt.timedelta(days=14),
        )
        OpportunityFactory(user=user, title="Needs Setup Application")
        RequirementItemFactory(
            opportunity=ready,
            title="Resume",
            is_completed=True,
        )
        RequirementItemFactory(
            opportunity=ready,
            title="Essay",
            is_completed=True,
        )
        ready.materials.append(MaterialFactory(user=user, title="Ready Resume"))
        RequirementItemFactory(
            opportunity=in_progress,
            title="Statement draft",
            is_completed=False,
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("workspace.index"))

        assert "Ready to review" in res
        assert "Needs setup" in res
        assert "missing checklist" in res
        assert "missing materials" in res
