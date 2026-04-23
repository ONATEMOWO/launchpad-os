# -*- coding: utf-8 -*-
"""Resource hub view tests."""
from flask import url_for

from launchpad_os.resources.models import ResourceSource

from .factories import ResourceSourceFactory, UserFactory


def login(testapp, user):
    """Log in a user through the public login form."""
    res = testapp.get(url_for("public.login"))
    form = res.forms["loginForm"]
    form["username"] = user.username
    form["password"] = "myprecious"
    return form.submit().follow()


class TestResourceViews:
    """Resource hub view tests."""

    def test_anonymous_user_cannot_access_resource_hub(self, testapp):
        """Anonymous users cannot access the resource hub."""
        testapp.get(url_for("resources.index"), status=401)

    def test_resource_hub_renders_curated_sections(self, user, testapp):
        """Authenticated users can view the curated resource hub."""
        login(testapp, user)
        res = testapp.get(url_for("resources.index"))

        assert res.status_code == 200
        assert "Discover opportunity sources" in res
        assert "Handshake" in res
        assert "NSF REU" in res
        assert "Capture from source" in res

    def test_user_can_save_personal_resource_source(self, user, testapp):
        """Authenticated users can save a personal source link."""
        old_count = ResourceSource.query.count()
        login(testapp, user)
        res = testapp.get(url_for("resources.index"))
        form = res.forms["resourceSourceForm"]
        form["name"] = "Professor Opportunities Page"
        form["category"] = "research"
        form["url"] = "https://example.edu/professor"
        form["notes"] = "Updated weekly during the semester."

        res = form.submit().follow()

        assert res.status_code == 200
        assert "Resource source saved." in res
        assert ResourceSource.query.count() == old_count + 1
        source = ResourceSource.query.filter_by(
            name="Professor Opportunities Page"
        ).one()
        assert source.user == user
        assert source.url == "https://example.edu/professor"

    def test_resource_hub_only_shows_current_users_sources(self, user, testapp, db):
        """Personal resource links are scoped to the current user."""
        other_user = UserFactory(password="myprecious")
        own_source = ResourceSourceFactory(user=user, name="My Fellowship Page")
        other_source = ResourceSourceFactory(user=other_user, name="Other Private Link")
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("resources.index"))

        assert own_source.name in res
        assert other_source.name not in res

    def test_authenticated_nav_includes_resource_hub(self, user, testapp):
        """Authenticated navigation links to the resource hub."""
        login(testapp, user)
        res = testapp.get(url_for("workspace.index"))

        assert "Resources" in res
        assert url_for("resources.index") in res
