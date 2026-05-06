from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, url_for

from app.auth_utils import role_required
from app.extensions import db
from app.models import Course, Enrollment, Progress


bp = Blueprint("student", __name__, url_prefix="/student")


def _sync_progress_records(enrollment):
    existing_lesson_ids = {row.lesson_id for row in enrollment.progress_records}
    for lesson in enrollment.course.lessons:
        if lesson.lesson_id not in existing_lesson_ids:
            enrollment.progress_records.append(Progress(lesson=lesson))


def _refresh_enrollment_status(enrollment):
    if enrollment.progress_records and all(row.is_completed for row in enrollment.progress_records):
        enrollment.status = "completed"
    else:
        enrollment.status = "active"


@bp.route("/dashboard")
@role_required("student")
def dashboard():
    enrollments = (
        Enrollment.query.filter_by(user_id=g.user.user_id)
        .order_by(Enrollment.enrollment_date.desc())
        .all()
    )
    return render_template("student/dashboard.html", enrollments=enrollments)


@bp.route("/courses/<int:course_id>/enroll", methods=("POST",))
@role_required("student")
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(user_id=g.user.user_id, course_id=course.course_id).first()

    if enrollment:
        flash("You are already enrolled in this course.", "info")
    else:
        enrollment = Enrollment(user_id=g.user.user_id, course_id=course.course_id)
        db.session.add(enrollment)
        db.session.flush()

        for lesson in course.lessons:
            enrollment.progress_records.append(Progress(lesson=lesson))

        db.session.commit()
        flash("Enrollment created.", "success")

    return redirect(url_for("student.enrollment_confirmation", enrollment_id=enrollment.enrollment_id))


@bp.route("/enrollments/<int:enrollment_id>/confirmed")
@role_required("student")
def enrollment_confirmation(enrollment_id):
    enrollment = Enrollment.query.filter_by(
        enrollment_id=enrollment_id,
        user_id=g.user.user_id,
    ).first_or_404()
    return render_template("student/enrollment_confirmation.html", enrollment=enrollment)


@bp.route("/enrollments/<int:enrollment_id>")
@role_required("student")
def learn(enrollment_id):
    enrollment = Enrollment.query.filter_by(
        enrollment_id=enrollment_id,
        user_id=g.user.user_id,
    ).first_or_404()

    _sync_progress_records(enrollment)
    _refresh_enrollment_status(enrollment)
    db.session.commit()

    progress_by_lesson = {row.lesson_id: row for row in enrollment.progress_records}
    return render_template(
        "student/learn.html",
        enrollment=enrollment,
        progress_by_lesson=progress_by_lesson,
    )


@bp.route("/progress/<int:progress_id>/toggle", methods=("POST",))
@role_required("student")
def toggle_progress(progress_id):
    progress = (
        Progress.query.join(Enrollment)
        .filter(Progress.progress_id == progress_id, Enrollment.user_id == g.user.user_id)
        .first_or_404()
    )

    progress.is_completed = not progress.is_completed
    progress.completion_date = date.today() if progress.is_completed else None
    _refresh_enrollment_status(progress.enrollment)
    db.session.commit()

    flash("Progress updated.", "success")
    return redirect(url_for("student.learn", enrollment_id=progress.enrollment_id))
