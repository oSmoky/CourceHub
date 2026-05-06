# CourseHub: Web-Based Online Course Platform Using Python and PostgreSQL

## 1. Introduction

CourseHub is a simplified online course platform designed for core educational workflows. The system allows instructors to create courses and publish lessons, while students can browse courses, enroll, access lessons, and track completion progress.

The project focuses on database-driven functionality that is easy to explain in a classroom setting: users, courses, lessons, enrollments, and progress records are stored in a relational PostgreSQL database.

## 2. Problem Statement

Many commercial learning platforms contain advanced features such as payments, recommendations, certificates, and live video tools. These features increase technical complexity and make it harder to study the core database design behind an e-learning system.

CourseHub solves this by focusing only on essential modules required for course delivery and progress tracking.

## 3. Objectives

- Design a relational database for users, courses, lessons, enrollments, and progress records.
- Build a Python-based web application with instructor and student roles.
- Enable instructors to create courses and upload lesson content.
- Allow students to enroll in courses and access lessons.
- Track lesson completion status and display course progress.
- Demonstrate CRUD operations on the main system entities.

## 4. System Overview

CourseHub has two main user roles:

- Instructor: creates courses, edits course information, adds lessons, updates lessons, and removes course content.
- Student: browses available courses, enrolls in selected courses, opens lesson resources, and marks lessons as completed.

All operational data is stored through SQLAlchemy models connected to PostgreSQL.

## 5. Main Modules

| Module | Purpose |
| --- | --- |
| User Management | Registration, login, logout, authentication, and role-based access. |
| Course Management | Instructor CRUD operations for course records. |
| Lesson Management | Instructor CRUD operations for lessons inside courses. |
| Enrollment Management | Student enrollment records for selected courses. |
| Progress Tracking | Completion records for each lesson within an enrollment. |

## 6. Tools and Technologies

| Component | Technology |
| --- | --- |
| Programming Language | Python |
| Framework | Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Frontend | HTML, CSS, Bootstrap |
| Development Tools | VS Code, Git-compatible project layout |

## 7. Database Design

The database uses five main entities:

- Users
- Courses
- Lessons
- Enrollments
- Progress

The full PostgreSQL schema is available in `database_schema.sql`, and the ER diagram is available in `er_diagram.mmd`.

## 8. Functional Requirements

- Users can register, log in, and log out.
- Instructors can create, update, view, and delete courses.
- Instructors can add, update, view, and delete lessons within their own courses.
- Students can browse courses and enroll in selected courses.
- Students can mark lessons as completed and view progress percentage.
- The system restricts instructor and student actions according to role.

## 9. CRUD Operations

| Operation | Examples |
| --- | --- |
| Create | User account, course, lesson, enrollment, progress record. |
| Read | Course list, lesson list, enrollment dashboard, progress percentage. |
| Update | Course details, lesson details, completion status. |
| Delete | Course records and lesson records by instructor. |

## 10. Expected Outcome

The final result is a working Flask web application prototype with PostgreSQL database design, role-based workflows, Bootstrap templates, and professional system documentation suitable for a database applications course.

## 11. Screenshot Plan

The report screenshots are listed in `figure_checklist.md`. The checklist
includes the requested Figure 2 through Figure 10 items, plus Figure 1 for the
course catalog overview and optional extra figures for the admin panel and
Telegram WebView interface.
