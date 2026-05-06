# Figure Checklist

Use this checklist when preparing the final report screenshots.

| Figure | Screenshot / Output to Insert | Where to Capture |
| --- | --- | --- |
| Figure 1 | System home page or CourseHub course catalog overview | `/courses` |
| Figure 2 | User registration page | `/auth/register` |
| Figure 3 | Login page | `/auth/login` |
| Figure 4 | Instructor dashboard | `/instructor/dashboard` |
| Figure 5 | Course creation page | `/instructor/courses/new` |
| Figure 6 | Lesson management page | Course detail page as instructor, with lesson actions visible |
| Figure 7 | Student course browsing page | `/courses` as a student |
| Figure 8 | Enrollment confirmation page | `/student/enrollments/<enrollment_id>/confirmed` after enrolling |
| Figure 9 | Progress tracking page | `/student/enrollments/<enrollment_id>` |
| Figure 10 | Database tables or SQL query output | Render PostgreSQL query result, SQLite query result, or `docs/database_schema.sql` |
| Figure 11 | Admin management panel, additional option not in the original list | `/admin/` |
| Figure 12 | Telegram WebView mobile dashboard, additional option for bot interface | `/telegram/app` inside Telegram |

Recommended demo accounts:

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@coursehub.test | admin123 |
| Instructor | instructor@coursehub.test | teacher123 |
| Student | student@coursehub.test | student123 |
