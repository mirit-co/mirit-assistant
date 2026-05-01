# Build a Personal Assistant Telegram Bot

## Overview

Build a modular personal assistant bot with a Telegram interface. The bot uses the Anthropic API for intent routing and skill execution. Skills are pluggable modules — adding a new skill requires only two files.

---

## Tech Stack

- **Python 3.11+**
- **python-telegram-bot** — Telegram webhook handler
- **FastAPI** — webhook HTTP server
- **SQLite** — storage (via `sqlite3` stdlib, no ORM)
- **Anthropic API** — `claude-haiku-4-5` for routing, `claude-sonnet-4-5` for complex tasks
- **systemd** — process management on DigitalOcean droplet

---

## Project Structure

Create the following file tree at `/opt/assistant/`:

```
/opt/assistant/
├── main.py                  # FastAPI app + Telegram webhook entry point
├── config.py                # Settings loaded from environment variables
├── router.py                # Intent detection via Claude API
├── dispatcher.py            # Maps intents to skill handlers
│
├── skills/
│   ├── __init__.py
│   ├── base.py              # BaseSkill abstract class
│   ├── lists.py             # Skill: manage lists (books, movies, ideas)
│   └── knowledge.py         # Skill: save and search notes
│
├── storage/
│   ├── __init__.py
│   └── db.py                # SQLite connection + helpers
│
├── skills_registry/
│   ├── lists.md             # SKILL.md for lists skill
│   └── knowledge.md         # SKILL.md for knowledge skill
│
├── requirements.txt
├── .env.example
└── assistant.service        # systemd unit file
```

---

## Environment Variables

File: `.env.example` (user copies to `.env` and fills in values)

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=random_secret_string_for_security
ALLOWED_USERS=123456789,987654321   # Telegram user IDs, comma-separated
```

---

## File: `config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
ALLOWED_USERS = [
    int(uid.strip())
    for uid in os.environ.get("ALLOWED_USERS", "").split(",")
    if uid.strip()
]

ROUTER_MODEL = "claude-haiku-4-5-20251001"
SMART_MODEL = "claude-sonnet-4-5-20251015"

DB_PATH = "/opt/assistant/data/assistant.db"
SKILLS_REGISTRY_PATH = "/opt/assistant/skills_registry"
```

---

## File: `storage/db.py`

```python
import sqlite3
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_name TEXT NOT NULL,
                item TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

def get_or_create_user(telegram_id: int, username: str = None) -> int:
    """Returns internal user id."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username)
        )
        return cursor.lastrowid
```

---

## File: `skills/base.py`

```python
from abc import ABC, abstractmethod

class BaseSkill(ABC):
    name: str = ""
    description: str = ""  # Used by router to understand what this skill does

    @abstractmethod
    def execute(self, action: str, params: dict, user_id: int) -> str:
        """
        Execute a skill action.
        Returns a string response to send back to the user.
        """
        pass
```

---

## File: `skills_registry/lists.md`

```markdown
# Skill: lists

Manages named lists for the user. Each list has a name (e.g. "books", "movies", "ideas", "shopping").

## Actions

- **add**: Add an item to a list.
  Params: list_name (str), item (str)
  Example: "добавь Dune в список книг" → action=add, list_name=books, item=Dune

- **show**: Show all items in a list.
  Params: list_name (str)
  Example: "покажи мой список книг" → action=show, list_name=books

- **done**: Mark an item as done/read/watched.
  Params: list_name (str), item (str)
  Example: "отметь Dune как прочитанное" → action=done, list_name=books, item=Dune

- **delete**: Remove an item from a list.
  Params: list_name (str), item (str)

- **all_lists**: Show all list names the user has.
  Params: none

## Notes
- List names should be normalized to lowercase English: books, movies, ideas, shopping, etc.
- If user says "книги" → list_name=books; "фильмы" → list_name=movies; "идеи" → list_name=ideas
```

---

## File: `skills_registry/knowledge.md`

```markdown
# Skill: knowledge

Saves notes and lets the user search through them. Think of it as a personal knowledge base.

## Actions

- **save**: Save a note.
  Params: content (str), title (str, optional), tags (str, optional, comma-separated)
  Example: "сохрани заметку: dbt best practices — всегда используй sources" → action=save, content=..., title=dbt best practices

- **search**: Search notes by keyword or tag.
  Params: query (str)
  Example: "найди всё про dbt" → action=search, query=dbt

- **list**: Show recent notes (titles only).
  Params: limit (int, default 10)

- **get**: Get full content of a specific note.
  Params: note_id (int)

## Notes
- Tags are optional but useful for filtering.
- Search checks both content and title.
```

---

## File: `skills/lists.py`

```python
from skills.base import BaseSkill
from storage.db import get_conn

class ListsSkill(BaseSkill):
    name = "lists"
    description = open("skills_registry/lists.md").read()

    def execute(self, action: str, params: dict, user_id: int) -> str:
        if action == "add":
            return self._add(user_id, params.get("list_name", "misc"), params.get("item", ""))
        elif action == "show":
            return self._show(user_id, params.get("list_name", ""))
        elif action == "done":
            return self._done(user_id, params.get("list_name", ""), params.get("item", ""))
        elif action == "delete":
            return self._delete(user_id, params.get("list_name", ""), params.get("item", ""))
        elif action == "all_lists":
            return self._all_lists(user_id)
        else:
            return f"Неизвестное действие: {action}"

    def _add(self, user_id: int, list_name: str, item: str) -> str:
        if not item:
            return "Не указан элемент для добавления."
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lists (user_id, list_name, item) VALUES (?, ?, ?)",
                (user_id, list_name, item)
            )
        return f"✅ Добавил «{item}» в список *{list_name}*"

    def _show(self, user_id: int, list_name: str) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT item, done FROM lists WHERE user_id=? AND list_name=? ORDER BY created_at",
                (user_id, list_name)
            ).fetchall()
        if not rows:
            return f"Список *{list_name}* пуст."
        lines = []
        for i, row in enumerate(rows, 1):
            mark = "✓" if row["done"] else "○"
            lines.append(f"{i}. {mark} {row['item']}")
        return f"📋 *{list_name}* ({len(rows)}):\n" + "\n".join(lines)

    def _done(self, user_id: int, list_name: str, item: str) -> str:
        with get_conn() as conn:
            result = conn.execute(
                "UPDATE lists SET done=1 WHERE user_id=? AND list_name=? AND item LIKE ?",
                (user_id, list_name, f"%{item}%")
            )
        if result.rowcount == 0:
            return f"Не нашёл «{item}» в списке {list_name}."
        return f"✅ Отметил «{item}» как выполненное"

    def _delete(self, user_id: int, list_name: str, item: str) -> str:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM lists WHERE user_id=? AND list_name=? AND item LIKE ?",
                (user_id, list_name, f"%{item}%")
            )
        return f"🗑 Удалил «{item}» из списка {list_name}"

    def _all_lists(self, user_id: int) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT list_name, COUNT(*) as cnt FROM lists WHERE user_id=? GROUP BY list_name",
                (user_id,)
            ).fetchall()
        if not rows:
            return "У тебя пока нет списков."
        lines = [f"• {row['list_name']} ({row['cnt']} элем.)" for row in rows]
        return "📚 Твои списки:\n" + "\n".join(lines)
```

---

## File: `skills/knowledge.py`

```python
from skills.base import BaseSkill
from storage.db import get_conn

class KnowledgeSkill(BaseSkill):
    name = "knowledge"
    description = open("skills_registry/knowledge.md").read()

    def execute(self, action: str, params: dict, user_id: int) -> str:
        if action == "save":
            return self._save(user_id, params)
        elif action == "search":
            return self._search(user_id, params.get("query", ""))
        elif action == "list":
            return self._list(user_id, params.get("limit", 10))
        elif action == "get":
            return self._get(user_id, params.get("note_id"))
        else:
            return f"Неизвестное действие: {action}"

    def _save(self, user_id: int, params: dict) -> str:
        content = params.get("content", "")
        if not content:
            return "Нет содержимого для сохранения."
        title = params.get("title", "")
        tags = params.get("tags", "")
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (user_id, title, content, tags) VALUES (?, ?, ?, ?)",
                (user_id, title, content, tags)
            )
            note_id = cursor.lastrowid
        title_display = f"«{title}»" if title else f"#note{note_id}"
        return f"💾 Сохранил заметку {title_display} (id: {note_id})"

    def _search(self, user_id: int, query: str) -> str:
        if not query:
            return "Укажи запрос для поиска."
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT id, title, content, created_at FROM notes
                   WHERE user_id=? AND (content LIKE ? OR title LIKE ? OR tags LIKE ?)
                   ORDER BY created_at DESC LIMIT 5""",
                (user_id, f"%{query}%", f"%{query}%", f"%{query}%")
            ).fetchall()
        if not rows:
            return f"Ничего не нашёл по запросу «{query}»."
        lines = []
        for row in rows:
            title = row["title"] or f"note #{row['id']}"
            date = row["created_at"][:10]
            preview = row["content"][:80].replace("\n", " ")
            lines.append(f"[{row['id']}] *{title}* ({date})\n    {preview}…")
        return f"🔍 Найдено {len(rows)} заметок:\n\n" + "\n\n".join(lines)

    def _list(self, user_id: int, limit: int) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at FROM notes WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        if not rows:
            return "База знаний пуста. Сохрани первую заметку!"
        lines = [
            f"[{r['id']}] {r['title'] or 'без названия'} — {r['created_at'][:10]}"
            for r in rows
        ]
        return f"📝 Последние заметки ({len(rows)}):\n" + "\n".join(lines)

    def _get(self, user_id: int, note_id) -> str:
        if not note_id:
            return "Укажи id заметки."
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user_id)
            ).fetchone()
        if not row:
            return f"Заметка #{note_id} не найдена."
        title = row["title"] or f"note #{row['id']}"
        tags = f"\nТеги: {row['tags']}" if row["tags"] else ""
        return f"📄 *{title}*{tags}\n\n{row['content']}"
```

---

## File: `router.py`

This is the core of the system. It reads all SKILL.md files and sends the user message to Claude, which returns a structured JSON intent.

```python
import os
import json
import anthropic
from config import ANTHROPIC_API_KEY, ROUTER_MODEL, SKILLS_REGISTRY_PATH

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_skills_context() -> str:
    """Load all SKILL.md files and concatenate them."""
    parts = []
    registry_dir = SKILLS_REGISTRY_PATH
    for fname in sorted(os.listdir(registry_dir)):
        if fname.endswith(".md"):
            with open(os.path.join(registry_dir, fname)) as f:
                parts.append(f.read())
    return "\n\n---\n\n".join(parts)

SYSTEM_PROMPT = """You are an intent router for a personal assistant bot.

Given a user message, determine which skill to call and what parameters to pass.

Available skills:
{skills_context}

Respond ONLY with valid JSON in this exact format:
{{
  "skill": "<skill_name>",
  "action": "<action_name>",
  "params": {{<key>: <value>}},
  "confidence": <0.0-1.0>
}}

If the message doesn't match any skill, respond:
{{
  "skill": "unknown",
  "action": "none",
  "params": {{}},
  "confidence": 0.0
}}

Rules:
- skill must be one of the defined skill names
- action must be one of the actions defined for that skill
- params must match the params defined for that action
- Be generous with confidence — prefer routing over rejecting
- User messages may be in Russian or English
"""

def route(user_message: str) -> dict:
    """
    Returns intent dict: {skill, action, params, confidence}
    """
    skills_context = load_skills_context()
    system = SYSTEM_PROMPT.format(skills_context=skills_context)

    response = client.messages.create(
        model=ROUTER_MODEL,
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": user_message}]
    )

    raw = response.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract JSON from response if wrapped in markdown
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"skill": "unknown", "action": "none", "params": {}, "confidence": 0.0}
```

---

## File: `dispatcher.py`

```python
from skills.lists import ListsSkill
from skills.knowledge import KnowledgeSkill

# Registry: add new skills here
SKILLS = {
    skill.name: skill
    for skill in [ListsSkill(), KnowledgeSkill()]
}

FALLBACK_RESPONSES = [
    "Не понял запрос. Попробуй иначе.",
    "Можешь сохранить заметку, управлять списками.",
    "Напиши /help чтобы увидеть что я умею.",
]

def dispatch(intent: dict, user_id: int) -> str:
    skill_name = intent.get("skill")
    action = intent.get("action")
    params = intent.get("params", {})
    confidence = intent.get("confidence", 0.0)

    if skill_name == "unknown" or confidence < 0.3:
        return FALLBACK_RESPONSES[0]

    skill = SKILLS.get(skill_name)
    if not skill:
        return f"Навык «{skill_name}» не найден."

    return skill.execute(action, params, user_id)
```

---

## File: `main.py`

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import config
from storage.db import init_db, get_or_create_user
from router import route
from dispatcher import dispatch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Build Telegram application
bot_app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await bot_app.initialize()
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    await bot.set_webhook(
        url=config.WEBHOOK_URL,
        secret_token=config.WEBHOOK_SECRET
    )
    logger.info("Webhook set: %s", config.WEBHOOK_URL)
    yield
    await bot_app.shutdown()

fastapi_app = FastAPI(lifespan=lifespan)


# --- Access control ---

def is_allowed(telegram_id: int) -> bool:
    if not config.ALLOWED_USERS:
        return True  # No restriction if list is empty
    return telegram_id in config.ALLOWED_USERS


# --- Telegram handlers ---

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "Привет! Я твой личный ассистент.\n\n"
        "Умею:\n"
        "• Управлять списками: книги, фильмы, идеи\n"
        "• Хранить заметки и базу знаний\n\n"
        "Просто пиши что нужно, например:\n"
        "— добавь Dune в список книг\n"
        "— сохрани заметку: REST vs GraphQL — ...\n"
        "— покажи список фильмов\n"
        "— найди заметки про dbt\n\n"
        "/help — справка"
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text(
        "*Списки:*\n"
        "• добавь [item] в список [name]\n"
        "• покажи список [name]\n"
        "• отметь [item] как выполненное в [name]\n"
        "• покажи все мои списки\n\n"
        "*База знаний:*\n"
        "• сохрани заметку: [текст]\n"
        "• найди [запрос]\n"
        "• покажи последние заметки\n"
        "• заметка [id]",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_allowed(user.id):
        await update.message.reply_text("У тебя нет доступа к этому боту.")
        return

    text = update.message.text.strip()
    if not text:
        return

    # Get or create internal user record
    user_id = get_or_create_user(user.id, user.username)

    # Route intent
    intent = route(text)
    logger.info("User %s → intent: %s", user.id, intent)

    # Dispatch to skill
    response = dispatch(intent, user_id)

    await update.message.reply_text(response, parse_mode="Markdown")


# Register handlers
bot_app.add_handler(CommandHandler("start", handle_start))
bot_app.add_handler(CommandHandler("help", handle_help))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# --- Webhook endpoint ---

@fastapi_app.post("/webhook")
async def webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## File: `requirements.txt`

```
fastapi==0.115.0
uvicorn==0.30.0
python-telegram-bot==21.6
anthropic==0.40.0
python-dotenv==1.0.1
```

---

## File: `assistant.service` (systemd unit)

```ini
[Unit]
Description=Personal Assistant Telegram Bot
After=network.target

[Service]
Type=simple
User=assistant
WorkingDirectory=/opt/assistant
EnvironmentFile=/opt/assistant/.env
ExecStart=/opt/assistant/venv/bin/uvicorn main:fastapi_app --host 0.0.0.0 --port 8443
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Setup Instructions

Generate a complete `SETUP.md` with these steps:

1. Create system user: `useradd -r -s /bin/false assistant`
2. Create directory: `mkdir -p /opt/assistant/data`
3. Clone or copy project files to `/opt/assistant/`
4. Create virtualenv: `python3 -m venv /opt/assistant/venv`
5. Install deps: `venv/bin/pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and fill in values
7. Create data directory and set permissions: `chown -R assistant:assistant /opt/assistant`
8. Install systemd service: `cp assistant.service /etc/systemd/system/`
9. Enable and start: `systemctl enable --now assistant`
10. Check logs: `journalctl -u assistant -f`

**Nginx reverse proxy config** (HTTPS required for Telegram webhooks):

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:8443;
    }
}
```

---

## How to Add a New Skill

This is the key extensibility point. To add a new skill, only two files are needed:

**1. Create `skills_registry/reminders.md`:**

```markdown
# Skill: reminders

Manages time-based reminders.

## Actions

- **set**: Create a reminder.
  Params: text (str), remind_at (str, ISO datetime or natural language like "tomorrow at 10")
  Example: "напомни завтра в 10 купить молоко" → action=set, text=купить молоко, remind_at=tomorrow 10:00

- **list**: Show pending reminders.
  Params: none

- **delete**: Delete a reminder.
  Params: reminder_id (int)
```

**2. Create `skills/reminders.py`:**

```python
from skills.base import BaseSkill

class RemindersSkill(BaseSkill):
    name = "reminders"
    description = open("skills_registry/reminders.md").read()

    def execute(self, action: str, params: dict, user_id: int) -> str:
        # implement actions here
        return "Reminder skill: not yet implemented"
```

**3. Register in `dispatcher.py`:**

```python
from skills.reminders import RemindersSkill

SKILLS = {
    skill.name: skill
    for skill in [ListsSkill(), KnowledgeSkill(), RemindersSkill()]
}
```

The router will automatically pick up the new `reminders.md` on next startup and start routing messages to this skill — no changes to `router.py` needed.

---

## Important Implementation Notes

- The `skills_registry/*.md` files are loaded fresh on **each request** in `router.py`. This means you can update skill descriptions without restarting the service.
- SQLite database is at `/opt/assistant/data/assistant.db`. Back it up by copying the file: `cp /opt/assistant/data/assistant.db /backup/assistant_$(date +%Y%m%d).db`
- Access control is done via `ALLOWED_USERS` env var — comma-separated Telegram user IDs. Leave empty to allow all users.
- For Telegram webhooks, HTTPS is mandatory. Use certbot with Let's Encrypt.
- Use `claude-haiku-4-5-20251001` for routing (cheap, fast). Use `claude-sonnet-4-5-20251015` only in skills that need higher quality responses (e.g., a future `draft` skill).
- All Telegram message responses use `parse_mode="Markdown"` — make sure skill responses don't contain unescaped `*` or `_` characters in user-provided content.

---

## What to Build — Checklist

- [ ] All files listed in the project structure above
- [ ] `init_db()` creates all tables on first run
- [ ] `/start` and `/help` commands work
- [ ] Free-text messages are routed through Claude and dispatched to skills
- [ ] `lists` skill: add, show, done, delete, all_lists actions work
- [ ] `knowledge` skill: save, search, list, get actions work
- [ ] Access control via ALLOWED_USERS works
- [ ] systemd service file is included
- [ ] SETUP.md with full installation steps is included
- [ ] `.env.example` with all required variables is included