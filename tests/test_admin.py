import pytest

from app import create_app
from app.extensions import db
from app.models import Course, User


@pytest.fixture()
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with test_app.app_context():
        db.create_all()
        admin = User(name="Admin", email="admin@example.com", role="admin")
        admin.set_password("secret")
        instructor = User(name="Instructor", email="teacher@example.com", role="instructor")
        instructor.set_password("secret")
        db.session.add_all([admin, instructor])
        db.session.commit()
        yield test_app
        db.drop_all()


def test_admin_login_redirects_to_dashboard(app):
    client = app.test_client()

    response = client.post(
        "/auth/login",
        data={"email": "admin@example.com", "password": "secret"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Admin Panel" in response.data


def test_login_page_uses_standalone_auth_layout(app):
    response = app.test_client().get("/auth/login")

    assert response.status_code == 200
    assert b'class="auth-page"' in response.data
    assert b"app-navbar" not in response.data
    assert b'href="/courses"' not in response.data


def test_admin_can_create_course_for_instructor(app):
    client = app.test_client()
    client.post(
        "/auth/login",
        data={"email": "admin@example.com", "password": "secret"},
    )
    instructor = User.query.filter_by(email="teacher@example.com").first()

    response = client.post(
        "/admin/courses/new",
        data={
            "title": "Git and Deployment",
            "description": "Publish a working product with clean version control.",
            "level": "Intermediate",
            "instructor_id": str(instructor.user_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert Course.query.filter_by(title="Git and Deployment").first() is not None
