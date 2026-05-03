"""Full E2E tests for the /lists flow."""
from uuid import uuid4

from tests.conftest import TEST_LIST_NAME, run
from tests.helpers import click_and_wait, get_button_labels, has_button, send_and_wait


def _open_test_list(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/lists"))
    assert has_button(msg, TEST_LIST_NAME), f"Test list '{TEST_LIST_NAME}' not visible"
    return run(click_and_wait(tg_client, bot_username, msg, TEST_LIST_NAME))


def test_lists_command_shows_test_list(tg_client, bot_username):
    msg = run(send_and_wait(tg_client, bot_username, "/lists"))
    assert "Твои списки" in msg.text
    assert has_button(msg, TEST_LIST_NAME)


def test_open_list_shows_items_and_buttons(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    assert TEST_LIST_NAME in msg.text
    assert has_button(msg, "item_alpha")
    assert has_button(msg, "item_beta")
    assert has_button(msg, "➕ Добавить")
    assert has_button(msg, "🗑 Изменить")
    assert has_button(msg, "🔄 Сбросить")
    assert has_button(msg, "← Назад")


def test_add_item_appears_in_list(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "➕ Добавить"))
    assert "Что добавить" in msg.text

    item_name = f"new_{uuid4().hex[:6]}"
    msg = run(send_and_wait(tg_client, bot_username, item_name))
    assert f"✅ Добавил «{item_name}»" in msg.text
    assert has_button(msg, item_name)


def test_toggle_item_done(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    labels_before = get_button_labels(msg)
    alpha_label = next(l for l in labels_before if "item_alpha" in l)
    assert alpha_label.startswith("⚪"), "Expected item_alpha to be not done initially"

    msg = run(click_and_wait(tg_client, bot_username, msg, "item_alpha"))
    labels_after = get_button_labels(msg)
    alpha_label_after = next(l for l in labels_after if "item_alpha" in l)
    assert alpha_label_after.startswith("🟢")


def test_toggle_item_back_to_undone(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "item_alpha"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "item_alpha"))
    labels = get_button_labels(msg)
    alpha_label = next(l for l in labels if "item_alpha" in l)
    assert alpha_label.startswith("⚪")


def test_reset_all_marks_items_undone(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "item_alpha"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "item_beta"))

    labels_before = get_button_labels(msg)
    assert any("🟢" in l and "item_alpha" in l for l in labels_before)
    assert any("🟢" in l and "item_beta" in l for l in labels_before)

    msg = run(click_and_wait(tg_client, bot_username, msg, "🔄 Сбросить"))
    labels_after = get_button_labels(msg)
    assert all("🟢" not in l for l in labels_after if "item_" in l)


def test_edit_mode_shows_delete_buttons(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "🗑 Изменить"))
    assert has_button(msg, "🗑")
    assert has_button(msg, "✅ Готово")
    assert not has_button(msg, "➕ Добавить")


def test_exit_edit_mode_restores_buttons(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "🗑 Изменить"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "✅ Готово"))
    assert has_button(msg, "➕ Добавить")
    assert has_button(msg, "🗑 Изменить")


def test_delete_item_removes_it(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "➕ Добавить"))
    disposable = f"del_{uuid4().hex[:6]}"
    msg = run(send_and_wait(tg_client, bot_username, disposable))
    assert has_button(msg, disposable)

    msg = run(click_and_wait(tg_client, bot_username, msg, "🗑 Изменить"))
    msg = run(click_and_wait(tg_client, bot_username, msg, disposable))
    assert not has_button(msg, disposable)


def test_visibility_toggle(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    labels = get_button_labels(msg)
    vis_label = next(l for l in labels if "Приватный" in l or "Общий" in l)
    is_private = "Приватный" in vis_label

    msg = run(click_and_wait(tg_client, bot_username, msg, vis_label))
    labels_after = get_button_labels(msg)
    new_vis_label = next(l for l in labels_after if "Приватный" in l or "Общий" in l)
    assert ("Общий" in new_vis_label) == is_private

    run(click_and_wait(tg_client, bot_username, msg, new_vis_label))


def test_back_from_items_shows_list_screen(tg_client, bot_username):
    msg = _open_test_list(tg_client, bot_username)
    msg = run(click_and_wait(tg_client, bot_username, msg, "← Назад"))
    assert "Твои списки" in msg.text
    assert has_button(msg, TEST_LIST_NAME)
