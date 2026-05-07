import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


DEFAULT_RENDER_PUBLIC_BASE_URL = "https://courcehub.onrender.com"
DEFAULT_TELEGRAM_WEB_APP_URL = f"{DEFAULT_RENDER_PUBLIC_BASE_URL}/telegram/"
DEFAULT_TELEGRAM_BOT_TOKEN = "8740701480:AAHV9akw5_rj0wxs8jVHRXVGo18Sa3XEJEM"


def _env_value(key):
    return os.getenv(key, "").strip()


def _render_default(value):
    return value if os.getenv("RENDER") else ""


def _telegram_bot_token():
    return _env_value("TELEGRAM_BOT_TOKEN") or _render_default(DEFAULT_TELEGRAM_BOT_TOKEN)


def _public_base_url():
    return (
        _env_value("PUBLIC_BASE_URL")
        or _env_value("RENDER_EXTERNAL_URL")
        or _render_default(DEFAULT_RENDER_PUBLIC_BASE_URL)
    ).rstrip("/")


def _telegram_web_app_url():
    return _env_value("TELEGRAM_WEB_APP_URL") or _render_default(DEFAULT_TELEGRAM_WEB_APP_URL)


def _database_url():
    url = _env_value("DATABASE_URL")
    if not url:
        if os.getenv("RENDER"):
            return "sqlite:////tmp/coursehub.sqlite"
        local_db = Path(__file__).resolve().parent / "instance" / "coursehub.sqlite"
        local_db.parent.mkdir(exist_ok=True)
        return f"sqlite:///{local_db.as_posix()}"

    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TELEGRAM_BOT_TOKEN = _telegram_bot_token()
    PUBLIC_BASE_URL = _public_base_url()
    TELEGRAM_WEB_APP_URL = _telegram_web_app_url()
