# -*- coding: utf-8 -*-
"""Opportunity view tests."""
from flask import url_for

from launchpad_os.opportunities.models import Opportunity

from .factories import OpportunityFactory, UserFactory


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
        """The old workspace page redirects to the opportunity list."""
        login(testapp, user)
        res = testapp.get(url_for("user.members"))

        assert res.status_code == 302
        assert res.location.endswith(url_for("opportunities.index"))

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
