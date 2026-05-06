# Telegram Bot

The Telegram bot is an optional CourseHub catalog interface. It can show available courses and course details using the same PostgreSQL database as the Flask web application.

## Security

Do not hardcode the Telegram bot token in Python files. Store it in `.env` as `TELEGRAM_BOT_TOKEN`.

If a token was shared in chat, screenshots, Git history, or any public place, revoke it in BotFather and generate a new one.

## Telegram WebView

The bot can open CourseHub as a Telegram Mini App. Telegram requires the Web App
URL to be public HTTPS, so local `http://127.0.0.1:5000` will not open inside
Telegram clients.

Set the public WebView URL in `.env`:

```text
TELEGRAM_WEB_APP_URL=https://your-public-domain.example/telegram/
```

When a Telegram user opens this page, Flask validates Telegram `initData`, creates
or updates a student account, stores it in the session, and redirects the user to
the student dashboard.

For local development:

```powershell
flask --app run.py run
ngrok http 5000
```

Use the generated HTTPS forwarding URL as `PUBLIC_BASE_URL` or set the exact
`TELEGRAM_WEB_APP_URL`.

## Commands

The bot also shows a persistent command keyboard above the message box, so users
can tap common actions instead of remembering command syntax.

- `/start` - show bot help.
- `/help` - show all commands.
- `/register` - create or update the Telegram student profile.
- `/profile` - show the linked CourseHub student profile.
- `/webview` - open CourseHub in Telegram WebView.
- `/courses` - list recent available courses.
- `/course <id>` - show details for one course.
- `/enroll <id>` - enroll in a course after registration.
- `/mycourses` - list enrolled courses and progress.
- `/progress <enrollment_id>` - list lessons for an enrollment.
- `/complete <enrollment_id> <lesson_no>` - mark a lesson as completed.

## Run

Install dependencies and initialize the database first:

```powershell
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed.py
```

Set the token in `.env`:

```text
TELEGRAM_BOT_TOKEN=your-new-token-here
TELEGRAM_WEB_APP_URL=https://your-public-domain.example/telegram/
```

Start the bot:

```powershell
python -m bot.main
```
