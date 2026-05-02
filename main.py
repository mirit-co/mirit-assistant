import logging
import traceback

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from bot.handlers.common import MAIN_MENU_TEXT, main_menu_keyboard
from bot.handlers.lists import build_handler as lists_handler
from bot.handlers.knowledge import build_handler as knowledge_handler
from storage.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update %s:\n%s", update, traceback.format_exc())


def is_allowed(telegram_id: int) -> bool:
    if not config.ALLOWED_USERS:
        return True
    return telegram_id in config.ALLOWED_USERS


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("lists", "Управление списками"),
        BotCommand("knowledge", "База знаний"),
    ])


def main():
    init_db()
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(lists_handler())
    app.add_handler(knowledge_handler())
    app.add_error_handler(error_handler)

    logger.info("Starting polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
