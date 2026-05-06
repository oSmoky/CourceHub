import pytest

from app import create_app
from app.extensions import db
from app.models import Course, Enrollment, Lesson, Progress, User


@pytest.fixture()
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


def test_password_hashing(app):
    user = User(name="Student", email="student@example.com", role="student")
    user.set_password("secret")

    assert user.password_hash != "secret"
    assert user.check_password("secret")
    assert not user.check_password("wrong")


def test_enrollment_progress_percentage(app):
    instructor = User(name="Instructor", email="teacher@example.com", role="instructor")
    instructor.set_password("secret")
    student = User(name="Student", email="student@example.com", role="student")
    student.set_password("secret")
    db.session.add_all([instructor, student])
    db.session.flush()

    course = Course(
        instructor_id=instructor.user_id,
        title="Databases",
        description="Relational database basics.",
        level="Beginner",
    )
    db.session.add(course)
    db.session.flush()

    first_lesson = Lesson(course_id=course.course_id, title="Tables", video_url="https://example.com/1", display_order=1, duration_min=10)
    second_lesson = Lesson(course_id=course.course_id, title="Keys", video_url="https://example.com/2", display_order=2, duration_min=10)
    db.session.add_all([first_lesson, second_lesson])
    db.session.flush()

    enrollment = Enrollment(user_id=student.user_id, course_id=course.course_id)
    db.session.add(enrollment)
    db.session.flush()
    db.session.add_all(
        [
            Progress(enrollment_id=enrollment.enrollment_id, lesson_id=first_lesson.lesson_id, is_completed=True),
            Progress(enrollment_id=enrollment.enrollment_id, lesson_id=second_lesson.lesson_id, is_completed=False),
        ]
    )
    db.session.commit()

    assert enrollment.progress_percent == 50

