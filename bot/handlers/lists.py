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


def _get_is_shared(conn, owner_uid: int, list_name: str) -> int:
    row = conn.execute(
        "SELECT is_shared FROM list_meta WHERE user_id=? AND list_name=?",
        (owner_uid, list_name),
    ).fetchone()
    return row["is_shared"] if row else 0


def _set_shared(owner_uid: int, list_name: str, is_shared: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO list_meta (user_id, list_name, is_shared) VALUES (?, ?, ?)"
            " ON CONFLICT(user_id, list_name) DO UPDATE SET is_shared=excluded.is_shared",
            (owner_uid, list_name, is_shared),
        )


def _lists_keyboard(user_id: int) -> InlineKeyboardMarkup:
    with get_conn() as conn:
        own_rows = conn.execute(
            """SELECT DISTINCT l.list_name, COALESCE(m.is_shared, 0) as is_shared
               FROM lists l
               LEFT JOIN list_meta m ON l.user_id = m.user_id AND l.list_name = m.list_name
               WHERE l.user_id = ? ORDER BY l.list_name""",
            (user_id,),
        ).fetchall()
        shared_rows = conn.execute(
            """SELECT DISTINCT l.user_id as owner_id, l.list_name, u.username
               FROM lists l
               JOIN list_meta m ON l.user_id = m.user_id AND l.list_name = m.list_name
               JOIN users u ON l.user_id = u.id
               WHERE m.is_shared = 1 AND l.user_id != ?
               ORDER BY l.list_name""",
            (user_id,),
        ).fetchall()

    private_rows = [r for r in own_rows if not r["is_shared"]]
    public_own_rows = [r for r in own_rows if r["is_shared"]]

    buttons = []
    if private_rows:
        buttons.append([InlineKeyboardButton("🔒 Личные", callback_data="noop")])
        for r in private_rows:
            buttons.append([InlineKeyboardButton(r["list_name"], callback_data=f"list:{r['list_name']}")])

    if public_own_rows or shared_rows:
        buttons.append([InlineKeyboardButton("🌐 Общие", callback_data="noop")])
        for r in public_own_rows:
            buttons.append([InlineKeyboardButton(r["list_name"], callback_data=f"list:{r['list_name']}")])
        for r in shared_rows:
            owner = f"@{r['username']}" if r["username"] else f"#{r['owner_id']}"
            buttons.append([InlineKeyboardButton(
                f"{r['list_name']} ({owner})",
                callback_data=f"list:s:{r['owner_id']}:{r['list_name']}",
            )])

    buttons.append([InlineKeyboardButton("✏️ Новый список", callback_data="list:__new__")])
    return InlineKeyboardMarkup(buttons)


def _items_keyboard(owner_uid: int, list_name: str, edit_mode: bool = False, is_owner: bool = True) -> InlineKeyboardMarkup:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, item, done FROM lists WHERE user_id=? AND list_name=? ORDER BY created_at",
            (owner_uid, list_name),
        ).fetchall()
        is_shared = _get_is_shared(conn, owner_uid, list_name)

    buttons = []
    if edit_mode and is_owner:
        for row in rows:
            buttons.append([InlineKeyboardButton(
                f"🗑  {row['item']}",
                callback_data=f"delete:{list_name}:{row['id']}",
            )])
        buttons.append([
            InlineKeyboardButton("✅ Готово", callback_data=f"done_edit:{list_name}"),
            InlineKeyboardButton("← Назад", callback_data="back:lists"),
        ])
    else:
        for row in rows:
            mark = "🟢" if row["done"] else "⚪"
            buttons.append([InlineKeyboardButton(
                f"{mark}  {row['item']}",
                callback_data=f"toggle:{list_name}:{row['id']}",
            )])
        if is_owner:
            buttons.append([
                InlineKeyboardButton("➕ Добавить", callback_data=f"add:{list_name}"),
                InlineKeyboardButton("🗑 Изменить", callback_data=f"edit_mode:{list_name}"),
                InlineKeyboardButton("🔄 Сбросить", callback_data=f"reset_all:{list_name}"),
            ])
            vis_label = "🔒 Приватный" if not is_shared else "🌐 Общий"
            buttons.append([InlineKeyboardButton(vis_label, callback_data=f"visibility:{list_name}")])
        buttons.append([InlineKeyboardButton("← Назад", callback_data="back:lists")])
    return InlineKeyboardMarkup(buttons)


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    return VIEW_LISTS


async def cmd_lists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    kb = _lists_keyboard(uid)
    await update.message.reply_text("📚 Твои списки:", reply_markup=kb)
    return VIEW_LISTS


async def on_list_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    data = query.data[len("list:"):]

    if data == "__new__":
        await query.edit_message_text("Напиши название нового списка:")
        context.user_data["adding_to"] = "__new_list__"
        return WAIT_ADD_ITEM

    # Shared list from another user: list:s:{owner_id}:{list_name}
    if data.startswith("s:"):
        _, owner_id_str, list_name = data.split(":", 2)
        owner_uid = int(owner_id_str)
        context.user_data["current_list"] = list_name
        context.user_data["owner_uid"] = owner_uid
        kb = _items_keyboard(owner_uid, list_name, is_owner=False)
        await query.edit_message_text(f"📋 *{list_name}*", parse_mode="Markdown", reply_markup=kb)
        return VIEW_ITEMS

    list_name = data
    context.user_data["current_list"] = list_name
    context.user_data["owner_uid"] = uid
    kb = _items_keyboard(uid, list_name)
    await query.edit_message_text(f"📋 *{list_name}*", parse_mode="Markdown", reply_markup=kb)
    return VIEW_ITEMS


async def on_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    owner_uid = context.user_data.get("owner_uid", uid)
    is_owner = owner_uid == uid
    _, list_name, item_id = query.data.split(":", 2)
    command.execute("toggle", {"list_name": list_name, "item_id": int(item_id)}, owner_uid)
    kb = _items_keyboard(owner_uid, list_name, is_owner=is_owner)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_ITEMS


async def on_enter_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    list_name = query.data.split(":", 1)[1]
    kb = _items_keyboard(uid, list_name, edit_mode=True)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_ITEMS


async def on_exit_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    list_name = query.data.split(":", 1)[1]
    kb = _items_keyboard(uid, list_name, edit_mode=False)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_ITEMS


async def on_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    _, list_name, item_id = query.data.split(":", 2)
    command.execute("delete_by_id", {"item_id": int(item_id)}, uid)
    kb = _items_keyboard(uid, list_name, edit_mode=True)
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


async def on_toggle_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    list_name = query.data.split(":", 1)[1]
    with get_conn() as conn:
        current = _get_is_shared(conn, uid, list_name)
    _set_shared(uid, list_name, 1 - current)
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
    context.user_data.pop("owner_uid", None)
    kb = _lists_keyboard(uid)
    await query.edit_message_text("📚 Твои списки:", reply_markup=kb)
    return VIEW_LISTS


async def receive_item_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    text = update.message.text.strip()
    list_name = context.user_data.get("adding_to", "misc")

    if list_name == "__new_list__":
        context.user_data["current_list"] = text
        context.user_data["owner_uid"] = uid
        kb = _items_keyboard(uid, text)
        await update.message.reply_text(f"📋 *{text}*", parse_mode="Markdown", reply_markup=kb)
        return VIEW_ITEMS

    command.execute("add", {"list_name": list_name, "item": text}, uid)
    kb = _items_keyboard(uid, list_name)
    await update.message.reply_text(
        f"✅ Добавил «{text}»\n\n📋 *{list_name}*", parse_mode="Markdown", reply_markup=kb
    )
    return VIEW_ITEMS


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("lists", cmd_lists)],
        states={
            VIEW_LISTS: [
                CallbackQueryHandler(noop, pattern=r"^noop$"),
                CallbackQueryHandler(on_list_selected, pattern=r"^list:"),
            ],
            VIEW_ITEMS: [
                CallbackQueryHandler(on_list_selected, pattern=r"^list:"),
                CallbackQueryHandler(on_toggle, pattern=r"^toggle:"),
                CallbackQueryHandler(on_enter_edit, pattern=r"^edit_mode:"),
                CallbackQueryHandler(on_exit_edit, pattern=r"^done_edit:"),
                CallbackQueryHandler(on_delete, pattern=r"^delete:"),
                CallbackQueryHandler(on_reset_all, pattern=r"^reset_all:"),
                CallbackQueryHandler(on_add, pattern=r"^add:"),
                CallbackQueryHandler(on_back_lists, pattern=r"^back:lists"),
                CallbackQueryHandler(on_toggle_visibility, pattern=r"^visibility:"),
            ],
            WAIT_ADD_ITEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item_text),
            ],
        },
        fallbacks=[CommandHandler("start", end_conversation), CommandHandler("lists", cmd_lists)],
        allow_reentry=True,
        per_message=False,
    )
