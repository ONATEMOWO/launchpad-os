# -*- coding: utf-8 -*-
"""Material views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.materials.forms import MaterialForm
from launchpad_os.materials.models import Material
from launchpad_os.utils import flash_errors

blueprint = Blueprint(
    "materials", __name__, url_prefix="/materials", static_folder="../static"
)


@blueprint.route("/")
@login_required
def index():
    """List current user's materials."""
    materials = (
        Material.query.filter_by(user_id=current_user.id)
        .order_by(Material.updated_at.desc())
        .all()
    )
    return render_template("materials/index.html", materials=materials)


def _get_owned_material_or_404(material_id):
    """Return a material owned by the current user."""
    return Material.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()


@blueprint.route("/new/", methods=["GET", "POST"])
@login_required
def new():
    """Create a new material."""
    form = MaterialForm()
    if form.validate_on_submit():
        material = Material.create(
            title=form.title.data,
            material_type=form.material_type.data,
            content=form.content.data,
            link=form.link.data or None,
            notes=form.notes.data or None,
            user_id=current_user.id,
        )
        flash("Material added.", "success")
        return redirect(url_for("materials.detail", material_id=material.id))
    if form.errors:
        flash_errors(form)
    return render_template("materials/new.html", form=form)


@blueprint.route("/<int:material_id>/")
@login_required
def detail(material_id):
    """Show full material details."""
    material = _get_owned_material_or_404(material_id)
    return render_template("materials/detail.html", material=material)


@blueprint.route("/<int:material_id>/edit/", methods=["GET", "POST"])
@login_required
def edit(material_id):
    """Edit an existing material."""
    material = _get_owned_material_or_404(material_id)
    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        material.update(
            title=form.title.data,
            material_type=form.material_type.data,
            content=form.content.data,
            link=form.link.data or None,
            notes=form.notes.data or None,
        )
        flash("Material updated.", "success")
        return redirect(url_for("materials.detail", material_id=material.id))
    if form.errors:
        flash_errors(form)
    return render_template("materials/edit.html", form=form, material=material)
