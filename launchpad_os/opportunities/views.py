# -*- coding: utf-8 -*-
"""Opportunity views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.opportunities.forms import OpportunityForm
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
    requirement_items = (
        RequirementItem.query.filter_by(opportunity_id=opportunity.id)
        .order_by(RequirementItem.is_completed.asc(), RequirementItem.created_at.asc())
        .all()
    )
    total_requirements = len(requirement_items)
    completed_requirements = sum(
        1 for requirement in requirement_items if requirement.is_completed
    )
    completion_percent = (
        round((completed_requirements / total_requirements) * 100)
        if total_requirements
        else 0
    )
    return render_template(
        "opportunities/detail.html",
        opportunity=opportunity,
        requirement_items=requirement_items,
        total_requirements=total_requirements,
        completed_requirements=completed_requirements,
        completion_percent=completion_percent,
    )


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
