import secrets

from .extensions import db
from .models import User


def find_student_by_telegram_id(telegram_user_id):
    return User.query.filter_by(email=telegram_email(telegram_user_id), role="student").first()


def find_or_create_student(telegram_user):
    email = telegram_email(telegram_user["id"])
    name = telegram_name(telegram_user)
    user = User.query.filter_by(email=email).first()
    created = user is None

    if user is None:
        user = User(name=name, email=email, role="student")
        user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)
    elif user.name != name:
        user.name = name

    db.session.commit()
    return user, created


def telegram_email(telegram_user_id):
    return f"telegram-{telegram_user_id}@coursehub.local"


def telegram_name(telegram_user):
    parts = [
        telegram_user.get("first_name", "").strip(),
        telegram_user.get("last_name", "").strip(),
    ]
    name = " ".join(part for part in parts if part)
    return name or telegram_user.get("username") or f"Telegram User {telegram_user['id']}"
