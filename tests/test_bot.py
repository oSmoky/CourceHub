import asyncio
from unittest.mock import AsyncMock, Mock

from sqlalchemy.exc import SQLAlchemyError
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from bot import main as bot_main


def test_configured_web_app_url_prefers_explicit_url(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://base.example")
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")

    assert bot_main._configured_web_app_url() == "https://app.example/telegram/"


def test_configured_web_app_url_uses_public_base_url(monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEB_APP_URL", raising=False)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://base.example/root")

    assert bot_main._configured_web_app_url() == "https://base.example/root/telegram/"


def test_configured_web_app_url_adds_https_to_host(monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEB_APP_URL", raising=False)
    monkeypatch.setenv("PUBLIC_BASE_URL", "coursehub-web.onrender.com")

    assert bot_main._configured_web_app_url() == "https://coursehub-web.onrender.com/telegram/"


def test_web_app_keyboard_requires_https(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "http://localhost:5000/telegram/")

    assert bot_main._web_app_keyboard() is None

    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")
    keyboard = bot_main._web_app_keyboard()

    assert keyboard.inline_keyboard[0][0].text == "Open CourseHub"
    assert keyboard.inline_keyboard[0][0].web_app.url == "https://app.example/telegram/"


def test_command_reply_keyboard_has_common_actions(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")

    keyboard = bot_main._command_reply_keyboard()

    assert keyboard.keyboard[0][0].text == "/register"
    assert keyboard.keyboard[1][0].text == "/courses"
    assert keyboard.keyboard[2][1].text == "/webview"
    assert keyboard.keyboard[3][0].text == "Open CourseHub"
    assert keyboard.keyboard[3][0].web_app.url == "https://app.example/telegram/"


def test_build_application_registers_bot_handlers(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")

    application = bot_main.build_application("123456:test-token")
    handlers = application.handlers[0]
    commands = [
        next(iter(handler.commands))
        for handler in handlers
        if isinstance(handler, CommandHandler)
    ]

    assert commands == [
        "start",
        "help",
        "register",
        "profile",
        "webview",
        "courses",
        "course",
        "enroll",
        "mycourses",
        "progress",
        "complete",
    ]
    assert any(isinstance(handler, CallbackQueryHandler) for handler in handlers)
    assert any(isinstance(handler, MessageHandler) for handler in handlers)


def test_bot_command_menu_order():
    assert [command.command for command in bot_main.BOT_COMMANDS] == [
        "start",
        "help",
        "register",
        "profile",
        "courses",
        "course",
        "enroll",
        "mycourses",
        "progress",
        "complete",
        "webview",
    ]


def test_start_mentions_webview_when_not_configured(monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEB_APP_URL", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    update = _update()

    asyncio.run(bot_main.start(update, Mock()))

    text = update.message.reply_text.await_args.kwargs.get("text") or update.message.reply_text.await_args.args[0]
    assert "/webview" in text
    assert "WebView is not configured" in text
    keyboard = update.message.reply_text.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].callback_data == "menu:register"


def test_webview_sends_keyboard_for_https_url(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")
    update = _update()

    asyncio.run(bot_main.webview(update, Mock()))

    assert update.message.reply_text.await_args.args[0] == "Open CourseHub in Telegram."
    assert update.message.reply_text.await_args.kwargs["reply_markup"].inline_keyboard[0][0].web_app.url == (
        "https://app.example/telegram/"
    )


def test_courses_lists_course_rows(monkeypatch):
    monkeypatch.setattr(
        bot_main,
        "_course_rows",
        lambda: [
            {
                "id": 3,
                "title": "Python Fundamentals",
                "level": "Beginner",
                "lesson_count": 4,
                "instructor": "Demo Instructor",
            }
        ],
    )
    update = _update()

    asyncio.run(bot_main.courses(update, Mock()))

    text = update.message.reply_text.await_args.args[0]
    assert "Available courses" in text
    assert "3. Python Fundamentals - Beginner - 4 lessons - Demo Instructor" in text
    keyboard = update.message.reply_text.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].callback_data == "course:3"


def test_courses_handles_database_error(monkeypatch):
    def raise_database_error():
        raise SQLAlchemyError()

    monkeypatch.setattr(bot_main, "_course_rows", raise_database_error)
    update = _update()

    asyncio.run(bot_main.courses(update, Mock()))

    assert update.message.reply_text.await_args.args[0] == (
        "Database is not ready. Please initialize CourseHub first."
    )


def test_register_creates_student_profile(monkeypatch):
    monkeypatch.setattr(
        bot_main,
        "_register_student",
        lambda user: {
            "id": 1,
            "name": "Ada Lovelace",
            "created": True,
            "enrollment_count": 0,
        },
    )
    update = _update(user_id=42, first_name="Ada", last_name="Lovelace")

    asyncio.run(bot_main.register(update, Mock()))

    text = update.message.reply_text.await_args.args[0]
    assert "Registration created" in text
    assert "Ada Lovelace" in text


def test_enroll_requires_registration(monkeypatch):
    monkeypatch.setattr(bot_main, "_enroll_student", lambda user_id, course_id: {"status": "not_registered"})
    update = _update(user_id=42)
    context = Mock(args=["3"])

    asyncio.run(bot_main.enroll(update, context))

    assert update.message.reply_text.await_args.args[0] == "Use Register before enrolling in a course."


def test_mycourses_lists_enrollments(monkeypatch):
    monkeypatch.setattr(
        bot_main,
        "_student_enrollment_rows",
        lambda user_id: [
            {
                "id": 7,
                "course_id": 3,
                "title": "Python Fundamentals",
                "status": "active",
                "progress_percent": 50,
            }
        ],
    )
    update = _update(user_id=42)

    asyncio.run(bot_main.mycourses(update, Mock()))

    text = update.message.reply_text.await_args.args[0]
    assert "My courses" in text
    assert "7. Python Fundamentals - 50% - active" in text
    keyboard = update.message.reply_text.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].callback_data == "progress:7"


def test_course_detail_includes_enroll_inline_button(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEB_APP_URL", "https://app.example/telegram/")
    monkeypatch.setattr(
        bot_main,
        "_course_detail",
        lambda course_id: {
            "id": course_id,
            "title": "Python Fundamentals",
            "description": "Learn Python.",
            "level": "Beginner",
            "instructor": "Demo Instructor",
            "lessons": ["1. Getting Started (12 min)"],
        },
    )
    update = _update()
    context = Mock(args=["3"])

    asyncio.run(bot_main.course_detail(update, context))

    keyboard = update.message.reply_text.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].callback_data == "enroll:3"


def test_inline_callback_routes_to_courses(monkeypatch):
    monkeypatch.setattr(
        bot_main,
        "_courses_message",
        lambda: ("Available courses", bot_main._inline_keyboard([[("Python", "course:3")]], include_web_app=False)),
    )
    update = _callback_update("menu:courses", user_id=42)

    asyncio.run(bot_main.inline_button(update, Mock()))

    update.callback_query.answer.assert_awaited_once()
    update.callback_query.edit_message_text.assert_awaited_once()
    assert update.callback_query.edit_message_text.await_args.args[0] == "Available courses"
    keyboard = update.callback_query.edit_message_text.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].callback_data == "course:3"


def test_inline_callback_can_complete_lesson(monkeypatch):
    monkeypatch.setattr(
        bot_main,
        "_complete_message",
        lambda user_id, enrollment_id, lesson_order: (
            f"Marked completed: {enrollment_id}/{lesson_order}",
            bot_main._enrollment_keyboard(enrollment_id),
        ),
    )
    update = _callback_update("complete:7:2", user_id=42)

    asyncio.run(bot_main.inline_button(update, Mock()))

    assert update.callback_query.edit_message_text.await_args.args[0] == "Marked completed: 7/2"


def _update(user_id=None, first_name="Student", last_name="", username="student"):
    update = Mock()
    update.effective_user = None
    if user_id is not None:
        update.effective_user = Mock(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
    update.message.reply_text = AsyncMock()
    return update


def _callback_update(data, user_id=None):
    update = _update(user_id=user_id)
    update.callback_query = Mock(data=data)
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update
