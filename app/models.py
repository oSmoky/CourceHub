from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint("role IN ('student', 'instructor', 'admin')", name="ck_users_role"),
    )

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    courses = db.relationship("Course", back_populates="instructor", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_instructor(self):
        return self.role == "instructor"

    @property
    def is_student(self):
        return self.role == "student"

    @property
    def is_admin(self):
        return self.role == "admin"


class Course(db.Model):
    __tablename__ = "courses"
    __table_args__ = (
        db.CheckConstraint("level IN ('Beginner', 'Intermediate', 'Advanced')", name="ck_courses_level"),
    )

    course_id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    instructor = db.relationship("User", back_populates="courses")
    lessons = db.relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Lesson.display_order",
    )
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    @property
    def student_count(self):
        return len(self.enrollments)


class Lesson(db.Model):
    __tablename__ = "lessons"
    __table_args__ = (
        db.CheckConstraint("display_order > 0", name="ck_lessons_display_order_positive"),
        db.CheckConstraint("duration_min >= 0", name="ck_lessons_duration_non_negative"),
    )

    lesson_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(150), nullable=False)
    video_url = db.Column(db.Text, nullable=False)
    display_order = db.Column(db.Integer, nullable=False)
    duration_min = db.Column(db.Integer, nullable=False, default=0)

    course = db.relationship("Course", back_populates="lessons")
    progress_records = db.relationship("Progress", back_populates="lesson", cascade="all, delete-orphan")


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),
        db.CheckConstraint("status IN ('active', 'completed', 'dropped')", name="ck_enrollments_status"),
    )

    enrollment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="active")

    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
    progress_records = db.relationship(
        "Progress",
        back_populates="enrollment",
        cascade="all, delete-orphan",
    )

    @property
    def progress_percent(self):
        total_lessons = len(self.course.lessons)
        if total_lessons == 0:
            return 0
        completed = sum(1 for row in self.progress_records if row.is_completed)
        return round((completed / total_lessons) * 100)


class Progress(db.Model):
    __tablename__ = "progress"
    __table_args__ = (
        db.UniqueConstraint("enrollment_id", "lesson_id", name="uq_progress_enrollment_lesson"),
    )

    progress_id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(
        db.Integer,
        db.ForeignKey("enrollments.enrollment_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id = db.Column(
        db.Integer,
        db.ForeignKey("lessons.lesson_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completion_date = db.Column(db.Date)

    enrollment = db.relationship("Enrollment", back_populates="progress_records")
    lesson = db.relationship("Lesson", back_populates="progress_records")
