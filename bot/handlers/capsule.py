from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

from bot.commands.capsule import (
    capsule_date_range,
    format_weekly_overview,
    get_checklist_state,
    get_pool_items,
    load_current_capsule,
    load_inventory,
    reset_checklist,
    toggle_checklist_item,
)
from bot.handlers.common import MAIN_MENU_TEXT, main_menu_keyboard
from storage.db import get_or_create_user

VIEW_SUBMENU, VIEW_CHECKLIST, VIEW_OVERVIEW = range(3)


def _uid(update: Update) -> int:
    user = update.effective_user
    return get_or_create_user(user.id, user.username)


def _submenu_keyboard(week: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Чеклист", callback_data="capsule:checklist")],
        [InlineKeyboardButton("📅 Обзор недели", callback_data="capsule:overview")],
        [InlineKeyboardButton("← Назад", callback_data="back:main")],
    ])


def _checklist_keyboard(uid: int, week: str, pool_items: list) -> InlineKeyboardMarkup:
    state = get_checklist_state(uid, week, pool_items)
    buttons = []
    for item_id, label, done, photo_url in state:
        mark = "🟢" if done else "⚪"
        row = [InlineKeyboardButton(
            f"{mark}  {label}",
            callback_data=f"capsule:toggle:{item_id}",
        )]
        if photo_url:
            row.append(InlineKeyboardButton("📷", url=photo_url))
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("🔄 Сбросить", callback_data="capsule:reset"),
        InlineKeyboardButton("← Назад", callback_data="capsule:back"),
    ])
    return InlineKeyboardMarkup(buttons)


def _overview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("← Назад", callback_data="capsule:back")],
    ])


def _load_and_store(context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    tg_id = context.user_data.get("telegram_id", 0)
    capsule = load_current_capsule(tg_id)
    if capsule is None:
        return None
    inventory = load_inventory(tg_id)
    context.user_data["capsule_week"] = capsule["week"]
    context.user_data["capsule_dates"] = capsule_date_range(capsule)
    context.user_data["capsule_pool"] = get_pool_items(capsule, inventory)
    context.user_data["capsule_data"] = capsule
    context.user_data["capsule_inventory"] = inventory
    return capsule


async def cmd_capsule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["telegram_id"] = update.effective_user.id
    capsule = _load_and_store(context)
    if capsule is None:
        await update.message.reply_text("Капсула ещё не готова 🙈")
        return ConversationHandler.END
    dates = context.user_data["capsule_dates"]
    await update.message.reply_text(
        f"👕 Капсула — {dates}",
        reply_markup=_submenu_keyboard(capsule["week"]),
    )
    return VIEW_SUBMENU


async def cmd_capsule_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["telegram_id"] = update.effective_user.id
    capsule = _load_and_store(context)
    if capsule is None:
        await query.edit_message_text("Капсула ещё не готова 🙈")
        return ConversationHandler.END
    dates = context.user_data["capsule_dates"]
    await query.edit_message_text(
        f"👕 Капсула — {dates}",
        reply_markup=_submenu_keyboard(capsule["week"]),
    )
    return VIEW_SUBMENU


async def on_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    week = context.user_data.get("capsule_week", "")
    dates = context.user_data.get("capsule_dates", "")
    pool_items = context.user_data.get("capsule_pool", [])
    kb = _checklist_keyboard(uid, week, pool_items)
    await query.edit_message_text(f"✅ Чеклист — {dates}:", reply_markup=kb)
    return VIEW_CHECKLIST


async def on_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    week = context.user_data.get("capsule_week", "")
    pool_items = context.user_data.get("capsule_pool", [])
    item_id = query.data.split(":", 2)[2]
    toggle_checklist_item(uid, week, item_id)
    kb = _checklist_keyboard(uid, week, pool_items)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_CHECKLIST


async def on_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    uid = _uid(update)
    week = context.user_data.get("capsule_week", "")
    pool_items = context.user_data.get("capsule_pool", [])
    reset_checklist(uid, week)
    kb = _checklist_keyboard(uid, week, pool_items)
    await query.edit_message_reply_markup(reply_markup=kb)
    return VIEW_CHECKLIST


async def on_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tg_id = context.user_data.get("telegram_id", 0)
    capsule = load_current_capsule(tg_id)
    if capsule is None:
        await query.edit_message_text("Капсула ещё не готова 🙈")
        return ConversationHandler.END
    inventory = load_inventory(tg_id)
    text = format_weekly_overview(capsule, inventory)
    await query.edit_message_text(text, reply_markup=_overview_keyboard(), parse_mode="HTML")
    return VIEW_OVERVIEW


async def on_back_to_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    week = context.user_data.get("capsule_week", "")
    dates = context.user_data.get("capsule_dates", "")
    await query.edit_message_text(
        f"👕 Капсула — {dates}",
        reply_markup=_submenu_keyboard(week),
    )
    return VIEW_SUBMENU


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    return ConversationHandler.END


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    return ConversationHandler.END


def build_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("capsule", cmd_capsule),
            CallbackQueryHandler(cmd_capsule_cb, pattern=r"^cmd:capsule$"),
        ],
        states={
            VIEW_SUBMENU: [
                CallbackQueryHandler(on_checklist, pattern=r"^capsule:checklist$"),
                CallbackQueryHandler(on_overview, pattern=r"^capsule:overview$"),
                CallbackQueryHandler(back_to_main, pattern=r"^back:main$"),
            ],
            VIEW_CHECKLIST: [
                CallbackQueryHandler(on_toggle, pattern=r"^capsule:toggle:"),
                CallbackQueryHandler(on_reset, pattern=r"^capsule:reset$"),
                CallbackQueryHandler(on_back_to_submenu, pattern=r"^capsule:back$"),
            ],
            VIEW_OVERVIEW: [
                CallbackQueryHandler(on_back_to_submenu, pattern=r"^capsule:back$"),
            ],
        },
        fallbacks=[
            CommandHandler("start", end_conversation),
            CommandHandler("capsule", cmd_capsule),
        ],
        allow_reentry=True,
        per_message=False,
    )
