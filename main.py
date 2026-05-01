import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from handlers.lists import build_handler as lists_handler
from handlers.knowledge import build_handler as knowledge_handler
from storage.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_allowed(telegram_id: int) -> bool:
    if not config.ALLOWED_USERS:
        return True
    return telegram_id in config.ALLOWED_USERS


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "Привет! Я твой личный ассистент.\n\n"
        "Команды:\n"
        "/lists — управление списками\n"
        "/knowledge — база знаний\n"
        "/cancel — отменить текущее действие\n"
        "/help — справка"
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "/lists — книги, фильмы, идеи и другие списки\n"
        "/knowledge — база знаний по категориям\n"
        "/cancel — выйти из текущего сценария"
    )


def main():
    init_db()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(lists_handler())
    app.add_handler(knowledge_handler())

    logger.info("Starting polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
