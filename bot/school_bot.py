import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в онлайн-школу! 🏫\n"
        "Команды:\n"
        "/schedule\n"
        "/homework\n"
        "/grades\n"
        "/profile"
    )


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/school/schedule")
        data = resp.json()

    text = "Расписание:\n"
    for item in data:
        text += f"{item['day']} {item['time']} — {item['subject']} ({item['class_name']})\n"
    await update.message.reply_text(text)


async def homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/school/homework")
        data = resp.json()

    text = "Домашние задания:\n"
    for item in data:
        text += f"{item['title']} — {item['subject']} ({item['due_date']})\n"
    await update.message.reply_text(text)


async def grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/school/grades")
        data = resp.json()

    text = "Оценки:\n"
    for item in data:
        text += f"{item['subject']}: {item['value']}\n"
    await update.message.reply_text(text)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Профиль:\n"
        f"Имя: {user.first_name} {user.last_name or ''}\n"
        f"Telegram ID: {user.id}"
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("homework", homework))
    app.add_handler(CommandHandler("grades", grades))
    app.add_handler(CommandHandler("profile", profile))
    app.run_polling()


if __name__ == "__main__":
    main()
