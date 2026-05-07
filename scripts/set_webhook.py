import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from bot.main import BOT_COMMANDS, _configured_web_app_url


ALLOWED_UPDATES = ["message", "callback_query"]


def telegram_api(token, method, payload):
    request_body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=request_body,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Telegram API {method} failed: {body}") from exc
    except URLError as exc:
        raise SystemExit(f"Telegram API {method} request failed: {exc}") from exc

    if not result.get("ok"):
        raise SystemExit(f"Telegram API {method} returned: {result}")
    return result


def main():
    app = create_app()
    token = app.config.get("TELEGRAM_BOT_TOKEN")
    webhook_url = app.config.get("TELEGRAM_WEBHOOK_URL")
    web_app_url = app.config.get("TELEGRAM_WEB_APP_URL") or _configured_web_app_url()

    if not token or not webhook_url:
        print("Telegram webhook is not configured; skipping.")
        return

    telegram_api(
        token,
        "setWebhook",
        {
            "url": webhook_url,
            "allowed_updates": ALLOWED_UPDATES,
            "drop_pending_updates": False,
        },
    )
    telegram_api(
        token,
        "setMyCommands",
        {
            "commands": [
                {"command": command.command, "description": command.description}
                for command in BOT_COMMANDS
            ]
        },
    )

    if web_app_url.lower().startswith("https://"):
        telegram_api(
            token,
            "setChatMenuButton",
            {
                "menu_button": {
                    "type": "web_app",
                    "text": "CourseHub",
                    "web_app": {"url": web_app_url},
                }
            },
        )

    print(f"Telegram webhook configured: {webhook_url}")


if __name__ == "__main__":
    main()
