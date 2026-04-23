# -*- coding: utf-8 -*-
"""Opportunity views."""
import datetime as dt
import json
import re

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload

from launchpad_os.materials.models import Material
from launchpad_os.opportunities.assist import request_ai_capture_suggestions
from launchpad_os.opportunities.forms import (
    MaterialLinkForm,
    OpportunityCaptureForm,
    OpportunityForm,
)
from launchpad_os.opportunities.models import (
    CATEGORY_CHOICES,
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    Opportunity,
    OpportunityOutreach,
    OpportunityTag,
)
from launchpad_os.requirements.models import RequirementItem
from launchpad_os.utils import csv_response, flash_errors

blueprint = Blueprint(
    "opportunities", __name__, url_prefix="/opportunities", static_folder="../static"
)

DEADLINE_APPROACHING_DAYS = 30
URGENT_THIS_WEEK_DAYS = 7
URL_PATTERN = re.compile(r"https?://[^\s]+")
SMART_VIEW_CHOICES = [
    ("urgent", "Urgent this week"),
    ("follow_up_due", "Follow-up due"),
    ("low_readiness", "Low readiness"),
    ("missing_materials", "Missing materials"),
    ("missing_checklist", "Missing checklist"),
]
CATEGORY_LABELS = dict(CATEGORY_CHOICES)


def _parse_tags_input(tags_text):
    """Return a cleaned, unique list of tag names."""
    if not tags_text:
        return []

    tag_names = []
    seen = set()
    for raw_tag in re.split(r"[,;\n]+", tags_text):
        cleaned = raw_tag.strip()
        if not cleaned:
            continue
        cleaned = cleaned[:50]
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        tag_names.append(cleaned)
    return tag_names


def _save_tags(opportunity, tags_text):
    """Assign parsed tags to an opportunity for the current user."""
    tag_names = _parse_tags_input(tags_text)
    existing_tags = {
        tag.name.lower(): tag
        for tag in OpportunityTag.query.filter_by(user_id=current_user.id).all()
    }
    selected_tags = []
    for name in tag_names:
        key = name.lower()
        tag = existing_tags.get(key)
        if not tag:
            tag = OpportunityTag(name=name, user_id=current_user.id)
            tag.save(commit=False)
            existing_tags[key] = tag
        selected_tags.append(tag)
    opportunity.tags = selected_tags
    opportunity.save()


def _opportunity_completion_percent(opportunity):
    """Return checklist completion percentage for an opportunity."""
    requirement_items = list(opportunity.requirement_items)
    total_requirements = len(requirement_items)
    if not total_requirements:
        return 0
    completed_requirements = sum(
        1 for requirement in requirement_items if requirement.is_completed
    )
    return round((completed_requirements / total_requirements) * 100)


def _matches_smart_view(opportunity, smart_view, today):
    """Return whether an opportunity matches a smart view."""
    if not smart_view:
        return True

    has_deadline = opportunity.deadline is not None
    days_until_deadline = (opportunity.deadline - today).days if has_deadline else None
    completion_percent = _opportunity_completion_percent(opportunity)

    if smart_view == "urgent":
        return has_deadline and days_until_deadline <= URGENT_THIS_WEEK_DAYS
    if smart_view == "follow_up_due":
        outreach = opportunity.outreach
        has_follow_up_due = outreach and outreach.outreach_status == "follow-up due"
        return bool(has_follow_up_due)
    if smart_view == "low_readiness":
        return completion_percent < 50
    if smart_view == "missing_materials":
        return len(opportunity.materials) == 0
    if smart_view == "missing_checklist":
        return len(opportunity.requirement_items) == 0
    return True


def _capture_prefill_from_request():
    """Build Quick Capture defaults from query parameters."""
    selected_text = request.args.get("selected_text", "").strip()
    details = request.args.get("details", "").strip()
    notes = request.args.get("notes", "").strip()
    merged_details = "\n\n".join(
        part for part in [selected_text, details, notes] if part
    )
    use_ai_value = request.args.get("use_ai", "").strip().lower()
    use_ai_requested = request.args.get("assist") == "ai"

    return {
        "title": request.args.get("title", "").strip(),
        "organization": request.args.get("organization", "").strip(),
        "link": (request.args.get("url") or request.args.get("link") or "").strip(),
        "deadline_text": (
            request.args.get("deadline_text") or request.args.get("deadline") or ""
        ).strip(),
        "details": merged_details,
        "use_ai": use_ai_requested or use_ai_value in {"1", "true", "yes", "on"},
    }


def _capture_prompt(form):
    """Return a structured capture prompt for optional AI assistance."""
    sections = [
        f"Title: {(form.title.data or '').strip()}",
        f"Organization: {(form.organization.data or '').strip()}",
        f"Link: {(form.link.data or '').strip()}",
        f"Deadline text: {(form.deadline_text.data or '').strip()}",
        f"Notes: {(form.details.data or '').strip()}",
    ]
    return "\n".join(sections)


def _merge_ai_prefill(prefill, ai_result):
    """Merge AI suggestions into deterministic capture defaults."""
    if ai_result.get("title"):
        prefill["title"] = ai_result["title"]
    if ai_result.get("organization"):
        prefill["organization"] = ai_result["organization"]
    if ai_result.get("category"):
        prefill["category"] = ai_result["category"]
    if ai_result.get("deadline_text"):
        ai_deadline = _parse_capture_deadline(ai_result["deadline_text"])
        if ai_deadline:
            prefill["deadline"] = ai_deadline
    if ai_result.get("tags"):
        prefill["tags"] = ", ".join(ai_result["tags"])
    return prefill


def _create_suggested_requirements(opportunity, serialized_items):
    """Create suggested requirement items from a serialized list."""
    if not serialized_items:
        return 0

    try:
        checklist_items = json.loads(serialized_items)
    except (TypeError, json.JSONDecodeError):
        return 0

    existing_titles = {
        requirement.title.strip().lower()
        for requirement in opportunity.requirement_items
    }
    created_count = 0
    for item in checklist_items:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in existing_titles:
            continue
        RequirementItem.create(title=cleaned, opportunity_id=opportunity.id)
        existing_titles.add(key)
        created_count += 1
    return created_count


def _index_filters():
    """Return validated list filters plus available tag records."""
    filters = {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", ""),
        "category": request.args.get("category", ""),
        "priority": request.args.get("priority", ""),
        "tag": request.args.get("tag", "").strip(),
        "view": request.args.get("view", "").strip(),
    }
    available_tags = (
        OpportunityTag.query.filter_by(user_id=current_user.id)
        .order_by(OpportunityTag.name.asc())
        .all()
    )

    valid_values = {
        "status": {choice[0] for choice in STATUS_CHOICES},
        "category": {choice[0] for choice in CATEGORY_CHOICES},
        "priority": {choice[0] for choice in PRIORITY_CHOICES},
        "view": {choice[0] for choice in SMART_VIEW_CHOICES},
        "tag": {item.name for item in available_tags},
    }
    for key in ["status", "category", "priority", "view", "tag"]:
        if filters[key] not in valid_values[key]:
            filters[key] = ""
    return filters, available_tags


def _filtered_opportunity_query(filters):
    """Return the base opportunity query after DB-friendly filters."""
    query = Opportunity.query.filter_by(user_id=current_user.id).options(
        selectinload(Opportunity.tags),
        selectinload(Opportunity.materials),
        selectinload(Opportunity.requirement_items),
        joinedload(Opportunity.outreach),
    )
    if filters["q"]:
        search_term = f"%{filters['q']}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(search_term),
                Opportunity.organization.ilike(search_term),
            )
        )
    if filters["status"]:
        query = query.filter_by(status=filters["status"])
    if filters["category"]:
        query = query.filter_by(category=filters["category"])
    if filters["priority"]:
        query = query.filter_by(priority=filters["priority"])
    if filters["tag"]:
        query = query.join(Opportunity.tags).filter(
            OpportunityTag.user_id == current_user.id,
            OpportunityTag.name == filters["tag"],
        )
    return query


@blueprint.route("/")
@login_required
def index():
    """List current user's opportunities."""
    today = dt.date.today()
    filters, available_tags = _index_filters()
    query = _filtered_opportunity_query(filters)
    opportunities = query.order_by(
        Opportunity.deadline.asc().nullslast(), Opportunity.updated_at.desc()
    ).all()
    filtered_opportunities = [
        opportunity
        for opportunity in opportunities
        if _matches_smart_view(opportunity, filters["view"], today)
    ]
    active_opportunities = [
        opportunity
        for opportunity in filtered_opportunities
        if opportunity.status != "archived"
    ]
    archived_opportunities = [
        opportunity
        for opportunity in filtered_opportunities
        if opportunity.status == "archived"
    ]
    filters = {
        "q": filters["q"],
        "status": filters["status"],
        "category": filters["category"],
        "priority": filters["priority"],
        "tag": filters["tag"],
        "view": filters["view"],
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
        smart_view_choices=SMART_VIEW_CHOICES,
        available_tags=available_tags,
    )


@blueprint.route("/export.csv")
@login_required
def export():
    """Export the current user's opportunities as CSV."""
    opportunities = (
        Opportunity.query.filter_by(user_id=current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )
    rows = [
        [
            opportunity.title,
            opportunity.organization,
            opportunity.category,
            opportunity.status,
            opportunity.priority,
            opportunity.deadline.isoformat() if opportunity.deadline else "",
            opportunity.link or "",
            opportunity.notes or "",
            opportunity.created_at.isoformat() if opportunity.created_at else "",
            opportunity.updated_at.isoformat() if opportunity.updated_at else "",
        ]
        for opportunity in opportunities
    ]
    return csv_response(
        "launchpad-opportunities.csv",
        [
            "title",
            "organization",
            "category",
            "status",
            "priority",
            "deadline",
            "link",
            "notes",
            "created_at",
            "updated_at",
        ],
        rows,
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


def _extract_first_url(*values):
    """Extract the first URL-like value from a series of text inputs."""
    for value in values:
        if not value:
            continue
        match = URL_PATTERN.search(value)
        if match:
            return match.group(0).rstrip(".,);]")
    return None


def _parse_capture_deadline(deadline_text):
    """Parse a small set of simple date formats from capture input."""
    if not deadline_text:
        return None

    normalized = deadline_text.strip()
    if not normalized:
        return None

    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]
    for fmt in formats:
        try:
            return dt.datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return None


def _build_capture_prefill(form):
    """Build deterministic opportunity defaults from quick capture input."""
    title = (form.title.data or "").strip()
    organization = (form.organization.data or "").strip()
    details = (form.details.data or "").strip()
    deadline_text = (form.deadline_text.data or "").strip()
    deadline = _parse_capture_deadline(deadline_text)
    link = _extract_first_url(form.link.data, details)

    notes_parts = []
    if details:
        notes_parts.append(details)
    if deadline_text and not deadline:
        notes_parts.append(f"Deadline note: {deadline_text}")

    return {
        "title": title,
        "organization": organization,
        "category": "internship",
        "deadline": deadline,
        "status": "saved",
        "priority": "medium",
        "tags": "",
        "link": link or "",
        "notes": "\n\n".join(notes_parts),
    }


def _render_opportunity_create_form(form, **overrides):
    """Render the opportunity create template with configurable copy."""
    context = {
        "form": form,
        "form_action": "",
        "page_eyebrow": "Opportunity Tracking",
        "page_heading": "Add opportunity",
        "page_description": (
            "Start with the essentials now, then come back to build the "
            "checklist, materials, and readiness details around the packet."
        ),
        "back_url": url_for("opportunities.index"),
        "back_label": "Back to list",
        "submit_label": "Save opportunity",
        "review_notice": None,
        "assistance_notice": None,
        "capture_summary": None,
        "suggested_title": "",
        "suggested_organization": "",
        "suggested_category": "",
        "suggested_category_label": "",
        "suggested_deadline_text": "",
        "suggested_checklist": [],
        "suggested_tags": [],
    }
    context.update(overrides)
    return render_template("opportunities/new.html", **context)


def _save_outreach(opportunity, form):
    """Create, update, or clear outreach details for an opportunity."""
    contact_name = (form.contact_name.data or "").strip() or None
    contact_role = (form.contact_role.data or "").strip() or None
    contact_method = (form.contact_method.data or "").strip() or None
    outreach_notes = (form.outreach_notes.data or "").strip() or None
    outreach_status = form.outreach_status.data or "not contacted"
    has_outreach_details = any(
        [contact_name, contact_role, contact_method, outreach_notes]
    ) or (outreach_status != "not contacted")

    outreach = opportunity.outreach
    if not has_outreach_details:
        if outreach:
            outreach.delete()
        return

    if not outreach:
        outreach = OpportunityOutreach(opportunity=opportunity)

    outreach.contact_name = contact_name
    outreach.contact_role = contact_role
    outreach.contact_method = contact_method
    outreach.outreach_notes = outreach_notes
    outreach.outreach_status = outreach_status
    outreach.save()


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
        opportunity = Opportunity.create(
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
        _save_tags(opportunity, form.tags.data)
        _save_outreach(opportunity, form)
        if form.create_suggested_checklist.data:
            created_count = _create_suggested_requirements(
                opportunity, form.suggested_checklist_items.data
            )
            if created_count:
                noun = "item" if created_count == 1 else "items"
                flash(f"{created_count} suggested checklist {noun} added.", "success")
        flash("Opportunity added.", "success")
        return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))
    if form.errors:
        flash_errors(form)
    return _render_opportunity_create_form(form)


@blueprint.route("/capture/", methods=["GET", "POST"])
@login_required
def capture():
    """Quickly capture rough opportunity details before full review."""
    if request.method == "GET" and request.args:
        form = OpportunityCaptureForm(data=_capture_prefill_from_request())
    else:
        form = OpportunityCaptureForm()
    if form.validate_on_submit():
        prefill = _build_capture_prefill(form)
        ai_result = {
            "used_ai": False,
            "title": "",
            "organization": "",
            "category": "",
            "summary": "",
            "deadline_text": "",
            "checklist_items": [],
            "tags": [],
            "reason": "",
        }
        if form.use_ai.data:
            ai_result = request_ai_capture_suggestions(
                current_app, _capture_prompt(form)
            )
            prefill = _merge_ai_prefill(prefill, ai_result)
        review_form = OpportunityForm(
            formdata=None,
            data={
                **prefill,
                "create_suggested_checklist": bool(ai_result["checklist_items"]),
                "suggested_checklist_items": json.dumps(ai_result["checklist_items"]),
            },
        )
        return _render_opportunity_create_form(
            review_form,
            form_action=url_for("opportunities.new"),
            page_eyebrow="Quick Capture",
            page_heading="Review captured opportunity",
            page_description=(
                "Quick Capture prefilled what it could. Review the details below, "
                "make changes, and save when you are ready."
            ),
            back_url=url_for("opportunities.capture"),
            back_label="Back to capture",
            review_notice=(
                "Quick Capture is best for saving a link, rough title, or notes "
                "now and refining the packet details afterward."
            ),
            assistance_notice=ai_result["reason"] if form.use_ai.data else None,
            capture_summary=ai_result["summary"],
            suggested_title=ai_result["title"],
            suggested_organization=ai_result["organization"],
            suggested_category=ai_result["category"],
            suggested_category_label=CATEGORY_LABELS.get(ai_result["category"], ""),
            suggested_deadline_text=ai_result["deadline_text"],
            suggested_checklist=ai_result["checklist_items"],
            suggested_tags=ai_result["tags"],
        )
    if form.errors:
        flash_errors(form)
    capture_prefill = {
        "title": (form.title.data or "").strip(),
        "organization": (form.organization.data or "").strip(),
        "link": (form.link.data or "").strip(),
        "deadline_text": (form.deadline_text.data or "").strip(),
        "details": (form.details.data or "").strip(),
    }
    return render_template(
        "opportunities/capture.html",
        form=form,
        capture_source=request.args.get("source", ""),
        capture_prefill=capture_prefill,
    )


@blueprint.route("/<int:opportunity_id>/")
@login_required
def detail(opportunity_id):
    """Show full opportunity details."""
    today = dt.date.today()
    opportunity = _get_owned_opportunity_or_404(opportunity_id)
    outreach = opportunity.outreach
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

    outreach_status = outreach.outreach_status if outreach else "not contacted"
    outreach_status_label = (
        outreach.outreach_status_label if outreach else "Not Contacted"
    )
    outreach_values = (
        [
            outreach.contact_name,
            outreach.contact_role,
            outreach.contact_method,
            outreach.outreach_notes,
            outreach.outreach_status != "not contacted",
        ]
        if outreach
        else []
    )
    has_outreach = bool(outreach and any(outreach_values))

    return render_template(
        "opportunities/detail.html",
        opportunity=opportunity,
        outreach=outreach,
        outreach_status=outreach_status,
        outreach_status_label=outreach_status_label,
        has_outreach=has_outreach,
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
    outreach = opportunity.outreach
    outreach_data = {
        "tags": ", ".join(opportunity.tag_names),
        "contact_name": outreach.contact_name if outreach else None,
        "contact_role": outreach.contact_role if outreach else None,
        "contact_method": outreach.contact_method if outreach else None,
        "outreach_status": outreach.outreach_status if outreach else "not contacted",
        "outreach_notes": outreach.outreach_notes if outreach else None,
    }
    form = OpportunityForm(obj=opportunity, data=outreach_data)
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
        _save_tags(opportunity, form.tags.data)
        _save_outreach(opportunity, form)
        flash("Opportunity updated.", "success")
        return redirect(url_for("opportunities.detail", opportunity_id=opportunity.id))
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
