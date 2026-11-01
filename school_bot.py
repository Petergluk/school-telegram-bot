import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
DB_FILE = "school_bot.db"

# Conversation states
ROLE, NAME, CLASS_NAME, SUBJECT, HOMEWORK_TEXT, GRADE_TEXT, SCHEDULE_TEXT = range(7)


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            class_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            student_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            subject TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT telegram_id, role, name, class_name, created_at FROM users WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_user(telegram_id: int, role: str, name: str, class_name: str | None = None):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO users (telegram_id, role, name, class_name, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            role = excluded.role,
            name = excluded.name,
            class_name = excluded.class_name
        """,
        (telegram_id, role, name, class_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_homework_for_class(class_name: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT subject, description FROM homework WHERE class_name = ? ORDER BY id DESC",
        (class_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_homework(class_name: str, subject: str, description: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO homework (class_name, subject, description, created_at) VALUES (?, ?, ?, ?)",
        (class_name, subject, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_grades_for_class(class_name: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT student_name, subject, grade FROM grades WHERE class_name = ? ORDER BY id DESC",
        (class_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_grade(class_name: str, student_name: str, subject: str, grade: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO grades (class_name, student_name, subject, grade, created_at) VALUES (?, ?, ?, ?, ?)",
        (class_name, student_name, subject, grade, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def get_schedule_for_class(class_name: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT day, time, subject FROM schedule WHERE class_name = ? ORDER BY id ASC",
        (class_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_schedule(class_name: str, day: str, time: str, subject: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO schedule (class_name, day, time, subject, created_at) VALUES (?, ?, ?, ?, ?)",
        (class_name, day, time, subject, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()


def main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📅 Расписание", callback_data="schedule"),
            InlineKeyboardButton("📝 Домашка", callback_data="homework"),
        ],
        [
            InlineKeyboardButton("🏆 Оценки", callback_data="grades"),
            InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    current = get_user(user.id)

    if current:
        text = (
            f"Привет, {current['name']}! 👋\n"
            f"Роль: {current['role']}\n"
            f"Класс: {current['class_name'] or '—'}"
        )
    else:
        text = (
            "Добро пожаловать в Telegram-бот онлайн-школы! 🏫\n\n"
            "Для начала зарегистрируйтесь: /register"
        )

    await update.message.reply_text(text, reply_markup=main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Команды бота:\n"
        "/start — главное меню\n"
        "/register — регистрация\n"
        "/schedule — расписание\n"
        "/homework — домашние задания\n"
        "/grades — оценки\n"
        "/profile — профиль\n"
        "/teacher_panel — панель учителя\n"
        "/help — помощь\n"
        "\n"
        "Для учителя доступны функции: добавление домашки, оценок и расписания."
    )
    await update.message.reply_text(text)


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выберите роль:\n"
        "1) Учитель\n"
        "2) Ученик\n\n"
        "Напишите: teacher или student",
    )
    return ROLE


async def register_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    role = update.message.text.strip().lower()
    if role not in {"teacher", "student"}:
        await update.message.reply_text("Неверная роль. Напишите teacher или student.")
        return ROLE

    context.user_data["role"] = role
    await update.message.reply_text("Введите имя:")
    return NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("Имя не может быть пустым. Попробуйте ещё раз.")
        return NAME

    context.user_data["name"] = name
    if context.user_data["role"] == "teacher":
        save_user(update.effective_user.id, "teacher", name)
        await update.message.reply_text(
            f"Регистрация завершена! 👩‍🏫\nИмя: {name}\nРоль: учитель\n\nТеперь можете использовать /teacher_panel",
            reply_markup=main_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text("Введите класс или группу (например: 10А, 10Б, Группа-1):")
    return CLASS_NAME


async def register_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    class_name = update.message.text.strip()
    if not class_name:
        await update.message.reply_text("Класс не может б��ть пустым. Попробуйте ещё раз.")
        return CLASS_NAME

    telegram_id = update.effective_user.id
    name = context.user_data["name"]
    save_user(telegram_id, "student", name, class_name)

    await update.message.reply_text(
        f"Регистрация завершена! ✅\nИмя: {name}\nКласс: {class_name}",
        reply_markup=main_keyboard(),
    )
    return ConversationHandler.END


async def cancel_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    text = (
        "👤 Профиль\n"
        f"Имя: {user['name']}\n"
        f"Роль: {user['role']}\n"
        f"Класс: {user['class_name'] or '—'}"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard())


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    if user["role"] == "teacher":
        text = "Вы учитель. Чтобы посмотреть расписание класса, используйте /teacher_panel."
        await update.message.reply_text(text)
        return

    rows = get_schedule_for_class(user["class_name"])
    if not rows:
        await update.message.reply_text(f"Для класса {user['class_name']} расписание пока пусто.")
        return

    text = f"📅 Расписание класса {user['class_name']}:\n\n"
    for row in rows:
        text += f"{row['day']} — {row['time']} — {row['subject']}\n"

    await update.message.reply_text(text, reply_markup=main_keyboard())


async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    if user["role"] == "teacher":
        text = "Вы учитель. Чтобы добавить домашку, воспользуйтесь /teacher_panel."
        await update.message.reply_text(text)
        return

    rows = get_homework_for_class(user["class_name"])
    if not rows:
        await update.message.reply_text(f"Для класса {user['class_name']} пока нет домашки.")
        return

    text = f"📝 Домашние задания для класса {user['class_name']}:\n\n"
    for idx, row in enumerate(rows, start=1):
        text += f"{idx}. {row['subject']}: {row['description']}\n"

    await update.message.reply_text(text, reply_markup=main_keyboard())


async def grades_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    if user["role"] == "teacher":
        text = "Вы учитель. Чтобы выставлять оценки, используйте /teacher_panel."
        await update.message.reply_text(text)
        return

    rows = get_grades_for_class(user["class_name"])
    if not rows:
        await update.message.reply_text(f"Для класса {user['class_name']} пока нет оценок.")
        return

    text = f"🏆 Оценки класса {user['class_name']}:\n\n"
    for row in rows:
        text += f"{row['student_name']} — {row['subject']}: {row['grade']}\n"

    await update.message.reply_text(text, reply_markup=main_keyboard())


async def teacher_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь: /register")
        return

    if user["role"] != "teacher":
        await update.message.reply_text("Эта панель доступна только учителям.")
        return

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Добавить домашку", callback_data="teacher_add_homework")],
            [InlineKeyboardButton("➕ Добавить оценку", callback_data="teacher_add_grade")],
            [InlineKeyboardButton("➕ Добавить урок", callback_data="teacher_add_schedule")],
        ]
    )
    await update.message.reply_text("Панель учителя 👩‍🏫", reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "schedule":
        user = get_user(query.from_user.id)
        if not user or user["role"] != "student":
            await query.edit_message_text("Сначала зарегистрируйтесь как ученик: /register")
            return
        rows = get_schedule_for_class(user["class_name"])
        if not rows:
            await query.edit_message_text(f"Для класса {user['class_name']} расписание пока пусто.")
            return
        text = f"📅 Расписание класса {user['class_name']}:\n\n"
        for row in rows:
            text += f"{row['day']} — {row['time']} — {row['subject']}\n"
        await query.edit_message_text(text)

    elif action == "homework":
        user = get_user(query.from_user.id)
        if not user or user["role"] != "student":
            await query.edit_message_text("Сначала зарегистрируйтесь как ученик: /register")
            return
        rows = get_homework_for_class(user["class_name"])
        if not rows:
            await query.edit_message_text(f"Для класса {user['class_name']} пока нет домашки.")
            return
        text = f"📝 Домашка класса {user['class_name']}:\n\n"
        for idx, row in enumerate(rows, start=1):
            text += f"{idx}. {row['subject']}: {row['description']}\n"
        await query.edit_message_text(text)

    elif action == "grades":
        user = get_user(query.from_user.id)
        if not user or user["role"] != "student":
            await query.edit_message_text("Сначала зарегистрируйтесь как ученик: /register")
            return
        rows = get_grades_for_class(user["class_name"])
        if not rows:
            await query.edit_message_text(f"Для класса {user['class_name']} пока нет оценок.")
            return
        text = f"🏆 Оценки класса {user['class_name']}:\n\n"
        for row in rows:
            text += f"{row['student_name']} — {row['subject']}: {row['grade']}\n"
        await query.edit_message_text(text)

    elif action == "profile":
        user = get_user(query.from_user.id)
        if not user:
            await query.edit_message_text("Сначала зарегистрируйтесь: /register")
            return
        text = (
            "👤 Профиль\n"
            f"Имя: {user['name']}\n"
            f"Роль: {user['role']}\n"
            f"Класс: {user['class_name'] or '—'}"
        )
        await query.edit_message_text(text)

    elif action == "teacher_add_homework":
        await query.edit_message_text("Введите класс, предмет и домашку в одной строке:\nПример: 10А|Математика|Решить задания 1-5")
        context.user_data["pending_action"] = "homework"
        return

    elif action == "teacher_add_grade":
        await query.edit_message_text("Введите данные оценки в формате: Класс|Ученик|Предмет|Оценка\nПример: 10А|Иван|Математика|5")
        context.user_data["pending_action"] = "grade"
        return

    elif action == "teacher_add_schedule":
        await query.edit_message_text("Введите урок в формате: Класс|День|Время|Предмет\nПример: 10А|Понедельник|09:00|Математика")
        context.user_data["pending_action"] = "schedule"
        return


async def handle_teacher_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    action = context.user_data.get("pending_action")

    if action == "homework":
        try:
            class_name, subject, desc = [part.strip() for part in text.split("|", 2)]
            add_homework(class_name, subject, desc)
            await update.message.reply_text(f"Домашка добавлена для класса {class_name}.")
        except ValueError:
            await update.message.reply_text("Неверный формат. Используйте: Класс|Предмет|Домашка")
        finally:
            context.user_data.pop("pending_action", None)
        return

    if action == "grade":
        try:
            class_name, student_name, subject, grade = [part.strip() for part in text.split("|", 3)]
            add_grade(class_name, student_name, subject, grade)
            await update.message.reply_text(f"Оценка добавлена: {student_name} — {subject} — {grade}")
        except ValueError:
            await update.message.reply_text("Неверный формат. Используйте: Класс|Ученик|Предмет|Оценка")
        finally:
            context.user_data.pop("pending_action", None)
        return

    if action == "schedule":
        try:
            class_name, day, time, subject = [part.strip() for part in text.split("|", 3)]
            add_schedule(class_name, day, time, subject)
            await update.message.reply_text(f"Урок добавлен: {class_name} — {day} — {time} — {subject}")
        except ValueError:
            await update.message.reply_text("Неверный формат. Используйте: Класс|День|Время|Предмет")
        finally:
            context.user_data.pop("pending_action", None)
        return

    await update.message.reply_text("Команда не распознана. Используйте /teacher_panel")


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(CommandHandler("homework", homework_command))
    app.add_handler(CommandHandler("grades", grades_command))
    app.add_handler(CommandHandler("teacher_panel", teacher_panel))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_role)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
            CLASS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_class)],
        },
        fallbacks=[CommandHandler("cancel", cancel_register)],
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_teacher_input))

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
