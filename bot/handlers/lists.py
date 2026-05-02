from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.commands.lists import Lists
from storage.db import get_conn, get_or_create_user

command = Lists()

VIEW_LISTS, VIEW_ITEMS, WAIT_ADD_ITEM = range(3)


def _uid(update: Update) -> int:
    user = update.effective_user
    return get_or_create_user(user.id, user.username)


def _lists_keyboard(user_id: int) -> InlineKeyboardMarkup:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT list_name FROM lists WHERE user_id=? ORDER BY list_name",
            (user_id,),
        ).fetchall()
    buttons = [[InlineKeyboardButton(r["list_name"], callback_data=f"list:{r['list_name']}")] for r in rows]
    buttons.append([InlineKeyboardButton("✏️ Новый список", callback_data="list:__new__")])
    return InlineKeyboardMarkup(buttons)


def _items_keyboard(user_id: int, list_name: str) -> InlineKeyboardMarkup:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, item, done FROM lists WHERE user_id=? AND list_name=? ORDER BY created_at",
            (user_id, list_name),
        ).fetchall()
    buttons = []
    for row in rows:
        mark = "☑" if row["done"] else "☐"
        buttons.append([InlineKeyboardButton(
            f"{mark} {row['item']}",
            callback_data=f"toggle:{list_name}:{row['id']}",
        )])
    buttons.append([
        InlineKeyboardButton("➕ Добавить", callback_data=f"add:{list_name}"),
        InlineKeyboardButton("🔄 Сбросить всё", callback_data=f"reset_all:{list_name}"),
        InlineKeyboardButton("← Назад", callback_data="back:lists"),
    ])
    return InlineKeyboardMarkup(buttons)


async def cmd_lists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    kb = _lists_keyboard(uid)
    await update.message.reply_text("📚 Твои списки:", reply_markup=kb)
    return VIEW_LISTS


async def on_list_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    list_name = query.data.split(":", 1)[1]

    if list_name == "__new__":
        await query.edit_message_text("Напиши название нового списка:")
        context.user_data["adding_to"] = "__new_list__"
        return WAIT_ADD_ITEM

    context.user_data["current_list"] = list_name
    kb = _items_keyboard(uid, list_name)
    await query.edit_message_text(f"📋 *{list_name}*", parse_mode="Markdown", reply_markup=kb)
    return VIEW_ITEMS


async def on_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    _, list_name, item_id = query.data.split(":", 2)
    command.execute("toggle", {"list_name": list_name, "item_id": int(item_id)}, uid)
    kb = _items_keyboard(uid, list_name)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_ITEMS


async def on_reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    list_name = query.data.split(":", 1)[1]
    command.execute("reset_all", {"list_name": list_name}, uid)
    kb = _items_keyboard(uid, list_name)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_ITEMS


async def on_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    list_name = query.data.split(":", 1)[1]
    context.user_data["adding_to"] = list_name
    await query.edit_message_text(f"Что добавить в *{list_name}*?", parse_mode="Markdown")
    return WAIT_ADD_ITEM


async def on_back_lists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    kb = _lists_keyboard(uid)
    await query.edit_message_text("📚 Твои списки:", reply_markup=kb)
    return VIEW_LISTS


async def receive_item_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    text = update.message.text.strip()
    list_name = context.user_data.get("adding_to", "misc")

    if list_name == "__new_list__":
        context.user_data["current_list"] = text
        kb = _items_keyboard(uid, text)
        await update.message.reply_text(f"📋 *{text}*", parse_mode="Markdown", reply_markup=kb)
        return VIEW_ITEMS

    command.execute("add", {"list_name": list_name, "item": text}, uid)
    kb = _items_keyboard(uid, list_name)
    await update.message.reply_text(
        f"✅ Добавил «{text}»\n\n📋 *{list_name}*", parse_mode="Markdown", reply_markup=kb
    )
    return VIEW_ITEMS


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("lists", cmd_lists)],
        states={
            VIEW_LISTS: [
                CallbackQueryHandler(on_list_selected, pattern=r"^list:"),
            ],
            VIEW_ITEMS: [
                CallbackQueryHandler(on_list_selected, pattern=r"^list:"),
                CallbackQueryHandler(on_toggle, pattern=r"^toggle:"),
                CallbackQueryHandler(on_reset_all, pattern=r"^reset_all:"),
                CallbackQueryHandler(on_add, pattern=r"^add:"),
                CallbackQueryHandler(on_back_lists, pattern=r"^back:lists"),
            ],
            WAIT_ADD_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
