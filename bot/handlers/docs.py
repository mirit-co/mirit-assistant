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

from bot.commands.docs import Docs, TAGS, auto_tags_from_title, normalize_tags
from bot.handlers.common import MAIN_MENU_TEXT, main_menu_keyboard
from storage.db import get_or_create_user

command = Docs()

VIEW_MENU, WAIT_ADD, WAIT_SEARCH, WAIT_TAGS = range(4)

PAGE_SIZE = 8

_TAG_ICON = {"Руслан": "👤", "Марьяна": "👤", "Антон": "👤", "Авто": "🚗"}


def _uid(update: Update) -> int:
    user = update.effective_user
    return get_or_create_user(user.id, user.username)


def _doc_icon(file_type: str) -> str:
    return "🖼" if file_type == "photo" else "📄"


# --- keyboards ---

def _menu_keyboard() -> InlineKeyboardMarkup:
    """First screen: tag buttons (with counts, non-empty only) + actions."""
    rows = []
    counts = command.execute("tag_counts", {}, 0)
    for tag in TAGS:
        if tag in counts:
            icon = _TAG_ICON.get(tag, "🏷")
            rows.append([InlineKeyboardButton(
                f"{icon} {tag} ({counts[tag]})", callback_data=f"docs:tag:{tag}"
            )])
    rows.append([InlineKeyboardButton("📋 Все документы", callback_data="docs:all:0")])
    rows.append([
        InlineKeyboardButton("➕ Добавить", callback_data="docs:add"),
        InlineKeyboardButton("🔍 Найти", callback_data="docs:search"),
    ])
    rows.append([InlineKeyboardButton("← Главное меню", callback_data="back:main")])
    return InlineKeyboardMarkup(rows)


def _docs_list_keyboard(rows) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows:
        title = row["title"] or f"#{row['id']}"
        buttons.append([InlineKeyboardButton(
            f"{_doc_icon(row['file_type'])} {title}", callback_data=f"view_doc:{row['id']}"
        )])
    buttons.append([InlineKeyboardButton("← Назад", callback_data="docs:back_menu")])
    return InlineKeyboardMarkup(buttons)


def _all_docs_keyboard(rows, offset: int, total: int) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows:
        title = row["title"] or f"#{row['id']}"
        buttons.append([InlineKeyboardButton(
            f"{_doc_icon(row['file_type'])} {title}", callback_data=f"view_doc:{row['id']}"
        )])
    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton("◀", callback_data=f"docs:all:{max(0, offset - PAGE_SIZE)}"))
    if offset + PAGE_SIZE < total:
        nav.append(InlineKeyboardButton("▶", callback_data=f"docs:all:{offset + PAGE_SIZE}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("← Назад", callback_data="docs:back_menu")])
    return InlineKeyboardMarkup(buttons)


def _tag_picker_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for tag in TAGS:
        mark = "✅ " if tag in selected else "▫️ "
        rows.append([InlineKeyboardButton(f"{mark}{tag}", callback_data=f"docs:picktag:{tag}")])
    rows.append([InlineKeyboardButton("Готово", callback_data="docs:tags_done")])
    return InlineKeyboardMarkup(rows)


def _doc_view_keyboard(doc_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Удалить", callback_data=f"docs:del:{doc_id}")],
        [InlineKeyboardButton("← К документам", callback_data="docs:back_menu")],
    ])


# --- entry ---

async def cmd_docs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📁 Документы — выбери раздел:", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def cmd_docs_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📁 Документы — выбери раздел:", reply_markup=_menu_keyboard())
    return VIEW_MENU


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def on_back_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📁 Документы — выбери раздел:", reply_markup=_menu_keyboard())
    return VIEW_MENU


# --- browse ---

async def on_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tag = query.data.split(":", 2)[2]
    rows = command.execute("by_tag", {"tag": tag}, 0)
    if not rows:
        await query.edit_message_text(f"В разделе «{tag}» пока пусто.", reply_markup=_menu_keyboard())
    else:
        await query.edit_message_text(f"🏷 {tag}:", reply_markup=_docs_list_keyboard(rows))
    return VIEW_MENU


async def on_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    offset = int(query.data.split(":", 2)[2])
    total = command.execute("count", {}, 0)
    rows = command.execute("list", {"limit": PAGE_SIZE, "offset": offset}, 0)
    if not rows:
        await query.edit_message_text("Документов пока нет.", reply_markup=_menu_keyboard())
        return VIEW_MENU
    page = offset // PAGE_SIZE + 1
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    await query.edit_message_text(
        f"📋 Все документы ({total}) · стр. {page}/{pages}:",
        reply_markup=_all_docs_keyboard(rows, offset, total),
    )
    return VIEW_MENU


async def on_view_doc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    doc_id = int(query.data.split(":", 1)[1])
    row = command.execute("get", {"doc_id": doc_id}, 0)
    if not row:
        await query.answer("Документ не найден", show_alert=True)
        return VIEW_MENU
    tags = normalize_tags(row["tags"])
    caption = row["title"] or ""
    if tags:
        caption = f"{caption}\n🏷 {', '.join(tags)}".strip()
    # Send the file WITHOUT an inline menu — buttons on a caption-only message
    # cannot be edited later (edit_message_text fails on media messages).
    if row["file_type"] == "photo":
        await context.bot.send_photo(query.message.chat_id, row["file_id"], caption=caption)
    else:
        await context.bot.send_document(query.message.chat_id, row["file_id"], caption=caption)
    # Menu goes in a separate TEXT message so it stays editable.
    await context.bot.send_message(
        query.message.chat_id, "Документ выше ☝️", reply_markup=_doc_view_keyboard(doc_id)
    )
    return VIEW_MENU


async def on_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    doc_id = int(query.data.split(":", 2)[2])
    command.execute("delete", {"doc_id": doc_id}, 0)
    await query.edit_message_text("🗑 Документ удалён.", reply_markup=_menu_keyboard())
    return VIEW_MENU


# --- search ---

async def on_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Что ищешь?")
    return WAIT_SEARCH


async def receive_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query_text = update.message.text.strip()
    rows = command.execute("search", {"query": query_text}, 0)
    if not rows:
        await update.message.reply_text(
            f"Ничего не нашёл по запросу «{query_text}».", reply_markup=_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            f"🔍 Найдено {len(rows)}:", reply_markup=_docs_list_keyboard(rows)
        )
    return VIEW_MENU


# --- add (file → tag picker) ---

async def on_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Отправьте фото или документ.\nМожно добавить подпись — она станет названием."
    )
    return WAIT_ADD


async def receive_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    msg = update.message
    today = date.today().strftime("%d.%m.%Y")

    if msg.photo:
        file_id = msg.photo[-1].file_id
        file_type = "photo"
        title = (msg.caption or "").strip() or f"Фото {today}"
    elif msg.document:
        file_id = msg.document.file_id
        file_type = "document"
        title = (msg.caption or "").strip() or msg.document.file_name or f"Документ {today}"
    else:
        await msg.reply_text("Отправьте фото или документ (или /start чтобы выйти).")
        return WAIT_ADD

    pre = auto_tags_from_title(title)
    doc_id = command.execute("save", {"file_id": file_id, "file_type": file_type, "title": title}, uid)
    context.user_data["pending_doc_id"] = doc_id
    context.user_data["pending_tags"] = pre
    if pre:
        command.execute("set_tags", {"doc_id": doc_id, "tags": ",".join(pre)}, uid)
    await msg.reply_text(
        f"💾 Сохранено: *{title}*\nВыбери теги:",
        parse_mode="Markdown",
        reply_markup=_tag_picker_keyboard(pre),
    )
    return WAIT_TAGS


async def on_pick_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tag = query.data.split(":", 2)[2]
    selected = context.user_data.get("pending_tags", [])
    if tag in selected:
        selected.remove(tag)
    else:
        selected.append(tag)
    context.user_data["pending_tags"] = selected
    doc_id = context.user_data.get("pending_doc_id")
    if doc_id:
        ordered = [t for t in TAGS if t in selected]
        command.execute("set_tags", {"doc_id": doc_id, "tags": ",".join(ordered)}, 0)
    await query.edit_message_reply_markup(reply_markup=_tag_picker_keyboard(selected))
    return WAIT_TAGS


async def on_tags_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected = [t for t in TAGS if t in context.user_data.get("pending_tags", [])]
    context.user_data.pop("pending_doc_id", None)
    context.user_data.pop("pending_tags", None)
    label = ", ".join(selected) if selected else "без тега"
    await query.edit_message_text(f"✅ Готово. Теги: {label}", reply_markup=_menu_keyboard())
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
                CallbackQueryHandler(on_tag, pattern=r"^docs:tag:"),
                CallbackQueryHandler(on_all, pattern=r"^docs:all:"),
                CallbackQueryHandler(on_delete, pattern=r"^docs:del:"),
                CallbackQueryHandler(on_back_menu, pattern=r"^docs:back_menu$"),
                CallbackQueryHandler(on_view_doc, pattern=r"^view_doc:"),
            ],
            WAIT_ADD: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_add),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add),
            ],
            WAIT_TAGS: [
                CallbackQueryHandler(on_pick_tag, pattern=r"^docs:picktag:"),
                CallbackQueryHandler(on_tags_done, pattern=r"^docs:tags_done$"),
            ],
            WAIT_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search),
            ],
        },
        fallbacks=[CommandHandler("start", end_conversation)],
        per_message=False,
        allow_reentry=True,
    )
