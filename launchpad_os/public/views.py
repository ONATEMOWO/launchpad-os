# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from launchpad_os.extensions import login_manager
from launchpad_os.public.forms import LoginForm
from launchpad_os.user.forms import RegisterForm
from launchpad_os.user.models import User
from launchpad_os.utils import flash_errors

blueprint = Blueprint("public", __name__, static_folder="../static")


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.get_by_id(int(user_id))


def _handle_login(form):
    """Validate the login form and redirect to the workspace."""
    if form.validate_on_submit():
        login_user(form.user)
        flash("You are logged in.", "success")
        redirect_url = request.args.get("next") or url_for("opportunities.index")
        return redirect(redirect_url)
    flash_errors(form)
    return None


@blueprint.route("/")
def home():
    """Home page."""
    current_app.logger.info("Hello from the home page!")
    return render_template("public/home.html")


@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    """Login page."""
    if current_user and current_user.is_authenticated:
        return redirect(url_for("opportunities.index"))

    form = LoginForm(request.form)
    if request.method == "POST":
        response = _handle_login(form)
        if response is not None:
            return response
    return render_template("public/login.html", form=form)


@blueprint.route("/logout/")
@login_required
def logout():
    """Logout."""
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("public.home"))


@blueprint.route("/register/", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            active=True,
        )
        flash("Thank you for registering. You can now sign in.", "success")
        return redirect(url_for("public.login"))
    else:
        flash_errors(form)
    return render_template("public/register.html", form=form)


@blueprint.route("/about/")
def about():
    """Project overview page."""
    return render_template("public/about.html")
