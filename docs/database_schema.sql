CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    instructor_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    level VARCHAR(30) NOT NULL CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lessons (
    lesson_id SERIAL PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    video_url TEXT NOT NULL,
    display_order INT NOT NULL CHECK (display_order > 0),
    duration_min INT NOT NULL DEFAULT 0 CHECK (duration_min >= 0)
);

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    course_id INT NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped')),
    CONSTRAINT uq_enrollment_user_course UNIQUE (user_id, course_id)
);

CREATE TABLE progress (
    progress_id SERIAL PRIMARY KEY,
    enrollment_id INT NOT NULL REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    lesson_id INT NOT NULL REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completion_date DATE,
    CONSTRAINT uq_progress_enrollment_lesson UNIQUE (enrollment_id, lesson_id)
);

CREATE INDEX idx_courses_instructor_id ON courses(instructor_id);
CREATE INDEX idx_lessons_course_id ON lessons(course_id);
CREATE INDEX idx_enrollments_user_id ON enrollments(user_id);
CREATE INDEX idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX idx_progress_enrollment_id ON progress(enrollment_id);
CREATE INDEX idx_progress_lesson_id ON progress(lesson_id);
