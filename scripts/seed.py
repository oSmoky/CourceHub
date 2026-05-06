import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.extensions import db
from app.models import Course, Enrollment, Lesson, Progress, User
from scripts.db_bootstrap import create_or_update_schema


app = create_app()

ADMIN_ACCOUNT = ("Main Admin", "admin@coursehub.test", "admin", "admin123")

INSTRUCTOR_ACCOUNTS = [
    ("Demo Instructor", "instructor@coursehub.test", "instructor", "teacher123"),
    ("Aziz Nurmatov", "aziz@coursehub.test", "instructor", "aziz123"),
    ("Malika Karimova", "malika@coursehub.test", "instructor", "malika123"),
    ("Rustam Tursunov", "rustam@coursehub.test", "instructor", "rustam123"),
    ("Kamila Sattorova", "kamila@coursehub.test", "instructor", "kamila123"),
]

STUDENT_ACCOUNTS = [
    ("Demo Student", "student@coursehub.test", "student", "student123"),
    ("Sardor Usmonov", "sardor@coursehub.test", "student", "sardor123"),
    ("Nilufar Akramova", "nilufar@coursehub.test", "student", "nilufar123"),
    ("Diana Lee", "diana@coursehub.test", "student", "diana123"),
    ("Jasur Olimov", "jasur@coursehub.test", "student", "jasur123"),
    ("Madina Rasulova", "madina@coursehub.test", "student", "madina123"),
    ("Timur Karimov", "timur@coursehub.test", "student", "timur123"),
    ("Aziza Hamidova", "aziza@coursehub.test", "student", "aziza123"),
    ("Bekzod Aliyev", "bekzod@coursehub.test", "student", "bekzod123"),
    ("Sevara Yuldasheva", "sevara@coursehub.test", "student", "sevara123"),
    ("Oybek Rahmonov", "oybek@coursehub.test", "student", "oybek123"),
    ("Lola Ismoilova", "lola@coursehub.test", "student", "lola123"),
    ("Sherzod Qodirov", "sherzod@coursehub.test", "student", "sherzod123"),
    ("Gulnoza Sobirova", "gulnoza@coursehub.test", "student", "gulnoza123"),
    ("Farrukh Mansurov", "farrukh@coursehub.test", "student", "farrukh123"),
]

COURSE_SPECS = [
    {
        "instructor_email": "instructor@coursehub.test",
        "title": "Python Fundamentals",
        "description": "Subject: Programming. Python syntax, control flow, functions, files, and a small Telegram quiz project.",
        "level": "Beginner",
        "lessons": [
            ("Getting Started with Python", "https://example.com/python-1", 1, 12),
            ("Variables, Types, and Input", "https://example.com/python-2", 2, 18),
            ("Conditions and Loops", "https://example.com/python-3", 3, 22),
            ("Functions and Modules", "https://example.com/python-4", 4, 25),
            ("Mini Project: Telegram Quiz", "https://example.com/python-5", 5, 35),
        ],
    },
    {
        "instructor_email": "aziz@coursehub.test",
        "title": "Flask Web Apps",
        "description": "Subject: Backend. Build routes, templates, forms, database models, auth, and deployment-ready Flask services.",
        "level": "Intermediate",
        "lessons": [
            ("Project Structure", "https://example.com/flask-1", 1, 16),
            ("Templates and Forms", "https://example.com/flask-2", 2, 24),
            ("SQLAlchemy Models", "https://example.com/flask-3", 3, 28),
            ("Auth and Roles", "https://example.com/flask-4", 4, 31),
            ("Deploying to Render", "https://example.com/flask-5", 5, 22),
        ],
    },
    {
        "instructor_email": "malika@coursehub.test",
        "title": "UI Design for Learning Platforms",
        "description": "Subject: Design. Dashboards, course cards, progress states, mobile layouts, and accessible forms.",
        "level": "Beginner",
        "lessons": [
            ("Dashboard Layouts", "https://example.com/ui-1", 1, 14),
            ("Course Detail Pages", "https://example.com/ui-2", 2, 19),
            ("Progress and Empty States", "https://example.com/ui-3", 3, 17),
            ("Responsive Polish", "https://example.com/ui-4", 4, 21),
        ],
    },
    {
        "instructor_email": "aziz@coursehub.test",
        "title": "PostgreSQL for Product Apps",
        "description": "Subject: Databases. Schemas, constraints, relationships, indexes, seed data, and production checks.",
        "level": "Advanced",
        "lessons": [
            ("Tables and Constraints", "https://example.com/postgres-1", 1, 26),
            ("Relationships and Indexes", "https://example.com/postgres-2", 2, 29),
            ("Seed Data and Backups", "https://example.com/postgres-3", 3, 23),
            ("Production Readiness", "https://example.com/postgres-4", 4, 33),
        ],
    },
    {
        "instructor_email": "rustam@coursehub.test",
        "title": "Git and Deployment Workflow",
        "description": "Subject: DevOps. Git basics, branches, commits, GitHub, Render deployment, logs, and rollback habits.",
        "level": "Beginner",
        "lessons": [
            ("Git Setup and First Commit", "https://example.com/git-1", 1, 18),
            ("Branches and Pull Requests", "https://example.com/git-2", 2, 24),
            ("Environment Variables", "https://example.com/git-3", 3, 17),
            ("Render Deploy Checklist", "https://example.com/git-4", 4, 28),
        ],
    },
    {
        "instructor_email": "kamila@coursehub.test",
        "title": "English for IT Interviews",
        "description": "Subject: English. Vocabulary, self-introduction, project explanation, interview answers, and email etiquette.",
        "level": "Intermediate",
        "lessons": [
            ("Developer Vocabulary", "https://example.com/english-1", 1, 20),
            ("Self Introduction", "https://example.com/english-2", 2, 18),
            ("Explaining a Project", "https://example.com/english-3", 3, 22),
            ("Interview Questions", "https://example.com/english-4", 4, 30),
            ("Professional Emails", "https://example.com/english-5", 5, 15),
        ],
    },
    {
        "instructor_email": "rustam@coursehub.test",
        "title": "JavaScript Essentials",
        "description": "Subject: Frontend. Variables, DOM events, async requests, local state, and small browser apps.",
        "level": "Beginner",
        "lessons": [
            ("JS Syntax", "https://example.com/js-1", 1, 16),
            ("DOM and Events", "https://example.com/js-2", 2, 23),
            ("Arrays and Objects", "https://example.com/js-3", 3, 25),
            ("Fetch and Async", "https://example.com/js-4", 4, 27),
            ("Mini Project: Course Filter", "https://example.com/js-5", 5, 32),
        ],
    },
    {
        "instructor_email": "malika@coursehub.test",
        "title": "Product Management Basics",
        "description": "Subject: Product. User stories, prioritization, MVP planning, metrics, and release notes.",
        "level": "Intermediate",
        "lessons": [
            ("User Problems and Personas", "https://example.com/product-1", 1, 21),
            ("Writing User Stories", "https://example.com/product-2", 2, 19),
            ("Prioritization", "https://example.com/product-3", 3, 24),
            ("MVP Scope", "https://example.com/product-4", 4, 26),
            ("Metrics and Feedback", "https://example.com/product-5", 5, 18),
        ],
    },
]

ENROLLMENT_PLAN = {
    "student@coursehub.test": [("Python Fundamentals", 3), ("Git and Deployment Workflow", 1)],
    "sardor@coursehub.test": [("Python Fundamentals", 5), ("Flask Web Apps", 2)],
    "nilufar@coursehub.test": [("UI Design for Learning Platforms", 3), ("Product Management Basics", 1)],
    "diana@coursehub.test": [("Flask Web Apps", 0), ("English for IT Interviews", 2)],
    "jasur@coursehub.test": [("JavaScript Essentials", 2), ("Git and Deployment Workflow", 4)],
    "madina@coursehub.test": [("Product Management Basics", 4), ("UI Design for Learning Platforms", 2)],
    "timur@coursehub.test": [("PostgreSQL for Product Apps", 1), ("Flask Web Apps", 3)],
    "aziza@coursehub.test": [("English for IT Interviews", 5), ("Python Fundamentals", 2)],
    "bekzod@coursehub.test": [("Git and Deployment Workflow", 0), ("JavaScript Essentials", 3)],
    "sevara@coursehub.test": [("UI Design for Learning Platforms", 4), ("English for IT Interviews", 1)],
    "oybek@coursehub.test": [("PostgreSQL for Product Apps", 2), ("Python Fundamentals", 4)],
    "lola@coursehub.test": [("Product Management Basics", 2), ("JavaScript Essentials", 1)],
    "sherzod@coursehub.test": [("Flask Web Apps", 5), ("PostgreSQL for Product Apps", 3)],
    "gulnoza@coursehub.test": [("English for IT Interviews", 3), ("UI Design for Learning Platforms", 1)],
    "farrukh@coursehub.test": [("Git and Deployment Workflow", 2), ("Python Fundamentals", 0)],
}


def ensure_user(name, email, role, password):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, role=role)
        db.session.add(user)

    user.name = name
    user.role = role
    user.set_password(password)
    db.session.flush()
    return user


def ensure_course(spec, instructors_by_email):
    instructor = instructors_by_email[spec["instructor_email"]]
    course = Course.query.filter_by(title=spec["title"]).first()
    if not course:
        course = Course(title=spec["title"])
        db.session.add(course)

    course.instructor_id = instructor.user_id
    course.description = spec["description"]
    course.level = spec["level"]
    db.session.flush()

    existing_lessons = {lesson.display_order: lesson for lesson in course.lessons}
    for title, video_url, display_order, duration_min in spec["lessons"]:
        lesson = existing_lessons.get(display_order)
        if not lesson:
            lesson = Lesson(course_id=course.course_id, display_order=display_order)
            db.session.add(lesson)

        lesson.title = title
        lesson.video_url = video_url
        lesson.duration_min = duration_min

    db.session.flush()
    return course


def ensure_enrollment(student, course, completed_count):
    enrollment = Enrollment.query.filter_by(user_id=student.user_id, course_id=course.course_id).first()
    if not enrollment:
        enrollment = Enrollment(user_id=student.user_id, course_id=course.course_id)
        db.session.add(enrollment)
        db.session.flush()

    existing_progress = {row.lesson_id: row for row in enrollment.progress_records}
    for lesson in course.lessons:
        progress = existing_progress.get(lesson.lesson_id)
        if not progress:
            progress = Progress(enrollment_id=enrollment.enrollment_id, lesson_id=lesson.lesson_id)
            db.session.add(progress)

        progress.is_completed = lesson.display_order <= completed_count
        progress.completion_date = date.today() if progress.is_completed else None

    enrollment.status = "completed" if completed_count >= len(course.lessons) else "active"
    return enrollment


with app.app_context():
    create_or_update_schema()

    admin = ensure_user(*ADMIN_ACCOUNT)
    instructors = [ensure_user(*account) for account in INSTRUCTOR_ACCOUNTS]
    students = [ensure_user(*account) for account in STUDENT_ACCOUNTS]

    instructors_by_email = {user.email: user for user in instructors}
    students_by_email = {user.email: user for user in students}

    courses = [ensure_course(spec, instructors_by_email) for spec in COURSE_SPECS]
    courses_by_title = {course.title: course for course in courses}

    for student_email, enrollments in ENROLLMENT_PLAN.items():
        for course_title, completed_count in enrollments:
            ensure_enrollment(
                students_by_email[student_email],
                courses_by_title[course_title],
                completed_count,
            )

    db.session.commit()

    print("Demo database is ready.")
    print(f"Admin: {admin.email} / {ADMIN_ACCOUNT[3]}")
    print(f"Instructors: {len(instructors)}")
    print(f"Students: {len(students)}")
    print(f"Courses: {len(courses)}")
