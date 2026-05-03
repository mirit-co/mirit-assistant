import asyncio
import os
import sqlite3
import threading
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path.home() / ".claude" / "telegram-mcp" / ".env", override=False)

TEST_LIST_NAME = "__e2e_test__"
TEST_DOC_TITLE = "e2e-test-doc"
_DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent.parent / "data" / "assistant.db"))

# Background event loop that runs continuously — Telethon needs it to receive updates
_bg_loop: asyncio.AbstractEventLoop = None
_bg_thread: threading.Thread = None


def _start_bg_loop():
    global _bg_loop
    _bg_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bg_loop)
    _bg_loop.run_forever()


def run(coro, timeout=30):
    """Submit coroutine to the background event loop and wait for result."""
    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    return future.result(timeout=timeout)


@pytest.fixture(scope="session", autouse=True)
def _bg_event_loop():
    global _bg_thread
    _bg_thread = threading.Thread(target=_start_bg_loop, daemon=True)
    _bg_thread.start()
    while _bg_loop is None:
        time.sleep(0.01)
    yield
    _bg_loop.call_soon_threadsafe(_bg_loop.stop)


@pytest.fixture(scope="session")
def tg_client(_bg_event_loop):
    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    session_string = os.environ["TELEGRAM_SESSION_STRING"]

    async def _connect():
        client = TelegramClient(StringSession(session_string), api_id, api_hash)
        await client.connect()
        return client

    client = run(_connect())
    yield client
    try:
        run(client.disconnect())
    except Exception:
        pass


@pytest.fixture(scope="session")
def bot_username():
    username = os.environ.get("TEST_BOT_USERNAME")
    assert username, "Set TEST_BOT_USERNAME in tests/.env"
    return username


@pytest.fixture(scope="session", autouse=True)
def seed_db(tg_client, bot_username):
    from tests.helpers import send_and_wait

    # /lists triggers get_or_create_user — /start does not
    run(send_and_wait(tg_client, bot_username, "/lists"))

    me = run(tg_client.get_me())
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row

    # Retry briefly — bot may write to DB slightly after responding
    import time
    for _ in range(10):
        row = conn.execute("SELECT id FROM users WHERE telegram_id=?", (me.id,)).fetchone()
        if row:
            break
        time.sleep(0.3)
    assert row, f"User {me.id} not in DB after /lists — is the test bot running?"
    user_id = row["id"]

    conn.execute("DELETE FROM lists WHERE user_id=? AND list_name=?", (user_id, TEST_LIST_NAME))
    conn.execute("DELETE FROM list_meta WHERE user_id=? AND list_name=?", (user_id, TEST_LIST_NAME))
    for item in ["item_alpha", "item_beta"]:
        conn.execute("INSERT INTO lists (user_id, list_name, item) VALUES (?,?,?)",
                     (user_id, TEST_LIST_NAME, item))
    conn.commit()
    conn.close()

    yield

    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "DELETE FROM lists WHERE user_id=(SELECT id FROM users WHERE telegram_id=?) AND list_name=?",
        (me.id, TEST_LIST_NAME))
    conn.execute(
        "DELETE FROM list_meta WHERE user_id=(SELECT id FROM users WHERE telegram_id=?) AND list_name=?",
        (me.id, TEST_LIST_NAME))
    conn.commit()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def seed_docs_db(tg_client, bot_username, seed_db):
    from tests.helpers import click_and_wait, send_and_wait, send_file_and_wait

    test_file = Path(__file__).parent / "fixtures" / "test_doc.txt"

    msg = run(send_and_wait(tg_client, bot_username, "/docs"))
    msg = run(click_and_wait(tg_client, bot_username, msg, "➕ Добавить"))
    msg = run(send_file_and_wait(tg_client, bot_username, str(test_file), caption=TEST_DOC_TITLE))
    # Exit the conversation so individual tests start with clean state
    run(click_and_wait(tg_client, bot_username, msg, "← Главное меню"))

    yield

    me = run(tg_client.get_me())
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "DELETE FROM docs WHERE user_id=(SELECT id FROM users WHERE telegram_id=?) AND title=?",
        (me.id, TEST_DOC_TITLE),
    )
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def reset_state():
    # Don't send /start — that would send 15 extra messages and trigger FloodWait.
    # Each test handles its own state: list tests send /lists (ConversationHandler
    # fallback resets state), smoke tests send /start explicitly.
    # A short sleep lets any delayed bot response from the previous test arrive
    # before the next test captures its baseline message ID.
    time.sleep(2)


@pytest.fixture(autouse=True)
def reset_item_states(seed_db):
    """Reset done=0 for all items in the test list before each test."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute(
        "UPDATE lists SET done=0 WHERE list_name=?",
        (TEST_LIST_NAME,),
    )
    conn.commit()
    conn.close()
