import logging
import os
from datetime import date
from urllib.parse import urljoin

from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.error import BadRequest
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from config import DEFAULT_TELEGRAM_BOT_TOKEN, DEFAULT_TELEGRAM_WEB_APP_URL
from app import create_app
from app.extensions import db
from app.models import Course, Enrollment, Progress
from app.telegram_accounts import find_or_create_student, find_student_by_telegram_id


load_dotenv()
flask_app = create_app()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


BOT_COMMANDS = (
    BotCommand("start", "Show the main menu"),
    BotCommand("help", "Show all commands"),
    BotCommand("register", "Create your student profile"),
    BotCommand("profile", "Show your CourseHub profile"),
    BotCommand("courses", "Browse available courses"),
    BotCommand("course", "Show course details by id"),
    BotCommand("enroll", "Enroll in a course by id"),
    BotCommand("mycourses", "Show your enrolled courses"),
    BotCommand("progress", "Show lessons for an enrollment"),
    BotCommand("complete", "Mark a lesson as completed"),
    BotCommand("webview", "Open CourseHub WebView"),
)


def _course_rows(limit=10):
    with flask_app.app_context():
        courses = Course.query.order_by(Course.created_at.desc()).limit(limit).all()
        return [
            {
                "id": course.course_id,
                "title": course.title,
                "level": course.level,
                "lesson_count": len(course.lessons),
                "instructor": course.instructor.name,
            }
            for course in courses
        ]


def _course_detail(course_id):
    with flask_app.app_context():
        course = db.session.get(Course, course_id)
        if course is None:
            return None

        lessons = [
            f"{lesson.display_order}. {lesson.title} ({lesson.duration_min} min)"
            for lesson in course.lessons
        ]
        return {
            "id": course.course_id,
            "title": course.title,
            "description": course.description,
            "level": course.level,
            "instructor": course.instructor.name,
            "lessons": lessons,
        }


def _telegram_user_payload(telegram_user):
    if telegram_user is None:
        return None

    return {
        "id": telegram_user.id,
        "first_name": telegram_user.first_name or "",
        "last_name": telegram_user.last_name or "",
        "username": telegram_user.username or "",
    }


def _register_student(telegram_user):
    with flask_app.app_context():
        user, created = find_or_create_student(telegram_user)
        return {
            "id": user.user_id,
            "name": user.name,
            "created": created,
            "enrollment_count": len(user.enrollments),
        }


def _student_profile(telegram_user_id):
    with flask_app.app_context():
        user = find_student_by_telegram_id(telegram_user_id)
        if user is None:
            return None

        return {
            "id": user.user_id,
            "name": user.name,
            "enrollment_count": len(user.enrollments),
        }


def _enroll_student(telegram_user_id, course_id):
    with flask_app.app_context():
        user = find_student_by_telegram_id(telegram_user_id)
        if user is None:
            return {"status": "not_registered"}

        course = db.session.get(Course, course_id)
        if course is None:
            return {"status": "course_not_found"}

        enrollment = Enrollment.query.filter_by(
            user_id=user.user_id,
            course_id=course.course_id,
        ).first()

        if enrollment is None:
            enrollment = Enrollment(user_id=user.user_id, course_id=course.course_id)
            db.session.add(enrollment)
            db.session.flush()

            for lesson in course.lessons:
                enrollment.progress_records.append(Progress(lesson=lesson))

            db.session.commit()
            status = "created"
        else:
            _sync_progress_records(enrollment)
            _refresh_enrollment_status(enrollment)
            db.session.commit()
            status = "existing"

        return {
            "status": status,
            "enrollment_id": enrollment.enrollment_id,
            "course_title": course.title,
            "progress_percent": enrollment.progress_percent,
        }


def _student_enrollment_rows(telegram_user_id):
    with flask_app.app_context():
        user = find_student_by_telegram_id(telegram_user_id)
        if user is None:
            return None

        enrollments = (
            Enrollment.query.filter_by(user_id=user.user_id)
            .order_by(Enrollment.enrollment_date.desc())
            .all()
        )
        for enrollment in enrollments:
            _sync_progress_records(enrollment)
            _refresh_enrollment_status(enrollment)

        db.session.commit()
        return [
            {
                "id": enrollment.enrollment_id,
                "course_id": enrollment.course_id,
                "title": enrollment.course.title,
                "status": enrollment.status,
                "progress_percent": enrollment.progress_percent,
            }
            for enrollment in enrollments
        ]


def _enrollment_progress_rows(telegram_user_id, enrollment_id):
    with flask_app.app_context():
        user = find_student_by_telegram_id(telegram_user_id)
        if user is None:
            return {"status": "not_registered"}

        enrollment = Enrollment.query.filter_by(
            enrollment_id=enrollment_id,
            user_id=user.user_id,
        ).first()
        if enrollment is None:
            return {"status": "not_found"}

        _sync_progress_records(enrollment)
        _refresh_enrollment_status(enrollment)
        db.session.commit()

        progress_by_lesson = {row.lesson_id: row for row in enrollment.progress_records}
        return {
            "status": "ok",
            "course_title": enrollment.course.title,
            "progress_percent": enrollment.progress_percent,
            "lessons": [
                {
                    "order": lesson.display_order,
                    "title": lesson.title,
                    "is_completed": progress_by_lesson[lesson.lesson_id].is_completed,
                }
                for lesson in enrollment.course.lessons
            ],
        }


def _complete_lesson(telegram_user_id, enrollment_id, lesson_order):
    with flask_app.app_context():
        user = find_student_by_telegram_id(telegram_user_id)
        if user is None:
            return {"status": "not_registered"}

        enrollment = Enrollment.query.filter_by(
            enrollment_id=enrollment_id,
            user_id=user.user_id,
        ).first()
        if enrollment is None:
            return {"status": "enrollment_not_found"}

        lesson = next(
            (row for row in enrollment.course.lessons if row.display_order == lesson_order),
            None,
        )
        if lesson is None:
            return {"status": "lesson_not_found"}

        _sync_progress_records(enrollment)
        progress = next(
            row for row in enrollment.progress_records if row.lesson_id == lesson.lesson_id
        )
        already_completed = progress.is_completed
        progress.is_completed = True
        progress.completion_date = progress.completion_date or date.today()
        _refresh_enrollment_status(enrollment)
        db.session.commit()

        return {
            "status": "already_completed" if already_completed else "completed",
            "course_title": enrollment.course.title,
            "lesson_title": lesson.title,
            "progress_percent": enrollment.progress_percent,
        }


def _sync_progress_records(enrollment):
    existing_lesson_ids = {row.lesson_id for row in enrollment.progress_records}
    for lesson in enrollment.course.lessons:
        if lesson.lesson_id not in existing_lesson_ids:
            enrollment.progress_records.append(Progress(lesson=lesson))


def _refresh_enrollment_status(enrollment):
    if enrollment.progress_records and all(row.is_completed for row in enrollment.progress_records):
        enrollment.status = "completed"
    else:
        enrollment.status = "active"


def _configured_web_app_url():
    explicit_url = os.getenv("TELEGRAM_WEB_APP_URL", "").strip()
    if explicit_url:
        return explicit_url

    public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip() or os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if public_base_url:
        if "://" not in public_base_url:
            public_base_url = f"https://{public_base_url}"
        return urljoin(public_base_url.rstrip("/") + "/", "telegram/")

    if os.getenv("RENDER"):
        return DEFAULT_TELEGRAM_WEB_APP_URL

    return ""


def _web_app_keyboard():
    web_app_url = _configured_web_app_url()
    if not web_app_url.lower().startswith("https://"):
        return None

    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Open CourseHub", web_app=WebAppInfo(url=web_app_url))]]
    )


def _command_reply_keyboard():
    rows = [
        ["/register", "/profile"],
        ["/courses", "/mycourses"],
        ["/help", "/webview"],
    ]
    web_app_url = _configured_web_app_url()
    if web_app_url.lower().startswith("https://"):
        rows.append([KeyboardButton("Open CourseHub", web_app=WebAppInfo(url=web_app_url))])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)


def _web_app_button():
    web_app_url = _configured_web_app_url()
    if not web_app_url.lower().startswith("https://"):
        return None
    return InlineKeyboardButton("Open CourseHub", web_app=WebAppInfo(url=web_app_url))


def _inline_keyboard(rows, include_web_app=True):
    keyboard = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in row]
        for row in rows
    ]
    web_app_button = _web_app_button() if include_web_app else None
    if web_app_button:
        keyboard.append([web_app_button])
    return InlineKeyboardMarkup(keyboard) if keyboard else None


def _main_menu_keyboard():
    return _inline_keyboard(
        [
            [("Register", "menu:register"), ("Profile", "menu:profile")],
            [("Courses", "menu:courses"), ("My Courses", "menu:mycourses")],
            [("Help", "menu:help")],
        ]
    )


def _course_list_keyboard(rows):
    keyboard_rows = [[(row["title"][:40], f"course:{row['id']}")] for row in rows]
    keyboard_rows.append([("Main Menu", "menu:start")])
    return _inline_keyboard(keyboard_rows)


def _course_detail_keyboard(course_id):
    return _inline_keyboard(
        [
            [("Enroll", f"enroll:{course_id}"), ("All Courses", "menu:courses")],
            [("Main Menu", "menu:start")],
        ]
    )


def _enrollment_keyboard(enrollment_id):
    return _inline_keyboard(
        [
            [("Progress", f"progress:{enrollment_id}"), ("My Courses", "menu:mycourses")],
            [("Main Menu", "menu:start")],
        ]
    )


def _mycourses_keyboard(rows):
    keyboard_rows = [[(f"Progress: {row['title'][:28]}", f"progress:{row['id']}")] for row in rows]
    keyboard_rows.append([("Browse Courses", "menu:courses"), ("Main Menu", "menu:start")])
    return _inline_keyboard(keyboard_rows)


def _progress_keyboard(enrollment_id, lessons):
    keyboard_rows = [
        [(f"Complete lesson {lesson['order']}", f"complete:{enrollment_id}:{lesson['order']}")]
        for lesson in lessons
        if not lesson["is_completed"]
    ]
    keyboard_rows.append([("My Courses", "menu:mycourses"), ("Main Menu", "menu:start")])
    return _inline_keyboard(keyboard_rows)


def _web_app_setup_hint():
    web_app_url = _configured_web_app_url()
    if not web_app_url:
        return "WebView is not configured. Set TELEGRAM_WEB_APP_URL to your public HTTPS /telegram/ URL."
    if not web_app_url.lower().startswith("https://"):
        return "Telegram WebView requires HTTPS. Update TELEGRAM_WEB_APP_URL to an HTTPS URL."
    return ""


def _start_message(telegram_user_id=None):
    profile = None
    if telegram_user_id:
        try:
            profile = _student_profile(telegram_user_id)
        except SQLAlchemyError:
            profile = None

    greeting = f"Welcome back, {profile['name']}." if profile else "Welcome to CourseHub."
    text = (
        f"{greeting}\n\n"
        "Choose an action below or use commands:\n"
        "/register - create your student profile\n"
        "/courses - browse courses\n"
        "/mycourses - view your learning\n"
        "/webview - open the full app"
    )
    setup_hint = _web_app_setup_hint()
    if setup_hint:
        text = f"{text}\n\n{setup_hint}"
    return text, _main_menu_keyboard()


def _help_message():
    return (
        "CourseHub commands:\n\n"
        "/register - create or update your student profile\n"
        "/profile - show your account status\n"
        "/courses - list available courses\n"
        "/course <id> - show one course\n"
        "/enroll <id> - enroll in a course\n"
        "/mycourses - show enrolled courses\n"
        "/progress <enrollment_id> - show lessons and progress\n"
        "/complete <enrollment_id> <lesson_no> - mark a lesson completed\n"
        "/webview - open the full app in Telegram"
    ), _main_menu_keyboard()


def _courses_message():
    rows = _course_rows()
    if not rows:
        return "No courses are available yet.", _main_menu_keyboard()

    lines = [
        f"{row['id']}. {row['title']} - {row['level']} - {row['lesson_count']} lessons - {row['instructor']}"
        for row in rows
    ]
    return (
        "Available courses:\n\n"
        + "\n".join(lines)
        + "\n\nTap a course below or use /course <id>.",
        _course_list_keyboard(rows),
    )


def _course_detail_message(course_id):
    detail = _course_detail(course_id)
    if detail is None:
        return "Course not found.", _course_list_keyboard([])

    lesson_text = "\n".join(detail["lessons"]) if detail["lessons"] else "No lessons yet."
    text = (
        f"{detail['title']}\n"
        f"Course ID: {detail['id']}\n"
        f"Level: {detail['level']}\n"
        f"Instructor: {detail['instructor']}\n\n"
        f"{detail['description']}\n\n"
        f"Lessons:\n{lesson_text}"
    )
    return text, _course_detail_keyboard(detail["id"])


def _profile_message(telegram_user_id):
    profile_data = _student_profile(telegram_user_id)
    if profile_data is None:
        return "You are not registered yet. Tap Register below.", _inline_keyboard(
            [[("Register", "menu:register"), ("Main Menu", "menu:start")]]
        )

    return (
        "CourseHub profile\n\n"
        f"Name: {profile_data['name']}\n"
        f"Enrolled courses: {profile_data['enrollment_count']}",
        _main_menu_keyboard(),
    )


def _registration_message(telegram_user):
    profile = _register_student(telegram_user)
    status = "Registration created" if profile["created"] else "Profile updated"
    return (
        f"{status}.\n\n"
        f"Name: {profile['name']}\n"
        f"Enrolled courses: {profile['enrollment_count']}\n\n"
        "Browse courses or open the full app.",
        _inline_keyboard(
            [
                [("Browse Courses", "menu:courses"), ("My Courses", "menu:mycourses")],
                [("Main Menu", "menu:start")],
            ]
        ),
    )


def _enroll_message(telegram_user_id, course_id):
    result = _enroll_student(telegram_user_id, course_id)
    if result["status"] == "not_registered":
        return "Use Register before enrolling in a course.", _inline_keyboard(
            [[("Register", "menu:register"), ("All Courses", "menu:courses")]]
        )
    if result["status"] == "course_not_found":
        return "Course not found.", _course_list_keyboard([])

    prefix = "Enrollment created" if result["status"] == "created" else "You are already enrolled"
    return (
        f"{prefix}: {result['course_title']}\n"
        f"Enrollment ID: {result['enrollment_id']}\n"
        f"Progress: {result['progress_percent']}%",
        _enrollment_keyboard(result["enrollment_id"]),
    )


def _mycourses_message(telegram_user_id):
    rows = _student_enrollment_rows(telegram_user_id)
    if rows is None:
        return "You are not registered yet. Tap Register below.", _inline_keyboard(
            [[("Register", "menu:register"), ("Browse Courses", "menu:courses")]]
        )
    if not rows:
        return "You are registered, but not enrolled yet. Browse courses to start.", _inline_keyboard(
            [[("Browse Courses", "menu:courses"), ("Main Menu", "menu:start")]]
        )

    lines = [
        f"{row['id']}. {row['title']} - {row['progress_percent']}% - {row['status']}"
        for row in rows
    ]
    return (
        "My courses:\n\n" + "\n".join(lines) + "\n\nTap a course to see progress.",
        _mycourses_keyboard(rows),
    )


def _progress_message(telegram_user_id, enrollment_id):
    result = _enrollment_progress_rows(telegram_user_id, enrollment_id)
    if result["status"] == "not_registered":
        return "You are not registered yet. Tap Register below.", _inline_keyboard(
            [[("Register", "menu:register"), ("Main Menu", "menu:start")]]
        )
    if result["status"] == "not_found":
        return "Enrollment not found.", _mycourses_keyboard([])

    lesson_lines = [
        f"{lesson['order']}. {'Done' if lesson['is_completed'] else 'Open'} - {lesson['title']}"
        for lesson in result["lessons"]
    ]
    lesson_text = "\n".join(lesson_lines) if lesson_lines else "No lessons yet."
    return (
        f"{result['course_title']}\n"
        f"Progress: {result['progress_percent']}%\n\n"
        f"{lesson_text}",
        _progress_keyboard(enrollment_id, result["lessons"]),
    )


def _complete_message(telegram_user_id, enrollment_id, lesson_order):
    result = _complete_lesson(telegram_user_id, enrollment_id, lesson_order)
    if result["status"] == "not_registered":
        return "You are not registered yet. Tap Register below.", _inline_keyboard(
            [[("Register", "menu:register"), ("Main Menu", "menu:start")]]
        )
    if result["status"] == "enrollment_not_found":
        return "Enrollment not found.", _mycourses_keyboard([])
    if result["status"] == "lesson_not_found":
        return "Lesson not found in this enrollment.", _enrollment_keyboard(enrollment_id)

    prefix = "Already completed" if result["status"] == "already_completed" else "Marked completed"
    return (
        f"{prefix}: {result['lesson_title']}\n"
        f"Course: {result['course_title']}\n"
        f"Progress: {result['progress_percent']}%",
        _enrollment_keyboard(enrollment_id),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else None
    text, keyboard = _start_message(user_id)
    await update.message.reply_text(
        "Command keyboard is ready below the message box.",
        reply_markup=_command_reply_keyboard(),
    )
    await update.message.reply_text(text, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, keyboard = _help_message()
    await update.message.reply_text(
        "Use the keyboard below for common actions.",
        reply_markup=_command_reply_keyboard(),
    )
    await update.message.reply_text(text, reply_markup=keyboard)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = _telegram_user_payload(update.effective_user)
    if telegram_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return

    try:
        text, keyboard = _registration_message(telegram_user)
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return

    try:
        text, keyboard = _profile_message(update.effective_user.id)
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def webview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    setup_hint = _web_app_setup_hint()
    if setup_hint:
        await update.message.reply_text(setup_hint)
        return

    await update.message.reply_text(
        "Open CourseHub in Telegram.",
        reply_markup=_web_app_keyboard(),
    )


async def courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text, keyboard = _courses_message()
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def course_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /course <id>")
        return

    try:
        text, keyboard = _course_detail_message(int(context.args[0]))
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def enroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /enroll <course_id>")
        return

    try:
        text, keyboard = _enroll_message(update.effective_user.id, int(context.args[0]))
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def mycourses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return

    try:
        text, keyboard = _mycourses_message(update.effective_user.id)
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /progress <enrollment_id>")
        return

    try:
        text, keyboard = _progress_message(update.effective_user.id, int(context.args[0]))
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Telegram user data is missing.")
        return
    if len(context.args) < 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        await update.message.reply_text("Usage: /complete <enrollment_id> <lesson_no>")
        return

    try:
        text, keyboard = _complete_message(
            update.effective_user.id,
            int(context.args[0]),
            int(context.args[1]),
        )
    except SQLAlchemyError:
        await update.message.reply_text("Database is not ready. Please initialize CourseHub first.")
        return

    await update.message.reply_text(text, reply_markup=keyboard)


async def inline_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    user = _telegram_user_payload(update.effective_user)
    user_id = update.effective_user.id if update.effective_user else None

    try:
        if data == "menu:start":
            text, keyboard = _start_message(user_id)
        elif data == "menu:help":
            text, keyboard = _help_message()
        elif data == "menu:register":
            if user is None:
                text, keyboard = "Telegram user data is missing.", _main_menu_keyboard()
            else:
                text, keyboard = _registration_message(user)
        elif data == "menu:profile":
            text, keyboard = _profile_message(user_id)
        elif data == "menu:courses":
            text, keyboard = _courses_message()
        elif data == "menu:mycourses":
            text, keyboard = _mycourses_message(user_id)
        elif data.startswith("course:"):
            text, keyboard = _course_detail_message(int(data.split(":", 1)[1]))
        elif data.startswith("enroll:"):
            text, keyboard = _enroll_message(user_id, int(data.split(":", 1)[1]))
        elif data.startswith("progress:"):
            text, keyboard = _progress_message(user_id, int(data.split(":", 1)[1]))
        elif data.startswith("complete:"):
            _prefix, enrollment_id, lesson_order = data.split(":", 2)
            text, keyboard = _complete_message(user_id, int(enrollment_id), int(lesson_order))
        else:
            text, keyboard = "Unknown action. Choose from the menu.", _main_menu_keyboard()
    except (SQLAlchemyError, ValueError):
        text, keyboard = "Database is not ready. Please try again in a moment.", _main_menu_keyboard()

    await _edit_callback_message(query, text, keyboard)


async def _edit_callback_message(query, text, keyboard):
    try:
        await query.edit_message_text(text, reply_markup=keyboard)
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            raise


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("CourseHub received your Web App data.")


async def configure_bot(application):
    await application.bot.set_my_commands(BOT_COMMANDS)

    web_app_url = _configured_web_app_url()
    if web_app_url.lower().startswith("https://"):
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="CourseHub",
                web_app=WebAppInfo(url=web_app_url),
            )
        )


def build_application(token):
    application = ApplicationBuilder().token(token).post_init(configure_bot).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("webview", webview))
    application.add_handler(CommandHandler("courses", courses))
    application.add_handler(CommandHandler("course", course_detail))
    application.add_handler(CommandHandler("enroll", enroll))
    application.add_handler(CommandHandler("mycourses", mycourses))
    application.add_handler(CommandHandler("progress", progress))
    application.add_handler(CommandHandler("complete", complete))
    application.add_handler(CallbackQueryHandler(inline_button))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    return application


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN") or (
        DEFAULT_TELEGRAM_BOT_TOKEN if os.getenv("RENDER") else ""
    )
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env or environment variables.")

    application = build_application(token)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
