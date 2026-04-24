# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging
import sys

from flask import Flask, render_template

from launchpad_os import (
    commands,
    materials,
    opportunities,
    public,
    requirements,
    resources,
    user,
    workspace,
)
from launchpad_os.extensions import (
    bcrypt,
    cache,
    csrf_protect,
    db,
    debug_toolbar,
    flask_static_digest,
    login_manager,
    migrate,
)


def _import_models():
    """Explicitly import every model module so SQLAlchemy metadata is complete.

    The top-level package imports in app.py reach user.models only through a
    transitive chain (public.views -> user.models). Making every model import
    explicit here guarantees all table definitions are registered with
    db.metadata before db.create_all() runs, regardless of import order or
    deployment-specific caching behaviour.
    """
    from launchpad_os.user import models as _user_models  # noqa: F401
    from launchpad_os.materials import models as _material_models  # noqa: F401
    from launchpad_os.opportunities import models as _opportunity_models  # noqa: F401
    from launchpad_os.requirements import models as _requirement_models  # noqa: F401
    from launchpad_os.resources import models as _resource_models  # noqa: F401


def create_app(config_object="launchpad_os.settings"):
    """Create application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    configure_logger(app)
    _import_models()
    with app.app_context():
        db.create_all()
        app.logger.info(
            "Startup: db.create_all() complete. Registered tables: %s",
            sorted(db.metadata.tables.keys()),
        )
    return app


def register_extensions(app):
    """Register Flask extensions."""
    bcrypt.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    login_manager.init_app(app)
    if app.debug:
        debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    flask_static_digest.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(opportunities.views.blueprint)
    app.register_blueprint(materials.views.blueprint)
    app.register_blueprint(requirements.views.blueprint)
    app.register_blueprint(resources.views.blueprint)
    app.register_blueprint(workspace.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {
            "db": db,
            "User": user.models.User,
            "Opportunity": opportunities.models.Opportunity,
            "OpportunityOutreach": opportunities.models.OpportunityOutreach,
            "OpportunityTag": opportunities.models.OpportunityTag,
            "Material": materials.models.Material,
            "RequirementItem": requirements.models.RequirementItem,
            "ResourceSource": resources.models.ResourceSource,
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)


def configure_logger(app):
    """Configure loggers."""
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)
