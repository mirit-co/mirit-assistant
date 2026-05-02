from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU_TEXT = "Выбери раздел:"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Списки", callback_data="cmd:lists")],
        [InlineKeyboardButton("📚 База знаний", callback_data="cmd:knowledge")],
    ])
