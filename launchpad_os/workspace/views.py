# -*- coding: utf-8 -*-
"""Workspace dashboard views."""
import datetime as dt

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from launchpad_os.materials.models import Material
from launchpad_os.opportunities.models import Opportunity

blueprint = Blueprint(
    "workspace", __name__, url_prefix="/workspace", static_folder="../static"
)

DUE_SOON_DAYS = 30
LOW_READINESS_THRESHOLD = 50


def _deadline_context(deadline, today):
    """Return simple deadline display metadata for an opportunity."""
    if not deadline:
        return {
            "days_until_deadline": None,
            "deadline_label": "No deadline",
            "is_due_soon": False,
            "is_overdue": False,
        }

    days_until_deadline = (deadline - today).days
    is_overdue = days_until_deadline < 0
    is_due_soon = 0 <= days_until_deadline <= DUE_SOON_DAYS

    if days_until_deadline == 0:
        deadline_label = "Due today"
    elif days_until_deadline == 1:
        deadline_label = "Due tomorrow"
    elif is_overdue:
        deadline_label = f"Overdue by {abs(days_until_deadline)} days"
    else:
        deadline_label = f"Due in {days_until_deadline} days"

    return {
        "days_until_deadline": days_until_deadline,
        "deadline_label": deadline_label,
        "is_due_soon": is_due_soon,
        "is_overdue": is_overdue,
    }


def _build_opportunity_progress(opportunities, today):
    """Build dashboard-ready opportunity progress data."""
    opportunity_cards = []
    for opportunity in opportunities:
        requirement_items = list(opportunity.requirement_items)
        total_requirements = len(requirement_items)
        completed_requirements = sum(
            1 for requirement in requirement_items if requirement.is_completed
        )
        completion_percent = (
            round((completed_requirements / total_requirements) * 100)
            if total_requirements
            else 0
        )
        needs_requirements = (
            completed_requirements < total_requirements or total_requirements == 0
        )
        deadline_context = _deadline_context(opportunity.deadline, today)
        outreach = opportunity.outreach
        outreach_status = outreach.outreach_status if outreach else "not contacted"
        opportunity_cards.append(
            {
                "opportunity": opportunity,
                "total_requirements": total_requirements,
                "completed_requirements": completed_requirements,
                "completion_percent": completion_percent,
                "needs_requirements": needs_requirements,
                "outreach_status": outreach_status,
                "follow_up_due": outreach_status == "follow-up due",
                **deadline_context,
            }
        )
    return opportunity_cards


def _is_high_priority_low_readiness(card):
    """Return whether an opportunity should appear in the priority digest."""
    return card["opportunity"].priority == "high" and (
        card["completion_percent"] < LOW_READINESS_THRESHOLD
    )


@blueprint.route("/")
@login_required
def index():
    """Show the authenticated application workspace dashboard."""
    today = dt.date.today()
    active_opportunities = (
        Opportunity.query.filter_by(user_id=current_user.id)
        .filter(Opportunity.status != "archived")
        .order_by(Opportunity.deadline.asc().nullslast(), Opportunity.created_at.desc())
        .all()
    )
    archived_opportunities_count = Opportunity.query.filter_by(
        user_id=current_user.id, status="archived"
    ).count()
    materials_count = Material.query.filter_by(user_id=current_user.id).count()

    opportunity_cards = _build_opportunity_progress(active_opportunities, today)
    due_soon_opportunities = [
        card
        for card in opportunity_cards
        if card["opportunity"].deadline and (card["is_due_soon"] or card["is_overdue"])
    ]
    due_soon_opportunities.sort(key=lambda card: card["opportunity"].deadline)
    incomplete_opportunities = [
        card for card in opportunity_cards if card["needs_requirements"]
    ]
    overdue_opportunities = [card for card in opportunity_cards if card["is_overdue"]]
    due_soon_upcoming = [
        card
        for card in due_soon_opportunities
        if card["opportunity"].deadline and not card["is_overdue"]
    ]
    high_priority_low_readiness = [
        card for card in opportunity_cards if _is_high_priority_low_readiness(card)
    ]
    follow_up_due_opportunities = [
        card for card in opportunity_cards if card["follow_up_due"]
    ]

    return render_template(
        "workspace/index.html",
        active_opportunities_count=len(active_opportunities),
        archived_opportunities_count=archived_opportunities_count,
        materials_count=materials_count,
        incomplete_opportunities_count=len(incomplete_opportunities),
        opportunity_cards=opportunity_cards,
        due_soon_opportunities=due_soon_opportunities[:5],
        incomplete_opportunities=incomplete_opportunities[:5],
        overdue_opportunities=overdue_opportunities[:5],
        due_soon_upcoming=due_soon_upcoming[:5],
        high_priority_low_readiness=high_priority_low_readiness[:5],
        follow_up_due_opportunities=follow_up_due_opportunities[:5],
    )
