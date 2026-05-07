import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app import create_app
from app.extensions import db
from app.models import User
from app.routes import telegram_webapp
from app.telegram_auth import TelegramAuthError, validate_web_app_init_data


BOT_TOKEN = "123456:test-token"


@pytest.fixture()
def app():
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "TELEGRAM_BOT_TOKEN": BOT_TOKEN,
            "TELEGRAM_WEBHOOK_SECRET": "test-webhook-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


def test_validate_web_app_init_data_accepts_signed_payload():
    init_data = _signed_init_data(
        BOT_TOKEN,
        {
            "auth_date": str(int(time.time())),
            "query_id": "query-1",
            "user": json.dumps({"id": 42, "first_name": "Ada"}, separators=(",", ":")),
        },
    )

    data = validate_web_app_init_data(init_data, BOT_TOKEN)

    assert data["user"]["id"] == 42
    assert data["user"]["first_name"] == "Ada"


def test_validate_web_app_init_data_rejects_bad_signature():
    init_data = _signed_init_data(
        BOT_TOKEN,
        {
            "auth_date": str(int(time.time())),
            "user": json.dumps({"id": 42}, separators=(",", ":")),
        },
    )

    with pytest.raises(TelegramAuthError):
        validate_web_app_init_data(f"{init_data}x", BOT_TOKEN)


def test_telegram_auth_creates_student_session(app):
    client = app.test_client()
    init_data = _signed_init_data(
        BOT_TOKEN,
        {
            "auth_date": str(int(time.time())),
            "user": json.dumps(
                {"id": 77, "first_name": "Grace", "last_name": "Hopper"},
                separators=(",", ":"),
            ),
        },
    )

    response = client.post("/telegram/auth", json={"initData": init_data})

    assert response.status_code == 200
    assert response.get_json()["redirectUrl"] == "/telegram/app"

    with client.session_transaction() as session:
        user_id = session["user_id"]
        assert session["telegram_user_id"] == "77"

    user = db.session.get(User, user_id)
    assert user.email == "telegram-77@coursehub.local"
    assert user.name == "Grace Hopper"
    assert user.role == "student"


def test_telegram_webhook_handles_start_command(app, monkeypatch):
    sent_requests = []
    monkeypatch.setattr(
        telegram_webapp,
        "_telegram_api",
        lambda method, payload, **_kwargs: sent_requests.append((method, payload)),
    )

    response = app.test_client().post(
        "/telegram/webhook/test-webhook-secret",
        json={
            "message": {
                "chat": {"id": 100},
                "from": {"id": 42, "first_name": "Ada"},
                "text": "/start",
            }
        },
    )

    assert response.status_code == 200
    assert [method for method, _payload in sent_requests] == ["sendMessage", "sendMessage"]
    assert sent_requests[0][1]["chat_id"] == 100
    assert sent_requests[0][1]["reply_markup"]["keyboard"][0][0]["text"] == "/register"


def test_telegram_webhook_handles_inline_callback(app, monkeypatch):
    sent_requests = []
    monkeypatch.setattr(
        telegram_webapp,
        "_telegram_api",
        lambda method, payload, **_kwargs: sent_requests.append((method, payload)),
    )

    response = app.test_client().post(
        "/telegram/webhook/test-webhook-secret",
        json={
            "callback_query": {
                "id": "callback-1",
                "from": {"id": 42, "first_name": "Ada"},
                "data": "menu:help",
                "message": {"message_id": 7, "chat": {"id": 100}},
            }
        },
    )

    assert response.status_code == 200
    assert [method for method, _payload in sent_requests] == ["answerCallbackQuery", "editMessageText"]
    assert sent_requests[1][1]["chat_id"] == 100
    assert sent_requests[1][1]["message_id"] == 7
    assert "CourseHub commands" in sent_requests[1][1]["text"]


def test_telegram_webhook_rejects_bad_secret(app):
    response = app.test_client().post("/telegram/webhook/wrong-secret", json={})

    assert response.status_code == 404


def _signed_init_data(bot_token, values):
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    signed_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return urlencode({**values, "hash": signed_hash})
