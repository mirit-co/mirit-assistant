from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from skills.knowledge import KnowledgeSkill
from storage.db import get_conn, get_or_create_user

skill = KnowledgeSkill()

# States
VIEW_CATEGORIES, VIEW_CATEGORY, WAIT_SEARCH, WAIT_ADD = range(4)

# Категории — расширяй по мере надобности
CATEGORIES = [
    ("Georgian Contacts", "georgian-contacts"),
    ("Notes", "notes"),
]


def _uid(update: Update) -> int:
    user = update.effective_user
    return get_or_create_user(user.id, user.username)


def _categories_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(label, callback_data=f"cat:{key}")] for label, key in CATEGORIES]
    return InlineKeyboardMarkup(buttons)


def _category_keyboard(cat_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍 Найти", callback_data=f"search:{cat_key}"),
            InlineKeyboardButton("📋 Последние", callback_data=f"recent:{cat_key}"),
        ],
        [
            InlineKeyboardButton("➕ Добавить", callback_data=f"kadd:{cat_key}"),
            InlineKeyboardButton("← Назад", callback_data="back:knowledge"),
        ],
    ])


async def cmd_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🗂 База знаний:", reply_markup=_categories_keyboard())
    return VIEW_CATEGORIES


async def on_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":", 1)[1]
    cat_label = next((label for label, k in CATEGORIES if k == cat_key), cat_key)
    context.user_data["cat_key"] = cat_key
    context.user_data["cat_label"] = cat_label
    await query.edit_message_text(
        f"📂 *{cat_label}*", parse_mode="Markdown", reply_markup=_category_keyboard(cat_key)
    )
    return VIEW_CATEGORY


async def on_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":", 1)[1]
    context.user_data["cat_key"] = cat_key
    await query.edit_message_text("Что ищешь?")
    return WAIT_SEARCH


async def on_recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    cat_key = query.data.split(":", 1)[1]
    cat_label = next((label for label, k in CATEGORIES if k == cat_key), cat_key)

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM notes WHERE user_id=? AND tags LIKE ? ORDER BY created_at DESC LIMIT 10",
            (uid, f"%{cat_key}%"),
        ).fetchall()

    if not rows:
        text = f"В разделе *{cat_label}* пока нет заметок."
    else:
        lines = [f"[{r['id']}] {r['title'] or 'без названия'} — {r['created_at'][:10]}" for r in rows]
        text = f"📋 *{cat_label}*:\n" + "\n".join(lines)

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=_category_keyboard(cat_key))
    return VIEW_CATEGORY


async def on_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":", 1)[1]
    context.user_data["cat_key"] = cat_key
    await query.edit_message_text("Напиши заметку (можно с заголовком через «:»):\nПример: *Гия Мамаладзе: +995 555 123456*", parse_mode="Markdown")
    return WAIT_ADD


async def on_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🗂 База знаний:", reply_markup=_categories_keyboard())
    return VIEW_CATEGORIES


async def receive_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    query_text = update.message.text.strip()
    cat_key = context.user_data.get("cat_key", "")
    cat_label = next((label for label, k in CATEGORIES if k == cat_key), cat_key)

    # Search within category (tagged with cat_key)
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, title, content, created_at FROM notes
               WHERE user_id=? AND tags LIKE ?
               AND (content LIKE ? OR title LIKE ?)
               ORDER BY created_at DESC LIMIT 5""",
            (uid, f"%{cat_key}%", f"%{query_text}%", f"%{query_text}%"),
        ).fetchall()

    if not rows:
        text = f"Ничего не нашёл в *{cat_label}* по запросу «{query_text}»."
    else:
        lines = []
        for row in rows:
            title = row["title"] or f"note #{row['id']}"
            preview = row["content"][:100].replace("\n", " ")
            lines.append(f"*{title}*\n{preview}")
        text = f"🔍 *{cat_label}* — {len(rows)} результатов:\n\n" + "\n\n".join(lines)

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=_category_keyboard(cat_key))
    return VIEW_CATEGORY


async def receive_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = _uid(update)
    text = update.message.text.strip()
    cat_key = context.user_data.get("cat_key", "notes")
    cat_label = next((label for label, k in CATEGORIES if k == cat_key), cat_key)

    # Split "Title: content" if colon present
    if ":" in text:
        title, content = text.split(":", 1)
        title = title.strip()
        content = content.strip()
    else:
        title, content = "", text

    skill.execute("save", {"content": content, "title": title, "tags": cat_key}, uid)
    await update.message.reply_text(
        f"💾 Сохранено в *{cat_label}*", parse_mode="Markdown",
        reply_markup=_category_keyboard(cat_key),
    )
    return VIEW_CATEGORY


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("knowledge", cmd_knowledge)],
        states={
            VIEW_CATEGORIES: [
                CallbackQueryHandler(on_category, pattern=r"^cat:"),
            ],
            VIEW_CATEGORY: [
                CallbackQueryHandler(on_search, pattern=r"^search:"),
                CallbackQueryHandler(on_recent, pattern=r"^recent:"),
                CallbackQueryHandler(on_add, pattern=r"^kadd:"),
                CallbackQueryHandler(on_back, pattern=r"^back:knowledge"),
                CallbackQueryHandler(on_category, pattern=r"^cat:"),
            ],
            WAIT_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search),
            ],
            WAIT_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_add),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )
