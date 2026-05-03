"""Full E2E tests for the /docs flow."""
from pathlib import Path

from tests.conftest import TEST_DOC_TITLE, run
from tests.helpers import click_and_wait, has_button, send_and_wait, send_file_and_wait

TEST_FILE = Path(__file__).parent / "fixtures" / "test_doc.txt"


def test_docs_menu_opens(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    assert "Документы" in msg.text
    assert has_button(msg, "➕ Добавить")
    assert has_button(msg, "🔍 Найти")
    assert has_button(msg, "📋 Последние")
    assert has_button(msg, "← Главное меню")


def test_docs_add_document(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "➕ Добавить"))
    assert "Отправьте фото или документ" in msg.text

    title = "test_upload_doc"
    msg = run(send_file_and_wait(tg_client, bot_username, str(TEST_FILE), caption=title))
    assert "Сохранено" in msg.text
    assert title in msg.text


def test_docs_recent_shows_test_doc(tg_client, bot_username, seed_docs_db):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📋 Последние"))
    assert "Последние документы" in msg.text
    assert has_button(msg, TEST_DOC_TITLE)


def test_docs_view_doc(tg_client, bot_username, seed_docs_db):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📋 Последние"))
    assert has_button(msg, TEST_DOC_TITLE)

    msg = run(click_and_wait(tg_client, bot_username, msg, TEST_DOC_TITLE, timeout=10))
    assert msg.document is not None or msg.photo is not None
    assert has_button(msg, "← Главное меню")


def test_docs_search_found(tg_client, bot_username, seed_docs_db):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "🔍 Найти"))
    assert "Что ищешь" in msg.text

    query = TEST_DOC_TITLE[:10]
    msg = run(send_and_wait(tg_client, bot_username, query))
    assert has_button(msg, TEST_DOC_TITLE)


def test_docs_search_not_found(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "🔍 Найти"))
    msg = run(send_and_wait(tg_client, bot_username, "zzz_nonexistent_zzz"))
    assert "Ничего не нашёл" in msg.text


def test_docs_back_to_menu(tg_client, bot_username, seed_docs_db):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "📋 Последние"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Документы" in msg.text
    assert has_button(msg, "➕ Добавить")


def test_docs_back_to_main_menu(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Главное меню"))
    assert "Выбери раздел" in msg.text
    assert has_button(msg, "📋 Списки")
