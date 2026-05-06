# Deployment

CourseHub needs two long-running processes in production:

- Web service: serves Flask and Telegram WebView.
- Bot worker: runs Telegram polling and handles commands/buttons.

Use PostgreSQL in production. SQLite is fine for local demos, but it is not a
good fit for a public multi-process deployment.

## Required Environment Variables

```text
SECRET_KEY=strong-random-secret
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
TELEGRAM_BOT_TOKEN=token-from-BotFather
PUBLIC_BASE_URL=https://your-public-domain.example
TELEGRAM_WEB_APP_URL=https://your-public-domain.example/telegram/
```

If `TELEGRAM_WEB_APP_URL` is empty, the bot builds it from `PUBLIC_BASE_URL` as
`/telegram/`.

## Render Setup

Create PostgreSQL first, then create two services from the same repository.

Web service:

```text
Build Command: pip install -r requirements.txt
Start Command: python scripts/init_db.py && python scripts/seed.py && gunicorn run:app
Health Check Path: /health
```

If Render shows this error:

```text
Couldn't find a package.json file in "/opt/render/project/src"
```

the service was created as Node.js or Static Site. CourseHub is a Python Flask
app, so do not add `package.json`. Fix the service settings instead:

```text
Service Type: Web Service
Runtime: Python 3
Root Directory: leave empty
Build Command: pip install -r requirements.txt
Start Command: python scripts/init_db.py && python scripts/seed.py && gunicorn run:app
Health Check Path: /health
```

If the service was created as Static Site, delete it and create a new Web
Service. If it was created as Web Service but runtime is Node, change Runtime to
Python in Settings or recreate the service.

If Render shows this error:

```text
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

Render is building from a folder that does not contain `requirements.txt`, or
the latest project files were not pushed to GitHub yet. In this project,
`requirements.txt` must be in the same folder as `run.py`, `render.yaml`,
`app/`, `bot/`, and `scripts/`.

Fix it with one of these options:

```text
Root Directory: leave empty
```

Use this if `requirements.txt` is at the repository root.

```text
Root Directory: telegramBot
```

Use this only if GitHub contains the project inside a `telegramBot/` subfolder.

Also make sure the file is committed and pushed:

```powershell
git add requirements.txt run.py app bot scripts docs render.yaml README.md Procfile Dockerfile runtime.txt
git commit -m "Prepare CourseHub Render deploy"
git push
```

Worker service:

```text
Build Command: pip install -r requirements.txt
Start Command: python -m bot.main
```

The Render blueprint runs database initialization and seed data before starting
the web service. If you deploy manually, run this once after the database is
attached:

```powershell
python scripts/init_db.py
python scripts/seed.py
```

The full seeded account list is in `docs/demo_data.md`. It includes one admin,
5 instructors, 15 students, 8 courses, lessons, enrollments, and progress.

Do not run more than one bot worker with polling for the same bot token.

## Docker / VPS Setup

Build and run web, bot, and PostgreSQL:

```powershell
docker compose up --build
```

For a real VPS, put a reverse proxy such as Caddy, Nginx, or a Cloudflare Tunnel
in front of the web service and set the resulting HTTPS URL in
`PUBLIC_BASE_URL` or `TELEGRAM_WEB_APP_URL`.

After the first deploy:

```powershell
docker compose exec web python scripts/init_db.py
docker compose exec web python scripts/seed.py
```
