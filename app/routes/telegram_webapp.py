from flask import Blueprint, current_app, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Course, Enrollment, Progress
from app.telegram_auth import TelegramAuthError, validate_web_app_init_data
from app.telegram_accounts import find_or_create_student


bp = Blueprint("telegram_webapp", __name__, url_prefix="/telegram")


@bp.get("/")
def index():
    return render_template("telegram/webapp.html")


@bp.get("/app")
def app_home():
    if g.user is None:
        return redirect(url_for("telegram_webapp.index"))

    enrollments = (
        Enrollment.query.filter_by(user_id=g.user.user_id)
        .order_by(Enrollment.enrollment_date.desc())
        .all()
    )
    courses = Course.query.order_by(Course.created_at.desc()).all()
    enrollment_by_course = {enrollment.course_id: enrollment for enrollment in enrollments}
    completed_lessons = sum(
        1
        for enrollment in enrollments
        for progress in enrollment.progress_records
        if progress.is_completed
    )
    total_lessons = sum(len(enrollment.course.lessons) for enrollment in enrollments)

    return render_template(
        "telegram/app.html",
        courses=courses,
        enrollments=enrollments,
        enrollment_by_course=enrollment_by_course,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
    )


@bp.post("/courses/<int:course_id>/enroll")
def enroll_course(course_id):
    if g.user is None:
        return redirect(url_for("telegram_webapp.index"))
    if not g.user.is_student:
        return redirect(url_for("telegram_webapp.app_home"))

    course = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(user_id=g.user.user_id, course_id=course.course_id).first()
    if enrollment is None:
        enrollment = Enrollment(user_id=g.user.user_id, course_id=course.course_id)
        db.session.add(enrollment)
        db.session.flush()

        for lesson in course.lessons:
            enrollment.progress_records.append(Progress(lesson=lesson))

        db.session.commit()

    return redirect(url_for("telegram_webapp.app_home"))


@bp.post("/auth")
def auth():
    init_data = _request_init_data()

    try:
        telegram_data = validate_web_app_init_data(
            init_data,
            current_app.config.get("TELEGRAM_BOT_TOKEN"),
        )
        telegram_user = telegram_data.get("user") or {}
        telegram_user_id = telegram_user.get("id")
        if not telegram_user_id:
            return jsonify({"error": "Telegram user data is missing."}), 400

        user, _created = find_or_create_student(telegram_user)
        session.clear()
        session["user_id"] = user.user_id
        session["telegram_user_id"] = str(telegram_user_id)
    except TelegramAuthError as exc:
        return jsonify({"error": str(exc)}), 401
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database is not ready."}), 503

    return jsonify({"redirectUrl": url_for("telegram_webapp.app_home")})


def _request_init_data():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return payload.get("initData", "")
    return request.form.get("initData", "")
