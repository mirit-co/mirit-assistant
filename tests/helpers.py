import asyncio

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Message


def _markup_key(msg: Message) -> str:
    if not msg or not msg.reply_markup:
        return ""
    return "|".join(
        btn.text
        for row in msg.reply_markup.rows
        for btn in row.buttons
    )


async def _wait_for_change(client: TelegramClient, bot, after_id: int,
                           edited_msg_id: int = None,
                           edited_before: tuple = None,
                           timeout: int = 5) -> Message:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(0.3)
        msgs = await client.get_messages(bot, limit=1)
        if msgs and msgs[0].id > after_id and not msgs[0].out:
            return msgs[0]
        if edited_msg_id and edited_before:
            m = await client.get_messages(bot, ids=edited_msg_id)
            if m:
                current = (m.text or "", _markup_key(m))
                if current != edited_before:
                    return m
    raise TimeoutError(f"No bot response within {timeout}s")


async def send_and_wait(client: TelegramClient, bot, text: str, timeout: int = 3) -> Message:
    before = await client.get_messages(bot, limit=1)
    before_id = before[0].id if before else 0
    try:
        await client.send_message(bot, text)
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        await client.send_message(bot, text)
    await asyncio.sleep(0.2)
    return await _wait_for_change(client, bot, after_id=before_id, timeout=timeout)


async def send_file_and_wait(client: TelegramClient, bot, file_path: str,
                              caption: str = "", timeout: int = 10) -> Message:
    before = await client.get_messages(bot, limit=1)
    before_id = before[0].id if before else 0
    try:
        await client.send_file(bot, file_path, caption=caption, parse_mode=None)
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        await client.send_file(bot, file_path, caption=caption, parse_mode=None)
    await asyncio.sleep(0.2)
    return await _wait_for_change(client, bot, after_id=before_id, timeout=timeout)


async def click_and_wait(client: TelegramClient, bot, message: Message,
                         label: str, timeout: int = 3) -> Message:
    before = await client.get_messages(bot, limit=1)
    before_id = before[0].id if before else 0
    # Capture baseline before click to avoid race with fast bot edits
    snapshot = (message.text or "", _markup_key(message))
    await message.click(text=lambda t: label in t)
    return await _wait_for_change(client, bot, after_id=before_id,
                                  edited_msg_id=message.id,
                                  edited_before=snapshot, timeout=timeout)


def has_button(message: Message, label: str) -> bool:
    if not message or not message.reply_markup:
        return False
    return any(
        label in btn.text
        for row in message.reply_markup.rows
        for btn in row.buttons
    )


def get_button_labels(message: Message) -> list[str]:
    if not message or not message.reply_markup:
        return []
    return [btn.text for row in message.reply_markup.rows for btn in row.buttons]
