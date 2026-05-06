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
Start Command: gunicorn run:app
Health Check Path: /health
```

Worker service:

```text
Build Command: pip install -r requirements.txt
Start Command: python -m bot.main
```

Run this once after the database is attached:

```powershell
python scripts/init_db.py
python scripts/seed.py
```

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
