import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, abort, current_app, g, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Course, Enrollment, Progress
from app.telegram_auth import TelegramAuthError, validate_web_app_init_data
from app.telegram_accounts import find_or_create_student


bp = Blueprint("telegram_webapp", __name__, url_prefix="/telegram")


@bp.get("/")
def index():
    return render_template("telegram/webapp.html")


@bp.get("")
def index_without_trailing_slash():
    return index()


@bp.get("/app")
def app_home():
    if g.user is None:
        return redirect(url_for("telegram_webapp.index"))

    enrollments = (
        Enrollment.query.filter_by(user_id=g.user.user_id)
        .order_by(Enrollment.enrollment_date.desc())
        .all()
    )
    courses = Course.query.order_by(Course.created_at.desc()).all()
    enrollment_by_course = {enrollment.course_id: enrollment for enrollment in enrollments}
    completed_lessons = sum(
        1
        for enrollment in enrollments
        for progress in enrollment.progress_records
        if progress.is_completed
    )
    total_lessons = sum(len(enrollment.course.lessons) for enrollment in enrollments)

    return render_template(
        "telegram/app.html",
        courses=courses,
        enrollments=enrollments,
        enrollment_by_course=enrollment_by_course,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
    )


@bp.post("/courses/<int:course_id>/enroll")
def enroll_course(course_id):
    if g.user is None:
        return redirect(url_for("telegram_webapp.index"))
    if not g.user.is_student:
        return redirect(url_for("telegram_webapp.app_home"))

    course = Course.query.get_or_404(course_id)
    enrollment = Enrollment.query.filter_by(user_id=g.user.user_id, course_id=course.course_id).first()
    if enrollment is None:
        enrollment = Enrollment(user_id=g.user.user_id, course_id=course.course_id)
        db.session.add(enrollment)
        db.session.flush()

        for lesson in course.lessons:
            enrollment.progress_records.append(Progress(lesson=lesson))

        db.session.commit()

    return redirect(url_for("telegram_webapp.app_home"))


@bp.post("/auth")
def auth():
    init_data = _request_init_data()

    try:
        telegram_data = validate_web_app_init_data(
            init_data,
            current_app.config.get("TELEGRAM_BOT_TOKEN"),
        )
        telegram_user = telegram_data.get("user") or {}
        telegram_user_id = telegram_user.get("id")
        if not telegram_user_id:
            return jsonify({"error": "Telegram user data is missing."}), 400

        user, _created = find_or_create_student(telegram_user)
        session.clear()
        session["user_id"] = user.user_id
        session["telegram_user_id"] = str(telegram_user_id)
    except TelegramAuthError as exc:
        return jsonify({"error": str(exc)}), 401
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database is not ready."}), 503

    return jsonify({"redirectUrl": url_for("telegram_webapp.app_home")})


@bp.post("/webhook/<secret>")
def bot_webhook(secret):
    expected_secret = current_app.config.get("TELEGRAM_WEBHOOK_SECRET", "")
    if not expected_secret or not hmac.compare_digest(secret, expected_secret):
        abort(404)

    update = request.get_json(silent=True) or {}
    bot_main = _bot_main()

    try:
        if "callback_query" in update:
            _handle_callback_query(bot_main, update["callback_query"])
        elif "message" in update:
            _handle_message(bot_main, update["message"])
    except SQLAlchemyError:
        current_app.logger.exception("Telegram webhook database error")
    except (KeyError, TypeError, ValueError):
        current_app.logger.exception("Telegram webhook payload error")

    return jsonify({"ok": True})


def _request_init_data():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return payload.get("initData", "")
    return request.form.get("initData", "")


def _bot_main():
    from bot import main as bot_main

    bot_main.flask_app = current_app._get_current_object()
    return bot_main


def _handle_message(bot_main, message):
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    if message.get("web_app_data"):
        _send_message(chat_id, "CourseHub received your Web App data.")
        return

    command, args = _parse_command(message.get("text", ""))
    if not command:
        return

    user = _telegram_user_from_update(message.get("from"))
    user_id = user["id"] if user else None

    if command == "start":
        text, keyboard = bot_main._start_message(user_id)
        _send_message(chat_id, "Command keyboard is ready below the message box.", bot_main._command_reply_keyboard())
        _send_message(chat_id, text, keyboard)
    elif command == "help":
        text, keyboard = bot_main._help_message()
        _send_message(chat_id, "Use the keyboard below for common actions.", bot_main._command_reply_keyboard())
        _send_message(chat_id, text, keyboard)
    elif command == "register":
        if user is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        text, keyboard = bot_main._registration_message(user)
        _send_message(chat_id, text, keyboard)
    elif command == "profile":
        if user_id is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        text, keyboard = bot_main._profile_message(user_id)
        _send_message(chat_id, text, keyboard)
    elif command == "webview":
        setup_hint = bot_main._web_app_setup_hint()
        if setup_hint:
            _send_message(chat_id, setup_hint)
        else:
            _send_message(chat_id, "Open CourseHub in Telegram.", bot_main._web_app_keyboard())
    elif command == "courses":
        text, keyboard = bot_main._courses_message()
        _send_message(chat_id, text, keyboard)
    elif command == "course":
        if not args or not args[0].isdigit():
            _send_message(chat_id, "Usage: /course <id>")
            return
        text, keyboard = bot_main._course_detail_message(int(args[0]))
        _send_message(chat_id, text, keyboard)
    elif command == "enroll":
        if user_id is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        if not args or not args[0].isdigit():
            _send_message(chat_id, "Usage: /enroll <course_id>")
            return
        text, keyboard = bot_main._enroll_message(user_id, int(args[0]))
        _send_message(chat_id, text, keyboard)
    elif command == "mycourses":
        if user_id is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        text, keyboard = bot_main._mycourses_message(user_id)
        _send_message(chat_id, text, keyboard)
    elif command == "progress":
        if user_id is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        if not args or not args[0].isdigit():
            _send_message(chat_id, "Usage: /progress <enrollment_id>")
            return
        text, keyboard = bot_main._progress_message(user_id, int(args[0]))
        _send_message(chat_id, text, keyboard)
    elif command == "complete":
        if user_id is None:
            _send_message(chat_id, "Telegram user data is missing.")
            return
        if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
            _send_message(chat_id, "Usage: /complete <enrollment_id> <lesson_no>")
            return
        text, keyboard = bot_main._complete_message(user_id, int(args[0]), int(args[1]))
        _send_message(chat_id, text, keyboard)


def _handle_callback_query(bot_main, query):
    _telegram_api("answerCallbackQuery", {"callback_query_id": query.get("id")})

    data = query.get("data") or ""
    user = _telegram_user_from_update(query.get("from"))
    user_id = user["id"] if user else None

    try:
        if data == "menu:start":
            text, keyboard = bot_main._start_message(user_id)
        elif data == "menu:help":
            text, keyboard = bot_main._help_message()
        elif data == "menu:register":
            if user is None:
                text, keyboard = "Telegram user data is missing.", bot_main._main_menu_keyboard()
            else:
                text, keyboard = bot_main._registration_message(user)
        elif data == "menu:profile":
            text, keyboard = bot_main._profile_message(user_id)
        elif data == "menu:courses":
            text, keyboard = bot_main._courses_message()
        elif data == "menu:mycourses":
            text, keyboard = bot_main._mycourses_message(user_id)
        elif data.startswith("course:"):
            text, keyboard = bot_main._course_detail_message(int(data.split(":", 1)[1]))
        elif data.startswith("enroll:"):
            text, keyboard = bot_main._enroll_message(user_id, int(data.split(":", 1)[1]))
        elif data.startswith("progress:"):
            text, keyboard = bot_main._progress_message(user_id, int(data.split(":", 1)[1]))
        elif data.startswith("complete:"):
            _prefix, enrollment_id, lesson_order = data.split(":", 2)
            text, keyboard = bot_main._complete_message(user_id, int(enrollment_id), int(lesson_order))
        else:
            text, keyboard = "Unknown action. Choose from the menu.", bot_main._main_menu_keyboard()
    except (SQLAlchemyError, ValueError):
        text, keyboard = "Database is not ready. Please try again in a moment.", bot_main._main_menu_keyboard()

    message = query.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    if chat_id and message_id:
        _telegram_api(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": _reply_markup_payload(keyboard),
            },
            ignore_message_not_modified=True,
        )


def _parse_command(text):
    if not text or not text.startswith("/"):
        return "", []

    parts = text.strip().split()
    command = parts[0][1:].split("@", 1)[0].lower()
    return command, parts[1:]


def _telegram_user_from_update(user):
    if not user:
        return None

    return {
        "id": user["id"],
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "username": user.get("username", ""),
    }


def _send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    markup_payload = _reply_markup_payload(reply_markup)
    if markup_payload:
        payload["reply_markup"] = markup_payload
    _telegram_api("sendMessage", payload)


def _reply_markup_payload(reply_markup):
    if reply_markup is None:
        return None
    if hasattr(reply_markup, "to_dict"):
        return reply_markup.to_dict()
    return reply_markup


def _telegram_api(method, payload, ignore_message_not_modified=False):
    token = current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        current_app.logger.warning("Telegram bot token is not configured.")
        return None

    request_body = json.dumps(payload).encode("utf-8")
    api_request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=request_body,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(api_request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        if ignore_message_not_modified and "message is not modified" in error_body.lower():
            return None
        current_app.logger.warning("Telegram API error: %s", error_body)
    except URLError as exc:
        current_app.logger.warning("Telegram API request failed: %s", exc)
    return None
