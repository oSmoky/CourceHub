from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth_utils import role_required
from app.extensions import db
from app.models import Course, Enrollment, Lesson, User


bp = Blueprint("admin", __name__, url_prefix="/admin")
VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}
VALID_ROLES = {"student", "instructor", "admin"}
VALID_ENROLLMENT_STATUSES = {"active", "completed", "dropped"}


def _parse_int(value, default, minimum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    if minimum is not None and parsed < minimum:
        return default
    return parsed


def _instructor_choices():
    return User.query.filter(User.role.in_(("instructor", "admin"))).order_by(User.name).all()


@bp.route("/")
@role_required("admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    courses = Course.query.order_by(Course.created_at.desc()).all()
    enrollments = Enrollment.query.order_by(Enrollment.enrollment_date.desc()).all()
    return render_template(
        "admin/dashboard.html",
        users=users,
        courses=courses,
        enrollments=enrollments,
    )


@bp.route("/users/new", methods=("GET", "POST"))
@role_required("admin")
def create_user():
    if request.method == "POST":
        user = User(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            role=request.form.get("role", "student"),
        )
        password = request.form.get("password", "")

        if not user.name or not user.email or not password:
            flash("Name, email, and password are required.", "danger")
        elif user.role not in VALID_ROLES:
            flash("Please choose a valid role.", "danger")
        elif User.query.filter_by(email=user.email).first():
            flash("This email is already registered.", "danger")
        else:
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("User created.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/user_form.html", user=None, roles=sorted(VALID_ROLES))


@bp.route("/users/<int:user_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit_user(user_id):
    user = db.session.get(User, user_id) or User.query.get_or_404(user_id)

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "student")
        existing_user = User.query.filter(User.email == email, User.user_id != user.user_id).first()

        user.name = request.form.get("name", "").strip()
        user.email = email
        user.role = role
        password = request.form.get("password", "")

        if not user.name or not user.email:
            flash("Name and email are required.", "danger")
        elif role not in VALID_ROLES:
            flash("Please choose a valid role.", "danger")
        elif existing_user:
            flash("This email is already registered.", "danger")
        else:
            if password:
                user.set_password(password)
            db.session.commit()
            flash("User updated.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/user_form.html", user=user, roles=sorted(VALID_ROLES))


@bp.route("/users/<int:user_id>/delete", methods=("POST",))
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin" and User.query.filter_by(role="admin").count() <= 1:
        flash("Keep at least one admin account.", "warning")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "info")
    return redirect(url_for("admin.dashboard"))


@bp.route("/courses/new", methods=("GET", "POST"))
@role_required("admin")
def create_course():
    instructors = _instructor_choices()

    if request.method == "POST":
        level = request.form.get("level", "Beginner")
        course = Course(
            instructor_id=_parse_int(request.form.get("instructor_id"), default=0, minimum=1),
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            level=level,
        )

        if not course.title or not course.description:
            flash("Title and description are required.", "danger")
        elif level not in VALID_LEVELS:
            flash("Please choose a valid course level.", "danger")
        elif course.instructor_id not in {user.user_id for user in instructors}:
            flash("Please choose an instructor.", "danger")
        else:
            db.session.add(course)
            db.session.commit()
            flash("Course created.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/course_form.html", course=None, instructors=instructors)


@bp.route("/courses/<int:course_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    instructors = _instructor_choices()

    if request.method == "POST":
        level = request.form.get("level", "Beginner")
        instructor_id = _parse_int(request.form.get("instructor_id"), default=0, minimum=1)
        course.title = request.form.get("title", "").strip()
        course.description = request.form.get("description", "").strip()
        course.level = level
        course.instructor_id = instructor_id

        if not course.title or not course.description:
            flash("Title and description are required.", "danger")
        elif level not in VALID_LEVELS:
            flash("Please choose a valid course level.", "danger")
        elif instructor_id not in {user.user_id for user in instructors}:
            flash("Please choose an instructor.", "danger")
        else:
            db.session.commit()
            flash("Course updated.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/course_form.html", course=course, instructors=instructors)


@bp.route("/courses/<int:course_id>/delete", methods=("POST",))
@role_required("admin")
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("admin.dashboard"))


@bp.route("/courses/<int:course_id>/lessons/new", methods=("GET", "POST"))
@role_required("admin")
def create_lesson(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        lesson = Lesson(
            course_id=course.course_id,
            title=request.form.get("title", "").strip(),
            video_url=request.form.get("video_url", "").strip(),
            display_order=_parse_int(request.form.get("display_order"), default=1, minimum=1),
            duration_min=_parse_int(request.form.get("duration_min"), default=0, minimum=0),
        )

        if not lesson.title or not lesson.video_url:
            flash("Lesson title and video URL are required.", "danger")
        else:
            db.session.add(lesson)
            db.session.commit()
            flash("Lesson added.", "success")
            return redirect(url_for("courses.detail", course_id=course.course_id))

    return render_template("admin/lesson_form.html", course=course, lesson=None)


@bp.route("/lessons/<int:lesson_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)

    if request.method == "POST":
        lesson.title = request.form.get("title", "").strip()
        lesson.video_url = request.form.get("video_url", "").strip()
        lesson.display_order = _parse_int(request.form.get("display_order"), default=1, minimum=1)
        lesson.duration_min = _parse_int(request.form.get("duration_min"), default=0, minimum=0)

        if not lesson.title or not lesson.video_url:
            flash("Lesson title and video URL are required.", "danger")
        else:
            db.session.commit()
            flash("Lesson updated.", "success")
            return redirect(url_for("courses.detail", course_id=lesson.course_id))

    return render_template("admin/lesson_form.html", course=lesson.course, lesson=lesson)


@bp.route("/lessons/<int:lesson_id>/delete", methods=("POST",))
@role_required("admin")
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash("Lesson deleted.", "info")
    return redirect(url_for("courses.detail", course_id=course_id))


@bp.route("/enrollments/<int:enrollment_id>/status", methods=("POST",))
@role_required("admin")
def update_enrollment_status(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    status = request.form.get("status", "active")
    if status not in VALID_ENROLLMENT_STATUSES:
        flash("Please choose a valid enrollment status.", "danger")
    else:
        enrollment.status = status
        db.session.commit()
        flash("Enrollment updated.", "success")
    return redirect(url_for("admin.dashboard"))


@bp.route("/enrollments/<int:enrollment_id>/delete", methods=("POST",))
@role_required("admin")
def delete_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash("Enrollment deleted.", "info")
    return redirect(url_for("admin.dashboard"))
