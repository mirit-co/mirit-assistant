import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import config
from dispatcher import dispatch
from router import route
from storage.db import get_or_create_user, init_db

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
        "Умею:\n"
        "• Управлять списками: книги, фильмы, идеи\n"
        "• Хранить заметки и базу знаний\n\n"
        "Просто пиши что нужно, например:\n"
        "— добавь Dune в список книг\n"
        "— сохрани заметку: REST vs GraphQL — ...\n"
        "— покажи список фильмов\n"
        "— найди заметки про dbt\n\n"
        "/help — справка"
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "*Списки:*\n"
        "• добавь [item] в список [name]\n"
        "• покажи список [name]\n"
        "• отметь [item] как выполненное в [name]\n"
        "• покажи все мои списки\n\n"
        "*База знаний:*\n"
        "• сохрани заметку: [текст]\n"
        "• найди [запрос]\n"
        "• покажи последние заметки\n"
        "• заметка [id]",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_allowed(user.id):
        await update.message.reply_text("У тебя нет доступа к этому боту.")
        return

    text = update.message.text.strip()
    if not text:
        return

    user_id = get_or_create_user(user.id, user.username)
    intent = route(text)
    logger.info("User %s → intent: %s", user.id, intent)
    response = dispatch(intent, user_id)

    await update.message.reply_text(response, parse_mode="Markdown")


def main():
    init_db()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Starting polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
