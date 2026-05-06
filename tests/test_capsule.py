"""E2E tests for the /capsule flow."""
import sqlite3

import pytest

from tests.conftest import _DB_PATH, run
from tests.helpers import click_and_wait, get_button_labels, has_button, send_and_wait


@pytest.fixture(autouse=True)
def reset_capsule_state():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("UPDATE capsule_checklist SET done=0")
    conn.commit()
    conn.close()


def _open_capsule(tg_client, bot_username):
    return run(send_and_wait(tg_client, bot_username, "/capsule"))


def _open_checklist(tg_client, bot_username):
    msg = _open_capsule(tg_client, bot_username)
    return run(click_and_wait(tg_client, bot_username, msg, "✅ Чеклист"))


def test_capsule_command_shows_submenu(tg_client, bot_username):
    msg = _open_capsule(tg_client, bot_username)
    assert "Капсула" in msg.text
    assert has_button(msg, "✅ Чеклист")
    assert has_button(msg, "📅 Обзор недели")
    assert has_button(msg, "← Назад")


def test_capsule_opens_from_main_menu(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/start"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "👕 Капсула"))
    assert "Капсула" in msg.text
    assert has_button(msg, "✅ Чеклист")


def test_checklist_shows_pool_items(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    assert "Чеклист" in msg.text
    labels = get_button_labels(msg)
    assert any(lbl.startswith("⚪") for lbl in labels)
    assert has_button(msg, "📷")
    assert has_button(msg, "🔄 Сбросить")
    assert has_button(msg, "← Назад")


def test_checklist_toggle_item_done(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    labels = get_button_labels(msg)
    first_unchecked = next(lbl for lbl in labels if lbl.startswith("⚪"))
    item_name = first_unchecked[2:].strip()

    msg = run(click_and_wait(tg_client, bot_username, msg, first_unchecked))
    labels_after = get_button_labels(msg)
    assert any(lbl.startswith("🟢") and item_name in lbl for lbl in labels_after)


def test_checklist_toggle_item_back_to_undone(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    labels = get_button_labels(msg)
    first_unchecked = next(lbl for lbl in labels if lbl.startswith("⚪"))
    item_name = first_unchecked[2:].strip()

    msg = run(click_and_wait(tg_client, bot_username, msg, first_unchecked))
    labels = get_button_labels(msg)
    checked = next(lbl for lbl in labels if lbl.startswith("🟢") and item_name in lbl)
    msg = run(click_and_wait(tg_client, bot_username, msg, checked))
    labels_final = get_button_labels(msg)
    assert any(lbl.startswith("⚪") and item_name in lbl for lbl in labels_final)


def test_checklist_reset_all(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    labels = get_button_labels(msg)
    unchecked = [lbl for lbl in labels if lbl.startswith("⚪")][:2]
    for lbl in unchecked:
        msg = run(click_and_wait(tg_client, bot_username, msg, lbl))

    msg = run(click_and_wait(tg_client, bot_username, msg, "🔄 Сбросить"))
    labels_after = get_button_labels(msg)
    assert not any(lbl.startswith("🟢") for lbl in labels_after)


def test_checklist_state_persists(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    labels = get_button_labels(msg)
    first_unchecked = next(lbl for lbl in labels if lbl.startswith("⚪"))
    item_name = first_unchecked[2:].strip()

    msg = run(click_and_wait(tg_client, bot_username, msg, first_unchecked))
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "✅ Чеклист"))
    labels_after = get_button_labels(msg)
    assert any(lbl.startswith("🟢") and item_name in lbl for lbl in labels_after)


def test_weekly_overview_shows_days(tg_client, bot_username):
    msg = _open_capsule(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "📅 Обзор недели"))
    assert "Понедельник" in msg.text
    assert "°C" in msg.text
    labels = get_button_labels(msg)
    assert labels == ["← Назад"]


def test_back_from_checklist_shows_submenu(tg_client, bot_username):
    msg = _open_checklist(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Капсула" in msg.text
    assert has_button(msg, "✅ Чеклист")


def test_back_from_overview_shows_submenu(tg_client, bot_username):
    msg = _open_capsule(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "📅 Обзор недели"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Капсула" in msg.text
    assert has_button(msg, "✅ Чеклист")


def test_back_from_submenu_shows_main_menu(tg_client, bot_username):
    msg = _open_capsule(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Выбери раздел" in msg.text
    assert has_button(msg, "📋 Списки")
