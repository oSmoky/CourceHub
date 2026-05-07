from flask import Flask, g

from config import Config

from .auth_utils import load_logged_in_user, require_site_login
from .extensions import db
from .routes import admin, auth, courses, instructor, student, telegram_webapp


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if config_object:
        app.config.update(config_object)

    db.init_app(app)

    app.before_request(load_logged_in_user)
    app.before_request(require_site_login)

    @app.context_processor
    def inject_current_user():
        return {"current_user": getattr(g, "user", None)}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.register_blueprint(auth.bp)
    app.register_blueprint(courses.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(instructor.bp)
    app.register_blueprint(student.bp)
    app.register_blueprint(telegram_webapp.bp)

    return app
