# -*- coding: utf-8 -*-
"""Requirement checklist views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.opportunities.models import Opportunity
from launchpad_os.requirements.forms import RequirementItemForm
from launchpad_os.requirements.models import RequirementItem
from launchpad_os.utils import flash_errors

blueprint = Blueprint("requirements", __name__, static_folder="../static")

CHECKLIST_TEMPLATES = {
    "internship": [
        "Update resume",
        "Draft or tailor cover letter",
        "Review application link",
        "Prepare portfolio or GitHub link",
        "Submit application form",
    ],
    "scholarship": [
        "Draft essay or personal statement",
        "Prepare transcript",
        "Request recommendation",
        "Review eligibility requirements",
        "Submit application before deadline",
    ],
    "research": [
        "Review project or lab description",
        "Prepare resume or CV",
        "Draft outreach email",
        "List relevant coursework or experience",
        "Identify recommendation/reference if needed",
    ],
    "fellowship": [
        "Draft personal statement or essay",
        "Research program requirements and eligibility",
        "Request letters of recommendation",
        "Prepare transcript and academic record",
        "Submit application before deadline",
    ],
}


def _get_owned_opportunity_or_404(opportunity_id):
    """Return an opportunity owned by the current user."""
    return Opportunity.query.filter_by(
        id=opportunity_id, user_id=current_user.id
    ).first_or_404()


def _get_owned_requirement_or_404(requirement_id):
    """Return a requirement item through an opportunity owned by the current user."""
    return (
        RequirementItem.query.join(Opportunity)
        .filter(RequirementItem.id == requirement_id)
        .filter(Opportunity.user_id == current_user.id)
        .first_or_404()
    )


def _normalized_title(title):
    """Normalize requirement titles for simple duplicate detection."""
    return title.strip().lower()


@blueprint.route(
    "/opportunities/<int:opportunity_id>/requirements/new/", methods=["GET", "POST"]
)
@login_required
def new(opportunity_id):
    """Create a new requirement item for an owned opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    form = RequirementItemForm()
    if form.validate_on_submit():
        RequirementItem.create(
            title=form.title.data,
            is_completed=form.is_completed.data,
            notes=form.notes.data or None,
            opportunity_id=opportunity.id,
        )
        flash("Requirement item added.", "success")
        return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))
    if form.errors:
        flash_errors(form)
    return render_template("requirements/new.html", form=form, opportunity=opportunity)


@blueprint.route(
    "/opportunities/<int:opportunity_id>/requirements/generate/", methods=["POST"]
)
@login_required
def generate_template(opportunity_id):
    """Generate starter checklist items for an owned opportunity."""
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    template_titles = CHECKLIST_TEMPLATES.get(opportunity.category, [])
    existing_titles = {
        _normalized_title(requirement.title)
        for requirement in opportunity.requirement_items
    }
    created_count = 0

    for title in template_titles:
        normalized_title = _normalized_title(title)
        if normalized_title in existing_titles:
            continue
        RequirementItem.create(title=title, opportunity_id=opportunity.id)
        existing_titles.add(normalized_title)
        created_count += 1

    if created_count:
        flash(f"Added {created_count} starter checklist item(s).", "success")
    else:
        flash("Checklist already includes the starter items.", "info")
    return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))


@blueprint.route("/requirements/<int:requirement_id>/edit/", methods=["GET", "POST"])
@login_required
def edit(requirement_id):
    """Edit an existing requirement item."""
    requirement = _get_owned_requirement_or_404(requirement_id)
    form = RequirementItemForm(obj=requirement)
    if form.validate_on_submit():
        requirement.update(
            title=form.title.data,
            is_completed=form.is_completed.data,
            notes=form.notes.data or None,
        )
        flash("Requirement item updated.", "success")
        return redirect(
            url_for("opportunities.detail", opportunity_id=requirement.opportunity_id)
        )
    if form.errors:
        flash_errors(form)
    return render_template("requirements/edit.html", form=form, requirement=requirement)


@blueprint.route("/requirements/<int:requirement_id>/toggle/", methods=["POST"])
@login_required
def toggle(requirement_id):
    """Toggle a requirement item complete or incomplete."""
    requirement = _get_owned_requirement_or_404(requirement_id)
    requirement.update(is_completed=not requirement.is_completed)
    if requirement.is_completed:
        flash("Requirement marked complete.", "success")
    else:
        flash("Requirement marked incomplete.", "info")
    return redirect(
        url_for("opportunities.detail", opportunity_id=requirement.opportunity_id)
    )


@blueprint.route("/requirements/<int:requirement_id>/delete/", methods=["POST"])
@login_required
def delete(requirement_id):
    """Delete a requirement item from an owned opportunity."""
    requirement = _get_owned_requirement_or_404(requirement_id)
    opportunity_id = requirement.opportunity_id
    requirement.delete()
    flash("Requirement item deleted.", "info")
    return redirect(url_for("opportunities.detail", opportunity_id=opportunity_id))
