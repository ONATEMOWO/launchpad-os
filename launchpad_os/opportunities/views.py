# -*- coding: utf-8 -*-
"""Opportunity views."""
import datetime as dt

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from launchpad_os.materials.models import Material
from launchpad_os.opportunities.forms import MaterialLinkForm, OpportunityForm
from launchpad_os.opportunities.models import (
    CATEGORY_CHOICES,
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    Opportunity,
)
from launchpad_os.requirements.models import RequirementItem
from launchpad_os.utils import flash_errors

blueprint = Blueprint(
    "opportunities", __name__, url_prefix="/opportunities", static_folder="../static"
)

DEADLINE_APPROACHING_DAYS = 30


@blueprint.route("/")
@login_required
def index():
    """List current user's opportunities."""
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    priority = request.args.get("priority", "")

    status_values = {choice[0] for choice in STATUS_CHOICES}
    category_values = {choice[0] for choice in CATEGORY_CHOICES}
    priority_values = {choice[0] for choice in PRIORITY_CHOICES}

    if status not in status_values:
        status = ""
    if category not in category_values:
        category = ""
    if priority not in priority_values:
        priority = ""

    query = Opportunity.query.filter_by(user_id=current_user.id)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(search_term),
                Opportunity.organization.ilike(search_term),
            )
        )
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if priority:
        query = query.filter_by(priority=priority)

    active_opportunities = (
        query.filter(Opportunity.status != "archived")
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    archived_opportunities = (
        query.filter_by(status="archived").order_by(Opportunity.updated_at.desc()).all()
    )
    filters = {
        "q": q,
        "status": status,
        "category": category,
        "priority": priority,
    }
    return render_template(
        "opportunities/index.html",
        active_opportunities=active_opportunities,
        archived_opportunities=archived_opportunities,
        filters=filters,
        has_filters=any(filters.values()),
        status_choices=STATUS_CHOICES,
        category_choices=CATEGORY_CHOICES,
        priority_choices=PRIORITY_CHOICES,
    )


def _get_owned_opportunity_or_404(opportunity_id):
    """Return an opportunity owned by the current user."""
    return Opportunity.query.filter_by(
        id=opportunity_id, user_id=current_user.id
    ).first_or_404()


def _get_owned_material_or_404(material_id):
    """Return a material owned by the current user."""
    return Material.query.filter_by(
        id=material_id, user_id=current_user.id
    ).first_or_404()


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
    return [
        material for material in materials if material.id not in linked_material_ids
    ]


def _deadline_packet_context(deadline, today):
    """Return deadline urgency metadata for the detail page."""
    if not deadline:
        return {
            "days_until_deadline": None,
            "deadline_label": "No deadline set",
            "deadline_urgency_label": "No deadline",
            "deadline_urgency_class": "muted",
            "is_due_soon": False,
            "is_overdue": False,
        }

    days_until_deadline = (deadline - today).days
    is_overdue = days_until_deadline < 0
    is_due_soon = 0 <= days_until_deadline <= DEADLINE_APPROACHING_DAYS

    if days_until_deadline == 0:
        deadline_label = "Due today"
    elif days_until_deadline == 1:
        deadline_label = "Due tomorrow"
    elif is_overdue:
        deadline_label = f"Overdue by {abs(days_until_deadline)} days"
    else:
        deadline_label = f"Due in {days_until_deadline} days"

    if is_overdue:
        deadline_urgency_label = "Overdue"
        deadline_urgency_class = "danger"
    elif is_due_soon:
        deadline_urgency_label = "Deadline approaching"
        deadline_urgency_class = "warning"
    else:
        deadline_urgency_label = "On track"
        deadline_urgency_class = "info"

    return {
        "days_until_deadline": days_until_deadline,
        "deadline_label": deadline_label,
        "deadline_urgency_label": deadline_urgency_label,
        "deadline_urgency_class": deadline_urgency_class,
        "is_due_soon": is_due_soon,
        "is_overdue": is_overdue,
    }


def _readiness_status(
    total_requirements,
    missing_requirements_count,
    linked_material_count,
    is_due_soon,
    is_overdue,
):
    """Return a simple readiness label and style for an opportunity packet."""
    is_ready = all(
        [
            total_requirements > 0,
            missing_requirements_count == 0,
            linked_material_count > 0,
            not is_overdue,
        ]
    )
    needs_attention = any(
        [
            total_requirements == 0,
            is_overdue,
            is_due_soon and missing_requirements_count > 0,
        ]
    )

    if is_ready:
        return {
            "readiness_label": "Ready",
            "readiness_class": "ready",
        }

    if needs_attention:
        return {
            "readiness_label": "Needs attention",
            "readiness_class": "attention",
        }

    return {
        "readiness_label": "In progress",
        "readiness_class": "progress",
    }


def _next_step_message(
    total_requirements,
    missing_requirements_count,
    linked_material_count,
    is_due_soon,
    is_overdue,
):
    """Return the next recommended action for an opportunity."""
    if total_requirements == 0:
        if is_due_soon or is_overdue:
            return (
                "Next step: prioritize this opportunity and generate a starter "
                "checklist."
            )
        return "Next step: generate a starter checklist for this application."

    if (is_due_soon or is_overdue) and missing_requirements_count > 0:
        urgency_phrase = (
            "The deadline has passed" if is_overdue else "The deadline is approaching"
        )
        return (
            f"Next step: prioritize this opportunity. {urgency_phrase} and work "
            "is still incomplete."
        )

    if missing_requirements_count > 0:
        noun = "requirement" if missing_requirements_count == 1 else "requirements"
        return f"Next step: complete {missing_requirements_count} remaining {noun}."

    if linked_material_count == 0:
        return "Next step: link a relevant material from the Materials Vault."

    return "Next step: review the packet, submit the application, or update the status."


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
    today = dt.date.today()
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
    missing_requirements_count = len(incomplete_requirements)
    linked_material_count = len(linked_materials)
    completion_percent = (
        round((completed_requirements / total_requirements) * 100)
        if total_requirements
        else 0
    )
    deadline_context = _deadline_packet_context(opportunity.deadline, today)
    readiness_status = _readiness_status(
        total_requirements=total_requirements,
        missing_requirements_count=missing_requirements_count,
        linked_material_count=linked_material_count,
        is_due_soon=deadline_context["is_due_soon"],
        is_overdue=deadline_context["is_overdue"],
    )
    next_step_message = _next_step_message(
        total_requirements=total_requirements,
        missing_requirements_count=missing_requirements_count,
        linked_material_count=linked_material_count,
        is_due_soon=deadline_context["is_due_soon"],
        is_overdue=deadline_context["is_overdue"],
    )

    if total_requirements == 0:
        missing_requirements_summary = "No checklist items yet."
    elif missing_requirements_count:
        noun = "requirement" if missing_requirements_count == 1 else "requirements"
        verb = "needs" if missing_requirements_count == 1 else "need"
        missing_requirements_summary = (
            f"{missing_requirements_count} {noun} still {verb} attention."
        )
    else:
        missing_requirements_summary = "All checklist items are complete."

    if linked_material_count == 0:
        linked_materials_summary = (
            "No materials linked yet. Add a resume, essay, cover letter, or note "
            "from the Materials Vault."
        )
    else:
        noun = "material" if linked_material_count == 1 else "materials"
        linked_materials_summary = (
            f"{linked_material_count} linked {noun} connected to this application."
        )

    return render_template(
        "opportunities/detail.html",
        opportunity=opportunity,
        linked_materials=linked_materials,
        requirement_items=requirement_items,
        incomplete_requirements=incomplete_requirements,
        total_requirements=total_requirements,
        completed_requirements=completed_requirements,
        missing_requirements_count=missing_requirements_count,
        linked_material_count=linked_material_count,
        completion_percent=completion_percent,
        missing_requirements_summary=missing_requirements_summary,
        linked_materials_summary=linked_materials_summary,
        next_step_message=next_step_message,
        **deadline_context,
        **readiness_status,
    )


@blueprint.route("/<int:opportunity_id>/materials/link/", methods=["GET", "POST"])
@login_required
def link_material(opportunity_id):
    """Link an existing material to an owned opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    available_materials = _available_materials_for(opportunity)
    form = MaterialLinkForm()
    form.material_id.choices = [
        (material.id, _material_choice_label(material))
        for material in available_materials
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
