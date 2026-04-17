# -*- coding: utf-8 -*-
"""Opportunity views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.opportunities.forms import OpportunityForm
from launchpad_os.opportunities.models import Opportunity
from launchpad_os.utils import flash_errors

blueprint = Blueprint(
    "opportunities", __name__, url_prefix="/opportunities", static_folder="../static"
)


@blueprint.route("/")
@login_required
def index():
    """List current user's opportunities."""
    opportunities = (
        Opportunity.query.filter_by(user_id=current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    return render_template("opportunities/index.html", opportunities=opportunities)


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
