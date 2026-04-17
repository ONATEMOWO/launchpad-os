# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, redirect, url_for
from flask_login import login_required

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../static")


@blueprint.route("/")
@login_required
def members():
    """Redirect the old workspace page to the main app feature."""
    return redirect(url_for("opportunities.index"))
