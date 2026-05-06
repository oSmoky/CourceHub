# CourseHub

CourseHub is a Flask and PostgreSQL prototype for an online course platform. It supports instructor and student roles, course and lesson CRUD, student enrollment, and lesson completion tracking.

## Project Structure

```text
app/
  routes/              Flask route blueprints
  static/css/          Application styles
  templates/           Bootstrap HTML templates
  __init__.py          App factory
  auth_utils.py        Login and role decorators
  extensions.py        SQLAlchemy extension
  models.py            Database models
bot/                   Optional Telegram bot interface
docs/                  SQL schema and Mermaid diagrams
scripts/               Database setup and seed scripts
tests/                 Pytest model tests
config.py              Environment-based configuration
run.py                 Local app entry point
requirements.txt       Python dependencies
```

## Setup

Prerequisites:

- Python 3.11 or newer
- PostgreSQL

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a PostgreSQL database named `coursehub`, then copy `.env.example` to `.env` and update `DATABASE_URL` if needed.

Initialize tables and optional demo data:

```powershell
python scripts/init_db.py
python scripts/seed.py
```

Run the application:

```powershell
flask --app run.py run
```

Run the optional Telegram bot after setting `TELEGRAM_BOT_TOKEN` in `.env`:

```powershell
python -m bot.main
```

Bot commands:

The bot shows a persistent command keyboard near the message box for common
actions, plus inline buttons inside bot messages.

- `/start` - main menu.
- `/register` - create a Telegram-linked student profile.
- `/courses` and `/course <id>` - browse course content.
- `/enroll <id>` - enroll from Telegram.
- `/mycourses`, `/progress <enrollment_id>`, and `/complete <enrollment_id> <lesson_no>` - track learning.
- `/webview` - open the full CourseHub WebView.

To open the app inside Telegram WebView, expose Flask through a public HTTPS URL
and set `TELEGRAM_WEB_APP_URL` to the `/telegram/` entrypoint:

```text
TELEGRAM_WEB_APP_URL=https://your-public-domain.example/telegram/
```

For local development, use an HTTPS tunnel such as ngrok or Cloudflare Tunnel,
then run Flask and the bot at the same time.

Demo accounts after seeding:

- Instructor: `instructor@coursehub.test` / `password`
- Student: `student@coursehub.test` / `password`

## Documentation

- SQL schema: `docs/database_schema.sql`
- Project report: `docs/project_report.md`
- Telegram bot notes: `docs/telegram_bot.md`
- ER diagram: `docs/er_diagram.mmd`
- Use case diagram: `docs/use_case_diagram.mmd`
- Enrollment sequence: `docs/sequence_enrollment.mmd`
- Progress sequence: `docs/sequence_progress.mmd`

## Tests

```powershell
pytest
```
