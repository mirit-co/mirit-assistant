from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU_TEXT = "Выбери раздел:"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Списки", callback_data="cmd:lists")],
        [InlineKeyboardButton("📁 Документы", callback_data="cmd:docs")],
        [InlineKeyboardButton("👕 Капсула", callback_data="cmd:capsule")],
    ])
