from functools import wraps

from flask import abort, flash, g, redirect, session, url_for

from .extensions import db
from .models import User


def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("auth.login"))
            allowed_roles = {role} if isinstance(role, str) else set(role)
            if g.user.role not in allowed_roles:
                abort(403)
            return view(**kwargs)

        return wrapped_view

    return decorator
