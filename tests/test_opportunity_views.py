# -*- coding: utf-8 -*-
"""Opportunity view tests."""
import datetime as dt

from flask import url_for

from launchpad_os.opportunities.models import Opportunity

from .factories import (
    MaterialFactory,
    OpportunityFactory,
    OpportunityOutreachFactory,
    OpportunityTagFactory,
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

    def test_anonymous_user_cannot_access_capture(self, testapp):
        """Anonymous users cannot access quick capture."""
        testapp.get(url_for("opportunities.capture"), status=401)

    def test_anonymous_user_cannot_export_opportunities(self, testapp):
        """Anonymous users cannot export opportunity data."""
        testapp.get(url_for("opportunities.export"), status=401)

    def test_logged_in_user_can_access_index(self, user, testapp):
        """Logged-in users can view their opportunity list."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.index"))

        assert res.status_code == 200
        assert "Opportunities" in res
        assert "Smart views" in res
        assert "Use smart views for recurring attention patterns" in res

    def test_logged_in_user_can_access_capture(self, user, testapp):
        """Logged-in users can open quick capture."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))

        assert res.status_code == 200
        assert "Capture opportunity" in res
        assert "Quick Capture" in res

    def test_capture_prefills_from_query_params(self, user, testapp):
        """Quick Capture accepts clipper-style prefill query parameters."""
        login(testapp, user)
        res = testapp.get(
            url_for(
                "opportunities.capture",
                source="clipper",
                title="Research Lab Opening",
                url="https://example.com/lab",
                selected_text="Faculty lab opening with transcript requirement.",
            )
        )
        form = res.forms["quickCaptureForm"]

        assert "Browser clipper details were prefilled" in res
        assert form["title"].value == "Research Lab Opening"
        assert form["link"].value == "https://example.com/lab"
        assert "transcript requirement" in form["details"].value

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

    def test_logged_in_user_can_quick_capture_and_create_opportunity(
        self, user, testapp
    ):
        """Quick capture pre-fills the form and creates an opportunity."""
        old_count = len(Opportunity.query.all())
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["title"] = "Summer Research Fellowship"
        form["organization"] = "Campus Lab"
        form["details"] = "Shared by faculty advisor."

        review = form.submit()

        assert review.status_code == 200
        assert "Review captured opportunity" in review

        save_form = review.forms["opportunityForm"]
        res = save_form.submit().follow()

        assert res.status_code == 200
        assert "Opportunity added." in res
        assert "Summer Research Fellowship" in res
        assert len(Opportunity.query.all()) == old_count + 1

    def test_quick_capture_saves_pasted_url_as_link(self, user, testapp):
        """A pasted URL is saved as the opportunity link."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["title"] = "Scholarship Packet"
        form["organization"] = "Example Foundation"
        form["details"] = "Application page: https://example.com/scholarship/apply"

        review = form.submit()
        save_form = review.forms["opportunityForm"]
        res = save_form.submit().follow()

        opportunity = Opportunity.query.filter_by(title="Scholarship Packet").one()

        assert opportunity.link == "https://example.com/scholarship/apply"
        assert "https://example.com/scholarship/apply" in res

    def test_quick_capture_saves_longer_description_as_notes(self, user, testapp):
        """Longer capture details carry into opportunity notes."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["title"] = "Policy Internship"
        form["organization"] = "City Office"
        form["details"] = (
            "Paid summer role with writing sample requirement and supervisor email."
        )

        review = form.submit()
        save_form = review.forms["opportunityForm"]
        res = save_form.submit().follow()

        opportunity = Opportunity.query.filter_by(title="Policy Internship").one()

        expected_notes = (
            "Paid summer role with writing sample requirement and supervisor email."
        )

        assert opportunity.notes == expected_notes
        assert "writing sample requirement" in res

    def test_quick_capture_created_opportunity_belongs_to_current_user(
        self, user, testapp
    ):
        """Quick capture creates an owned opportunity."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["title"] = "Design Fellowship"
        form["organization"] = "Innovation Studio"

        review = form.submit()
        save_form = review.forms["opportunityForm"]
        save_form.submit().follow()

        opportunity = Opportunity.query.filter_by(title="Design Fellowship").one()

        assert opportunity.user == user

    def test_ai_capture_falls_back_to_standard_review_when_unconfigured(
        self, user, testapp
    ):
        """AI-assisted capture falls back cleanly when no provider is configured."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["title"] = "Scholarship Packet"
        form["details"] = "Merit scholarship with essay requirement."
        form["use_ai"] = True

        review = form.submit()

        assert review.status_code == 200
        assert (
            "AI suggestions are not configured in this environment yet, "
            "so LaunchPad OS used the standard Quick Capture prefill." in review
        )
        assert "Review captured opportunity" in review

    def test_ai_capture_can_create_suggested_checklist(
        self, user, testapp, monkeypatch
    ):
        """AI-assisted capture can prefill the review form and seed checklist items."""

        def fake_ai_suggestions(app, capture_text):
            return {
                "used_ai": True,
                "title": "AI Suggested Fellowship",
                "organization": "Campus Innovation Office",
                "category": "research",
                "deadline_text": "2026-06-10",
                "summary": "Research fellowship focused on student innovation work.",
                "checklist_items": ["Update resume", "Draft personal statement"],
                "tags": ["innovation", "summer 2026"],
                "reason": "AI suggestions are ready to review before you save.",
            }

        monkeypatch.setattr(
            "launchpad_os.opportunities.views.request_ai_capture_suggestions",
            fake_ai_suggestions,
        )

        login(testapp, user)
        res = testapp.get(url_for("opportunities.capture"))
        form = res.forms["quickCaptureForm"]
        form["details"] = "Rough fellowship note."
        form["use_ai"] = True

        review = form.submit()

        assert "AI Suggested Fellowship" in review
        assert "AI suggestions" in review
        assert "Suggested organization" in review
        assert "Suggested category" in review
        assert "Research fellowship focused on student innovation work." in review
        assert "Update resume" in review
        assert "#innovation" in review

        save_form = review.forms["opportunityForm"]
        assert save_form["tags"].value == "innovation, summer 2026"
        save_form["create_suggested_checklist"] = True
        save_form.submit().follow()

        opportunity = Opportunity.query.filter_by(title="AI Suggested Fellowship").one()

        assert opportunity.organization == "Campus Innovation Office"
        assert opportunity.category == "research"
        assert {item.title for item in opportunity.requirement_items} == {
            "Update resume",
            "Draft personal statement",
        }

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

    def test_search_opportunities_by_title(self, user, testapp, db):
        """Users can search opportunities by title."""
        matching = OpportunityFactory(
            user=user, title="Amazon Software Internship", organization="AWS"
        )
        other = OpportunityFactory(
            user=user, title="Campus Writing Award", organization="English Department"
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", q="amazon"))

        assert matching.title in res
        assert other.title not in res

    def test_search_opportunities_by_organization(self, user, testapp, db):
        """Users can search opportunities by organization."""
        matching = OpportunityFactory(
            user=user, title="Cloud Program", organization="Amazon"
        )
        other = OpportunityFactory(
            user=user, title="Policy Fellowship", organization="City Office"
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", q="amazon"))

        assert matching.title in res
        assert other.title not in res

    def test_filter_opportunities_by_status(self, user, testapp, db):
        """Users can filter opportunities by status."""
        matching = OpportunityFactory(
            user=user, title="Submitted Fellowship", status="submitted"
        )
        other = OpportunityFactory(user=user, title="Saved Fellowship", status="saved")
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", status="submitted"))

        assert matching.title in res
        assert other.title not in res

    def test_filter_opportunities_by_category(self, user, testapp, db):
        """Users can filter opportunities by category."""
        matching = OpportunityFactory(
            user=user, title="Scholarship Match", category="scholarship"
        )
        other = OpportunityFactory(
            user=user, title="Internship Match", category="internship"
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", category="scholarship"))

        assert matching.title in res
        assert other.title not in res

    def test_filter_opportunities_by_priority(self, user, testapp, db):
        """Users can filter opportunities by priority."""
        matching = OpportunityFactory(user=user, title="Urgent Role", priority="high")
        other = OpportunityFactory(user=user, title="Later Role", priority="low")
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", priority="high"))

        assert matching.title in res
        assert other.title not in res

    def test_filter_opportunities_by_tag(self, user, testapp, db):
        """Users can filter opportunities by custom tag."""
        tag = OpportunityTagFactory(user=user, name="summer 2026")
        matching = OpportunityFactory(user=user, title="Tagged Fellowship")
        other = OpportunityFactory(user=user, title="Untagged Fellowship")
        matching.tags.append(tag)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", tag="summer 2026"))

        assert matching.title in res
        assert other.title not in res

    def test_smart_view_missing_materials_filters_results(self, user, testapp, db):
        """Smart views can isolate opportunities missing linked materials."""
        missing_materials = OpportunityFactory(user=user, title="Needs Materials")
        ready = OpportunityFactory(user=user, title="Has Materials")
        ready.materials.append(MaterialFactory(user=user, title="Resume"))
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", view="missing_materials"))

        assert missing_materials.title in res
        assert ready.title not in res

    def test_smart_view_follow_up_due_filters_results(self, user, testapp, db):
        """Smart views can isolate opportunities with outreach follow-up due."""
        follow_up = OpportunityFactory(user=user, title="Needs Follow-up")
        OpportunityOutreachFactory(
            opportunity=follow_up,
            outreach_status="follow-up due",
        )
        other = OpportunityFactory(user=user, title="No Follow-up")
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", view="follow_up_due"))

        assert follow_up.title in res
        assert other.title not in res

    def test_filtered_opportunities_remain_user_scoped(self, user, testapp, db):
        """Filtered opportunity results only include the current user's records."""
        other_user = UserFactory(password="myprecious")
        OpportunityFactory(
            user=other_user,
            title="Private Amazon Internship",
            organization="Amazon",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.index", q="amazon"))

        assert "Private Amazon Internship" not in res
        assert "No matching opportunities found." in res

    def test_authenticated_user_can_export_opportunities_csv(self, user, testapp, db):
        """Authenticated users can export their opportunities as CSV."""
        opportunity = OpportunityFactory(
            user=user,
            title="Research Fellowship",
            organization="Science Center",
            category="research",
            status="submitted",
            priority="high",
            link="https://example.com/fellowship",
            notes="Finalize transcript request.",
            deadline=dt.date(2026, 5, 15),
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.export"))

        assert res.status_code == 200
        assert res.content_type.startswith("text/csv")
        expected_disposition = 'attachment; filename="launchpad-opportunities.csv"'
        assert res.headers["Content-Disposition"] == expected_disposition
        assert "title,organization,category,status,priority,deadline,link" in res.text
        assert opportunity.title in res.text
        assert opportunity.organization in res.text
        assert "2026-05-15" in res.text

    def test_opportunity_export_excludes_other_users_records(self, user, testapp, db):
        """Opportunity CSV export only includes the current user's records."""
        other_user = UserFactory(password="myprecious")
        own_opportunity = OpportunityFactory(user=user, title="My Scholarship")
        other_opportunity = OpportunityFactory(
            user=other_user,
            title="Private Internship",
            organization="Private Org",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("opportunities.export"))

        assert own_opportunity.title in res.text
        assert other_opportunity.title not in res.text

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

    def test_detail_page_shows_outreach_section(self, user, testapp, db):
        """Opportunity detail renders saved outreach information."""
        opportunity = OpportunityFactory(user=user, title="Research Fellowship")
        OpportunityOutreachFactory(
            opportunity=opportunity,
            contact_name="Program Coordinator",
            contact_role="Graduate Office",
            contact_method="coordinator@example.com",
            outreach_notes="Send follow-up after office hours.",
            outreach_status="follow-up due",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Contact and follow-up" in res
        assert "Program Coordinator" in res
        assert "Graduate Office" in res
        assert "coordinator@example.com" in res
        assert "Follow-up Due" in res
        assert "Send follow-up after office hours." in res

    def test_readiness_summary_renders_on_detail_page(self, user, testapp, db):
        """Opportunity detail renders the application packet summary."""
        opportunity = OpportunityFactory(
            user=user,
            deadline=dt.date.today() + dt.timedelta(days=10),
        )
        material = MaterialFactory(user=user, title="Packet Resume")
        opportunity.materials.append(material)
        RequirementItemFactory(
            opportunity=opportunity, title="Draft essay", is_completed=True
        )
        RequirementItemFactory(
            opportunity=opportunity, title="Request transcript", is_completed=False
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Application Packet" in res
        assert "Readiness summary" in res
        assert "50%" in res
        assert "1 of 2 requirements complete" in res
        assert "1 linked material connected to this application." in res
        assert "Deadline approaching" in res

    def test_no_checklist_next_action_appears(self, user, testapp, db):
        """Opportunity detail prompts checklist generation when nothing exists."""
        opportunity = OpportunityFactory(user=user)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Needs attention" in res
        assert "Next step: generate a starter checklist for this application." in res
        assert "No checklist items yet." in res

    def test_incomplete_requirements_next_action_appears(self, user, testapp, db):
        """Opportunity detail prompts remaining checklist work."""
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

        assert "In progress" in res
        assert "Next step: complete 1 remaining requirement." in res
        assert "1 requirement still needs attention." in res

    def test_complete_checklist_state_appears(self, user, testapp, db):
        """Opportunity detail shows a ready state when checklist and materials exist."""
        opportunity = OpportunityFactory(user=user)
        opportunity.materials.append(MaterialFactory(user=user, title="Ready Resume"))
        RequirementItemFactory(
            opportunity=opportunity,
            title="Finalize resume",
            is_completed=True,
        )
        RequirementItemFactory(
            opportunity=opportunity,
            title="Submit application",
            is_completed=True,
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Ready" in res
        assert "All checklist items are complete." in res
        assert (
            "Next step: review the packet, submit the application, or update the "
            "status." in res
        )

    def test_linked_material_count_appears(self, user, testapp, db):
        """Opportunity detail shows the linked materials count."""
        opportunity = OpportunityFactory(user=user)
        opportunity.materials.append(MaterialFactory(user=user, title="Resume"))
        opportunity.materials.append(MaterialFactory(user=user, title="Essay Notes"))
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "2 linked materials connected to this application." in res

    def test_due_soon_deadline_urgency_and_priority_message_appear(
        self, user, testapp, db
    ):
        """Due-soon incomplete opportunities get deadline urgency guidance."""
        opportunity = OpportunityFactory(
            user=user,
            deadline=dt.date.today() + dt.timedelta(days=5),
        )
        RequirementItemFactory(
            opportunity=opportunity,
            title="Submit transcript",
            is_completed=False,
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Deadline approaching" in res
        assert "Due in 5 days" in res
        assert "Next step: prioritize this opportunity." in res

    def test_overdue_deadline_urgency_appears(self, user, testapp, db):
        """Overdue opportunities render overdue urgency messaging."""
        opportunity = OpportunityFactory(
            user=user,
            deadline=dt.date.today() - dt.timedelta(days=2),
        )
        RequirementItemFactory(
            opportunity=opportunity,
            title="Submit final application",
            is_completed=False,
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(
            url_for("opportunities.detail", opportunity_id=opportunity.id)
        )

        assert "Overdue" in res
        assert "Overdue by 2 days" in res
        assert "Next step: prioritize this opportunity." in res

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
        form["tags"] = "summer 2026, accepted"
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
        assert opportunity.tag_names == ["accepted", "summer 2026"]

    def test_owner_can_save_outreach_details(self, user, testapp, db):
        """Owners can save outreach details from the opportunity edit form."""
        opportunity = OpportunityFactory(user=user, title="Scholarship Packet")
        db.session.commit()
        login(testapp, user)
        res = testapp.get(url_for("opportunities.edit", opportunity_id=opportunity.id))
        form = res.forms[0]
        form["contact_name"] = "Scholarship Office"
        form["contact_role"] = "Financial Aid Advisor"
        form["contact_method"] = "advisor@example.edu"
        form["outreach_status"] = "follow-up due"
        form["outreach_notes"] = "Check back after submitting the transcript."

        res = form.submit().follow()
        db.session.refresh(opportunity)

        assert res.status_code == 200
        assert opportunity.outreach is not None
        assert opportunity.outreach.contact_name == "Scholarship Office"
        assert opportunity.outreach.contact_role == "Financial Aid Advisor"
        assert opportunity.outreach.contact_method == "advisor@example.edu"
        assert opportunity.outreach.outreach_status == "follow-up due"
        assert "Opportunity updated." in res

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
