from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.commands.docs import Docs
from bot.handlers.common import MAIN_MENU_TEXT, main_menu_keyboard
from storage.db import get_or_create_user

command = Docs()

VIEW_MENU, WAIT_ADD, WAIT_SEARCH = range(3)


def _uid(update: Update) -> int:
    user = update.effective_user
    return get_or_create_user(user.id, user.username)


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Добавить", callback_data="docs:add"),
            InlineKeyboardButton("🔍 Найти", callback_data="docs:search"),
        ],
        [InlineKeyboardButton("📋 Последние", callback_data="docs:recent")],
        [InlineKeyboardButton("← Главное меню", callback_data="back:main")],
    ])


def _docs_list_keyboard(rows) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows:
        icon = "🖼" if row["file_type"] == "photo" else "📄"
        title = row["title"] or f"#{row['id']}"
        buttons.append([InlineKeyboardButton(f"{icon} {title}", callback_data=f"view_doc:{row['id']}")])
    buttons.append([InlineKeyboardButton("← Назад", callback_data="docs:back_menu")])
    return InlineKeyboardMarkup(buttons)


async def cmd_docs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📁 Документы:", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def cmd_docs_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📁 Документы:", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def on_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Отправьте фото или документ.\nМожно добавить подпись — она станет названием."
    )
    return WAIT_ADD


async def on_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Что ищешь?")
    return WAIT_SEARCH


async def on_recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    rows = command.execute("list", {}, uid)
    if not rows:
        await query.edit_message_text("Документов пока нет.", reply_markup=_menu_keyboard())
    else:
        await query.edit_message_text("📋 Последние документы:", reply_markup=_docs_list_keyboard(rows))
    return VIEW_MENU


async def on_back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📁 Документы:", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def on_view_doc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    doc_id = int(query.data.split(":", 1)[1])
    row = command.execute("get", {"doc_id": doc_id}, uid)
    if not row:
        await query.answer("Документ не найден", show_alert=True)
        return VIEW_MENU
    caption = row["title"] or ""
    if row["file_type"] == "photo":
        await context.bot.send_photo(
            query.message.chat_id, row["file_id"], caption=caption, reply_markup=_menu_keyboard()
        )
    else:
        await context.bot.send_document(
            query.message.chat_id, row["file_id"], caption=caption, reply_markup=_menu_keyboard()
        )
    return VIEW_MENU


async def receive_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    msg = update.message
    today = date.today().strftime("%d.%m.%Y")

    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "photo"
        caption = msg.caption or ""
        title = caption.strip() or f"Фото {today}"
    elif msg.document:
        file_id = msg.document.file_id
        file_type = "document"
        caption = msg.caption or ""
        title = caption.strip() or msg.document.file_name or f"Документ {today}"
    else:
        await msg.reply_text("Отправьте фото или документ (или /start чтобы выйти).")
        return WAIT_ADD

    command.execute("save", {"file_id": file_id, "file_type": file_type, "title": title}, uid)
    await msg.reply_text(f"💾 Сохранено: *{title}*", parse_mode="Markdown", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def receive_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    query_text = update.message.text.strip()
    rows = command.execute("search", {"query": query_text}, uid)
    if not rows:
        await update.message.reply_text(
            f"Ничего не нашёл по запросу «{query_text}».", reply_markup=_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            f"🔍 Найдено {len(rows)}:", reply_markup=_docs_list_keyboard(rows)
        )
    return VIEW_MENU


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("docs", cmd_docs),
            CallbackQueryHandler(cmd_docs_cb, pattern=r"^cmd:docs$"),
        ],
        states={
            VIEW_MENU: [
                CallbackQueryHandler(back_to_main, pattern=r"^back:main$"),
                CallbackQueryHandler(on_add, pattern=r"^docs:add$"),
                CallbackQueryHandler(on_search, pattern=r"^docs:search$"),
                CallbackQueryHandler(on_recent, pattern=r"^docs:recent$"),
                CallbackQueryHandler(on_back_menu, pattern=r"^docs:back_menu$"),
                CallbackQueryHandler(on_view_doc, pattern=r"^view_doc:"),
            ],
            WAIT_ADD: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_add),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add),
            ],
            WAIT_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search),
            ],
        },
        fallbacks=[CommandHandler("start", end_conversation)],
        per_message=False,
        allow_reentry=True,
    )
