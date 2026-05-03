"""Smoke tests: basic navigation works end-to-end."""
from tests.conftest import run
from tests.helpers import click_and_wait, has_button, send_and_wait


def test_start_shows_main_menu(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/start"))
    assert "Выбери раздел" in msg.text
    assert has_button(msg, "📋 Списки")
    assert has_button(msg, "📁 Документы")


def test_lists_opens_from_menu(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/start"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📋 Списки"))
    assert "Твои списки" in msg.text
    assert has_button(msg, "← Назад")


def test_docs_opens_from_menu(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/start"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📁 Документы"))
    assert "Документы" in msg.text
    assert has_button(msg, "← Главное меню")


def test_back_from_lists_returns_to_main(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/start"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📋 Списки"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Выбери раздел" in msg.text
    assert has_button(msg, "📋 Списки")
