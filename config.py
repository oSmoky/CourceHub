import os

from dotenv import load_dotenv


load_dotenv()


def _database_url():
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/coursehub",
    )
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
    TELEGRAM_WEB_APP_URL = os.getenv("TELEGRAM_WEB_APP_URL", "")
