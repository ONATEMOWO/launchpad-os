# -*- coding: utf-8 -*-
"""Opportunity views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.materials.models import Material
from launchpad_os.opportunities.forms import MaterialLinkForm, OpportunityForm
from launchpad_os.opportunities.models import Opportunity
from launchpad_os.requirements.models import RequirementItem
from launchpad_os.utils import flash_errors

blueprint = Blueprint(
    "opportunities", __name__, url_prefix="/opportunities", static_folder="../static"
)


@blueprint.route("/")
@login_required
def index():
    """List current user's opportunities."""
    active_opportunities = (
        Opportunity.query.filter_by(user_id=current_user.id)
        .filter(Opportunity.status != "archived")
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    archived_opportunities = (
        Opportunity.query.filter_by(user_id=current_user.id, status="archived")
        .order_by(Opportunity.updated_at.desc())
        .all()
    )
    return render_template(
        "opportunities/index.html",
        active_opportunities=active_opportunities,
        archived_opportunities=archived_opportunities,
    )


def _get_owned_opportunity_or_404(opportunity_id):
    """Return an opportunity owned by the current user."""
    return Opportunity.query.filter_by(
        id=opportunity_id, user_id=current_user.id
    ).first_or_404()


def _get_owned_material_or_404(material_id):
    """Return a material owned by the current user."""
    return Material.query.filter_by(id=material_id, user_id=current_user.id).first_or_404()


def _material_choice_label(material):
    """Return a readable material label for linking forms."""
    material_type = material.material_type.replace("_", " ")
    return f"{material.title} ({material_type})"


def _available_materials_for(opportunity):
    """Return current user's materials not already linked to this opportunity."""
    linked_material_ids = {material.id for material in opportunity.materials}
    materials = (
        Material.query.filter_by(user_id=current_user.id)
        .order_by(Material.updated_at.desc())
        .all()
    )
    return [material for material in materials if material.id not in linked_material_ids]


@blueprint.route("/new/", methods=["GET", "POST"])
@login_required
def new():
    """Create a new opportunity."""
    form = OpportunityForm()
    if form.validate_on_submit():
        Opportunity.create(
            title=form.title.data,
            organization=form.organization.data,
            category=form.category.data,
            deadline=form.deadline.data,
            status=form.status.data,
            priority=form.priority.data,
            link=form.link.data or None,
            notes=form.notes.data or None,
            user_id=current_user.id,
        )
        flash("Opportunity added.", "success")
        return redirect(url_for("opportunities.index"))
    if form.errors:
        flash_errors(form)
    return render_template("opportunities/new.html", form=form)


@blueprint.route("/<int:opportunity_id>/")
@login_required
def detail(opportunity_id):
    """Show full opportunity details."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    linked_materials = sorted(
        opportunity.materials,
        key=lambda material: material.updated_at,
        reverse=True,
    )
    requirement_items = (
        RequirementItem.query.filter_by(opportunity_id=opportunity.id)
        .order_by(RequirementItem.is_completed.asc(), RequirementItem.created_at.asc())
        .all()
    )
    incomplete_requirements = [
        requirement for requirement in requirement_items if not requirement.is_completed
    ]
    total_requirements = len(requirement_items)
    completed_requirements = sum(
        1 for requirement in requirement_items if requirement.is_completed
    )
    completion_percent = (
        round((completed_requirements / total_requirements) * 100)
        if total_requirements
        else 0
    )
    if incomplete_requirements:
        count = len(incomplete_requirements)
        noun = "requirement" if count == 1 else "requirements"
        next_step_message = f"Next step: complete {count} remaining {noun}."
    elif not linked_materials:
        next_step_message = "Next step: link a saved material to support this application."
    else:
        next_step_message = "Next step: review linked materials and confirm the application is ready."

    return render_template(
        "opportunities/detail.html",
        opportunity=opportunity,
        linked_materials=linked_materials,
        requirement_items=requirement_items,
        incomplete_requirements=incomplete_requirements,
        total_requirements=total_requirements,
        completed_requirements=completed_requirements,
        completion_percent=completion_percent,
        next_step_message=next_step_message,
    )


@blueprint.route("/<int:opportunity_id>/materials/link/", methods=["GET", "POST"])
@login_required
def link_material(opportunity_id):
    """Link an existing material to an owned opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    available_materials = _available_materials_for(opportunity)
    form = MaterialLinkForm()
    form.material_id.choices = [
        (material.id, _material_choice_label(material)) for material in available_materials
    ]
    if form.validate_on_submit():
        material = _get_owned_material_or_404(form.material_id.data)
        if material not in opportunity.materials:
            opportunity.materials.append(material)
            opportunity.save()
            flash("Material linked.", "success")
        else:
            flash("Material is already linked.", "info")
        return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))
    if form.errors:
        flash_errors(form)
    return render_template(
        "opportunities/link_material.html",
        form=form,
        opportunity=opportunity,
        available_materials=available_materials,
    )


@blueprint.route(
    "/<int:opportunity_id>/materials/<int:material_id>/unlink/", methods=["POST"]
)
@login_required
def unlink_material(opportunity_id, material_id):
    """Unlink an owned material from an owned opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    material = _get_owned_material_or_404(material_id)
    if material in opportunity.materials:
        opportunity.materials.remove(material)
        opportunity.save()
        flash("Material unlinked.", "info")
    else:
        flash("Material was not linked to this opportunity.", "info")
    return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))


@blueprint.route("/<int:opportunity_id>/edit/", methods=["GET", "POST"])
@login_required
def edit(opportunity_id):
    """Edit an existing opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    form = OpportunityForm(obj=opportunity)
    if form.validate_on_submit():
        opportunity.update(
            title=form.title.data,
            organization=form.organization.data,
            category=form.category.data,
            deadline=form.deadline.data,
            status=form.status.data,
            priority=form.priority.data,
            link=form.link.data or None,
            notes=form.notes.data or None,
        )
        flash("Opportunity updated.", "success")
        return redirect(url_for("opportunities.index"))
    if form.errors:
        flash_errors(form)
    return render_template(
        "opportunities/edit.html", form=form, opportunity=opportunity
    )


@blueprint.route("/<int:opportunity_id>/archive/", methods=["POST"])
@login_required
def archive(opportunity_id):
    """Archive an opportunity without deleting it."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    opportunity.update(status="archived")
    flash("Opportunity archived.", "info")
    return redirect(url_for("opportunities.index"))


@blueprint.route("/<int:opportunity_id>/restore/", methods=["POST"])
@login_required
def restore(opportunity_id):
    """Restore an archived opportunity to active planning work."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    opportunity.update(status="planning")
    flash("Opportunity restored.", "success")
    return redirect(url_for("opportunities.index"))
