# -*- coding: utf-8 -*-
"""Material view tests."""
from flask import url_for

from launchpad_os.materials.models import Material

from .factories import MaterialFactory, UserFactory


def login(testapp, user):
    """Log in a user through the public login form."""
    res = testapp.get(url_for("public.login"))
    form = res.forms["loginForm"]
    form["username"] = user.username
    form["password"] = "myprecious"
    return form.submit().follow()


class TestMaterialViews:
    """Material view tests."""

    def test_anonymous_user_cannot_access_index(self, testapp):
        """Anonymous users cannot view materials."""
        testapp.get(url_for("materials.index"), status=401)

    def test_anonymous_user_cannot_access_new(self, testapp):
        """Anonymous users cannot create materials."""
        testapp.get(url_for("materials.new"), status=401)

    def test_logged_in_user_can_access_index(self, user, testapp):
        """Logged-in users can view their materials list."""
        login(testapp, user)
        res = testapp.get(url_for("materials.index"))

        assert res.status_code == 200
        assert "Materials" in res

    def test_logged_in_user_can_access_new(self, user, testapp):
        """Logged-in users can view the create form."""
        login(testapp, user)
        res = testapp.get(url_for("materials.new"))

        assert res.status_code == 200
        assert "Add material" in res

    def test_logged_in_user_can_create_material(self, user, testapp):
        """Logged-in users can create material records."""
        old_count = len(Material.query.all())
        login(testapp, user)
        res = testapp.get(url_for("materials.new"))
        form = res.forms[0]
        form["title"] = "Resume Draft"
        form["material_type"] = "resume"
        form["content"] = "Project bullets and leadership notes."
        form["link"] = "https://example.com/resume"
        form["notes"] = "Revise before internship applications."

        res = form.submit().follow()

        assert res.status_code == 200
        assert "Material added." in res
        assert "Resume Draft" in res
        assert "Project bullets and leadership notes." in res
        assert len(Material.query.all()) == old_count + 1
        material = Material.query.filter_by(title="Resume Draft").one()
        assert material.user == user

    def test_user_only_sees_own_materials(self, user, testapp, db):
        """Users only see materials connected to their account."""
        other_user = UserFactory(password="myprecious")
        own_material = MaterialFactory(user=user, title="My Essay")
        other_material = MaterialFactory(user=other_user, title="Other Resume")
        db.session.commit()

        login(testapp, user)
        res = testapp.get(url_for("materials.index"))

        assert own_material.title in res
        assert other_material.title not in res

    def test_owner_can_view_detail_page(self, user, testapp, db):
        """Owners can view full material details."""
        material = MaterialFactory(
            user=user,
            title="Scholarship Essay Notes",
            material_type="essay",
            content="Draft paragraph about research goals.",
            link="https://example.com/essay",
            notes="Ask writing center for feedback.",
        )
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("materials.detail", material_id=material.id))

        assert res.status_code == 200
        assert "Scholarship Essay Notes" in res
        assert "Draft paragraph about research goals." in res
        assert "https://example.com/essay" in res
        assert "Ask writing center for feedback." in res

    def test_non_owner_cannot_view_detail_page(self, user, testapp, db):
        """Users cannot view materials they do not own."""
        other_user = UserFactory(password="myprecious")
        material = MaterialFactory(user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(url_for("materials.detail", material_id=material.id), status=404)

    def test_detail_page_shows_empty_notes_message(self, user, testapp, db):
        """Detail page explains when notes are empty."""
        material = MaterialFactory(user=user, notes=None)
        db.session.commit()
        login(testapp, user)

        res = testapp.get(url_for("materials.detail", material_id=material.id))

        assert "No notes yet." in res

    def test_owner_can_edit_material(self, user, testapp, db):
        """Owners can update their materials."""
        material = MaterialFactory(
            user=user,
            title="Old Resume",
            material_type="resume",
            content="Old content.",
        )
        db.session.commit()
        login(testapp, user)
        res = testapp.get(url_for("materials.edit", material_id=material.id))
        form = res.forms[0]
        form["title"] = "Updated Cover Letter"
        form["material_type"] = "cover_letter"
        form["content"] = "Updated letter draft."
        form["link"] = "https://example.com/cover-letter"
        form["notes"] = "Tailor for research assistant roles."

        res = form.submit().follow()
        db.session.refresh(material)

        assert res.status_code == 200
        assert "Material updated." in res
        assert material.title == "Updated Cover Letter"
        assert material.material_type == "cover_letter"
        assert material.content == "Updated letter draft."
        assert "Updated letter draft." in res

    def test_non_owner_cannot_edit_material(self, user, testapp, db):
        """Users cannot edit materials they do not own."""
        other_user = UserFactory(password="myprecious")
        material = MaterialFactory(user=other_user)
        db.session.commit()
        login(testapp, user)

        testapp.get(url_for("materials.edit", material_id=material.id), status=404)

    def test_nav_includes_materials_for_authenticated_users(self, user, testapp):
        """Authenticated navigation links to the materials vault."""
        login(testapp, user)
        res = testapp.get(url_for("opportunities.index"))

        assert "Materials" in res
        assert url_for("materials.index") in res
