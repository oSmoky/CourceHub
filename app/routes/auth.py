from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import User


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "danger")
        elif role not in {"student", "instructor"}:
            flash("Please choose a valid role.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user.user_id
            flash(f"Welcome back, {user.name}.", "success")
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            if user.is_instructor:
                return redirect(url_for("instructor.dashboard"))
            return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("courses.index"))
