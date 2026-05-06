import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


class TelegramAuthError(ValueError):
    pass


def validate_web_app_init_data(init_data, bot_token, max_age_seconds=86400, now=None):
    if not bot_token:
        raise TelegramAuthError("Telegram bot token is not configured.")
    if not init_data:
        raise TelegramAuthError("Telegram init data is missing.")

    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("Telegram init data hash is missing.")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramAuthError("Telegram init data signature is invalid.")

    if max_age_seconds is not None:
        auth_date = _parse_auth_date(values.get("auth_date"))
        current_time = int(time.time() if now is None else now)
        if auth_date > current_time + 60:
            raise TelegramAuthError("Telegram init data auth date is in the future.")
        if current_time - auth_date > max_age_seconds:
            raise TelegramAuthError("Telegram init data has expired.")

    if "user" in values:
        try:
            values["user"] = json.loads(values["user"])
        except json.JSONDecodeError as exc:
            raise TelegramAuthError("Telegram user data is invalid.") from exc

    return values


def _parse_auth_date(raw_value):
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise TelegramAuthError("Telegram init data auth date is invalid.") from exc
