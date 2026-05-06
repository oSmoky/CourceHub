from flask import Blueprint, g, render_template

from app.models import Course, Enrollment


bp = Blueprint("courses", __name__)


@bp.route("/")
@bp.route("/courses")
def index():
    courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("courses/index.html", courses=courses)


@bp.route("/courses/<int:course_id>")
def detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment = None

    if g.user and g.user.is_student:
        enrollment = Enrollment.query.filter_by(
            user_id=g.user.user_id,
            course_id=course.course_id,
        ).first()

    return render_template("courses/detail.html", course=course, enrollment=enrollment)

