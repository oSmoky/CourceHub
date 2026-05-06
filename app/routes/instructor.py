from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.auth_utils import role_required
from app.extensions import db
from app.models import Course, Lesson


bp = Blueprint("instructor", __name__, url_prefix="/instructor")
VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}


def _parse_int(value, default, minimum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    if minimum is not None and parsed < minimum:
        return default
    return parsed


def _owned_course_or_404(course_id):
    return Course.query.filter_by(course_id=course_id, instructor_id=g.user.user_id).first_or_404()


def _owned_lesson_or_404(lesson_id):
    return (
        Lesson.query.join(Course)
        .filter(Lesson.lesson_id == lesson_id, Course.instructor_id == g.user.user_id)
        .first_or_404()
    )


@bp.route("/dashboard")
@role_required("instructor")
def dashboard():
    courses = Course.query.filter_by(instructor_id=g.user.user_id).order_by(Course.created_at.desc()).all()
    return render_template("instructor/dashboard.html", courses=courses)


@bp.route("/courses/new", methods=("GET", "POST"))
@role_required("instructor")
def create_course():
    if request.method == "POST":
        level = request.form.get("level", "Beginner")
        course = Course(
            instructor_id=g.user.user_id,
            title=request.form.get("title", "").strip(),
            description=request.form.get("description", "").strip(),
            level=level,
        )
        if not course.title or not course.description:
            flash("Title and description are required.", "danger")
        elif level not in VALID_LEVELS:
            flash("Please choose a valid course level.", "danger")
        else:
            db.session.add(course)
            db.session.commit()
            flash("Course created.", "success")
            return redirect(url_for("instructor.dashboard"))

    return render_template("instructor/course_form.html", course=None)


@bp.route("/courses/<int:course_id>/edit", methods=("GET", "POST"))
@role_required("instructor")
def edit_course(course_id):
    course = _owned_course_or_404(course_id)

    if request.method == "POST":
        level = request.form.get("level", "Beginner")
        course.title = request.form.get("title", "").strip()
        course.description = request.form.get("description", "").strip()
        course.level = level

        if not course.title or not course.description:
            flash("Title and description are required.", "danger")
        elif level not in VALID_LEVELS:
            flash("Please choose a valid course level.", "danger")
        else:
            db.session.commit()
            flash("Course updated.", "success")
            return redirect(url_for("instructor.dashboard"))

    return render_template("instructor/course_form.html", course=course)


@bp.route("/courses/<int:course_id>/delete", methods=("POST",))
@role_required("instructor")
def delete_course(course_id):
    course = _owned_course_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "info")
    return redirect(url_for("instructor.dashboard"))


@bp.route("/courses/<int:course_id>/lessons/new", methods=("GET", "POST"))
@role_required("instructor")
def create_lesson(course_id):
    course = _owned_course_or_404(course_id)

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

    return render_template("instructor/lesson_form.html", course=course, lesson=None)


@bp.route("/lessons/<int:lesson_id>/edit", methods=("GET", "POST"))
@role_required("instructor")
def edit_lesson(lesson_id):
    lesson = _owned_lesson_or_404(lesson_id)

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

    return render_template("instructor/lesson_form.html", course=lesson.course, lesson=lesson)


@bp.route("/lessons/<int:lesson_id>/delete", methods=("POST",))
@role_required("instructor")
def delete_lesson(lesson_id):
    lesson = _owned_lesson_or_404(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash("Lesson deleted.", "info")
    return redirect(url_for("courses.detail", course_id=course_id))
