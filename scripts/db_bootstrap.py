from app.extensions import db


def create_or_update_schema():
    db.create_all()
    _migrate_sqlite_user_roles()
    _repair_sqlite_user_foreign_keys()


def _migrate_sqlite_user_roles():
    engine = db.engine
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        users_table = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).scalar()
        if not users_table or "'admin'" in users_table:
            return

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("PRAGMA legacy_alter_table=ON")
        connection.exec_driver_sql("ALTER TABLE users RENAME TO users_old")
        connection.exec_driver_sql(
            """
            CREATE TABLE users (
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (user_id),
                CONSTRAINT ck_users_role CHECK (role IN ('student', 'instructor', 'admin'))
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO users (user_id, name, email, password_hash, role, created_at)
            SELECT user_id, name, email, password_hash, role, created_at
            FROM users_old
            """
        )
        connection.exec_driver_sql("DROP TABLE users_old")
        connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
        connection.exec_driver_sql("PRAGMA legacy_alter_table=OFF")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def _repair_sqlite_user_foreign_keys():
    engine = db.engine
    with engine.begin() as connection:
        courses_table = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'courses'"
        ).scalar()
        enrollments_table = connection.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'enrollments'"
        ).scalar()

        if "users_old" not in f"{courses_table or ''}{enrollments_table or ''}":
            return

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("PRAGMA legacy_alter_table=ON")

        connection.exec_driver_sql("ALTER TABLE courses RENAME TO courses_old")
        connection.exec_driver_sql(
            """
            CREATE TABLE courses (
                course_id INTEGER NOT NULL,
                instructor_id INTEGER NOT NULL,
                title VARCHAR(150) NOT NULL,
                description TEXT NOT NULL,
                level VARCHAR(30) NOT NULL,
                created_at DATETIME NOT NULL,
                PRIMARY KEY (course_id),
                CONSTRAINT ck_courses_level CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
                FOREIGN KEY(instructor_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO courses (course_id, instructor_id, title, description, level, created_at)
            SELECT course_id, instructor_id, title, description, level, created_at
            FROM courses_old
            """
        )
        connection.exec_driver_sql("DROP TABLE courses_old")
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_courses_instructor_id ON courses (instructor_id)"
        )

        connection.exec_driver_sql("ALTER TABLE enrollments RENAME TO enrollments_old")
        connection.exec_driver_sql(
            """
            CREATE TABLE enrollments (
                enrollment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrollment_date DATE NOT NULL,
                status VARCHAR(20) NOT NULL,
                PRIMARY KEY (enrollment_id),
                CONSTRAINT uq_enrollment_user_course UNIQUE (user_id, course_id),
                CONSTRAINT ck_enrollments_status CHECK (status IN ('active', 'completed', 'dropped')),
                FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses (course_id) ON DELETE CASCADE
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO enrollments (enrollment_id, user_id, course_id, enrollment_date, status)
            SELECT enrollment_id, user_id, course_id, enrollment_date, status
            FROM enrollments_old
            """
        )
        connection.exec_driver_sql("DROP TABLE enrollments_old")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_enrollments_user_id ON enrollments (user_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_enrollments_course_id ON enrollments (course_id)")

        connection.exec_driver_sql("PRAGMA legacy_alter_table=OFF")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
