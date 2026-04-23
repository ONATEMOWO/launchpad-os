# -*- coding: utf-8 -*-
"""Resource hub views."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from launchpad_os.resources.forms import ResourceSourceForm
from launchpad_os.resources.models import RESOURCE_CATEGORY_CHOICES, ResourceSource
from launchpad_os.utils import flash_errors

blueprint = Blueprint(
    "resources", __name__, url_prefix="/resources", static_folder="../static"
)

CURATED_SOURCES = [
    {
        "category": "internship",
        "name": "Handshake",
        "url": "https://joinhandshake.com/",
        "notes": "Common campus career portal for internships, early-career roles, and employer events.",
    },
    {
        "category": "internship",
        "name": "LinkedIn Jobs",
        "url": "https://www.linkedin.com/jobs/",
        "notes": "Useful for finding roles, company pages, and recruiter context in one place.",
    },
    {
        "category": "scholarship",
        "name": "Fastweb",
        "url": "https://www.fastweb.com/",
        "notes": "Large scholarship directory that helps surface broad national opportunities.",
    },
    {
        "category": "scholarship",
        "name": "Scholarships.com",
        "url": "https://www.scholarships.com/",
        "notes": "Good starting point for scholarship discovery and deadline tracking.",
    },
    {
        "category": "research",
        "name": "NSF REU",
        "url": "https://www.nsf.gov/crssprgm/reu/",
        "notes": "Central source for undergraduate research experiences and program listings.",
    },
    {
        "category": "research",
        "name": "Pathways To Science",
        "url": "https://www.pathwaystoscience.org/",
        "notes": "Useful for research internships, summer programs, and STEM-focused student opportunities.",
    },
    {
        "category": "fellowship",
        "name": "Fulbright",
        "url": "https://us.fulbrightonline.org/",
        "notes": "Useful benchmark for program-style applications with essays and outreach components.",
    },
    {
        "category": "fellowship",
        "name": "ProFellow",
        "url": "https://www.profellow.com/",
        "notes": "Helpful for fellowship and program discovery, especially when comparing deadlines and fit.",
    },
]


def _group_curated_sources():
    """Return curated sources grouped by category label."""
    grouped_sources = []
    for value, label in RESOURCE_CATEGORY_CHOICES:
        grouped_sources.append(
            {
                "value": value,
                "label": label,
                "sources": [
                    source for source in CURATED_SOURCES if source["category"] == value
                ],
            }
        )
    return grouped_sources


@blueprint.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show the resource hub and allow personal source saving."""
    form = ResourceSourceForm()
    if form.validate_on_submit():
        ResourceSource.create(
            name=form.name.data,
            category=form.category.data,
            url=form.url.data,
            notes=form.notes.data or None,
            user_id=current_user.id,
        )
        flash("Resource source saved.", "success")
        return redirect(url_for("resources.index"))
    if form.errors:
        flash_errors(form)

    personal_sources = (
        ResourceSource.query.filter_by(user_id=current_user.id)
        .order_by(ResourceSource.updated_at.desc())
        .all()
    )
    return render_template(
        "resources/index.html",
        form=form,
        curated_groups=_group_curated_sources(),
        personal_sources=personal_sources,
    )
