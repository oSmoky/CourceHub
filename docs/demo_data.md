# Demo Data

Run this command after the production database is connected:

```powershell
python scripts/seed.py
```

The script is idempotent: running it again updates the same demo users, courses,
lessons, enrollments, and passwords.

## Admin

| Name | Email | Password |
| --- | --- | --- |
| Main Admin | admin@coursehub.test | admin123 |

## Instructors

| Name | Email | Password | Subjects / Courses |
| --- | --- | --- | --- |
| Demo Instructor | instructor@coursehub.test | teacher123 | Python Fundamentals |
| Aziz Nurmatov | aziz@coursehub.test | aziz123 | Flask Web Apps, PostgreSQL for Product Apps |
| Malika Karimova | malika@coursehub.test | malika123 | UI Design for Learning Platforms, Product Management Basics |
| Rustam Tursunov | rustam@coursehub.test | rustam123 | Git and Deployment Workflow, JavaScript Essentials |
| Kamila Sattorova | kamila@coursehub.test | kamila123 | English for IT Interviews |

## Students

| Name | Email | Password |
| --- | --- | --- |
| Demo Student | student@coursehub.test | student123 |
| Sardor Usmonov | sardor@coursehub.test | sardor123 |
| Nilufar Akramova | nilufar@coursehub.test | nilufar123 |
| Diana Lee | diana@coursehub.test | diana123 |
| Jasur Olimov | jasur@coursehub.test | jasur123 |
| Madina Rasulova | madina@coursehub.test | madina123 |
| Timur Karimov | timur@coursehub.test | timur123 |
| Aziza Hamidova | aziza@coursehub.test | aziza123 |
| Bekzod Aliyev | bekzod@coursehub.test | bekzod123 |
| Sevara Yuldasheva | sevara@coursehub.test | sevara123 |
| Oybek Rahmonov | oybek@coursehub.test | oybek123 |
| Lola Ismoilova | lola@coursehub.test | lola123 |
| Sherzod Qodirov | sherzod@coursehub.test | sherzod123 |
| Gulnoza Sobirova | gulnoza@coursehub.test | gulnoza123 |
| Farrukh Mansurov | farrukh@coursehub.test | farrukh123 |

## Courses

| Course | Subject | Level | Instructor | Lessons |
| --- | --- | --- | --- | --- |
| Python Fundamentals | Programming | Beginner | Demo Instructor | 5 |
| Flask Web Apps | Backend | Intermediate | Aziz Nurmatov | 5 |
| UI Design for Learning Platforms | Design | Beginner | Malika Karimova | 4 |
| PostgreSQL for Product Apps | Databases | Advanced | Aziz Nurmatov | 4 |
| Git and Deployment Workflow | DevOps | Beginner | Rustam Tursunov | 4 |
| English for IT Interviews | English | Intermediate | Kamila Sattorova | 5 |
| JavaScript Essentials | Frontend | Beginner | Rustam Tursunov | 5 |
| Product Management Basics | Product | Intermediate | Malika Karimova | 5 |

Each student is enrolled in two courses with different completion progress, so
the student dashboard and admin enrollment controls have real data to show.
