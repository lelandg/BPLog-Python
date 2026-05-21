"""Flask app factory.

Constructs the Flask app with paths and settings injected via
`app.config`. Routes look up `current_app.config["bplog_paths"]` and
`current_app.config["bplog_settings"]` for runtime state.
"""
from __future__ import annotations

from typing import Optional

from flask import Flask

from . import db as db_mod
from . import settings as settings_mod
from .config import Paths


def create_app(
    paths: Paths,
    settings: Optional[settings_mod.Settings] = None,
    reminder_state=None,
    reminder_scheduler=None,
) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    paths.ensure()
    db_mod.initialize(paths.db)

    app.config["bplog_paths"] = paths
    app.config["bplog_settings"] = settings or settings_mod.load(paths.settings)

    from .routes.readings import bp as readings_bp
    from .routes.exports import bp as exports_bp
    from .routes.settings_ui import bp as settings_bp
    from .routes.vision import bp as vision_bp

    app.register_blueprint(readings_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(vision_bp)

    if reminder_state is not None and reminder_scheduler is not None:
        from .reminders import register_reminders

        register_reminders(app, reminder_scheduler, reminder_state)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
