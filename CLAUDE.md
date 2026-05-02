# mirit-assistant

Personal assistant Telegram bot with Claude Code slash commands for local DB access.

## Architecture

```
main.py                   — регистрация хендлеров, запуск polling
config.py                 — env vars (TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USERS)

bot/
  handlers/               — ConversationHandlers (Telegram UI, кнопки и состояния)
    lists.py              — /lists сценарий
    knowledge.py          — /knowledge сценарий
  commands/               — бизнес-логика (чтение/запись DB)
    lists.py              — операции со списками
    knowledge.py          — операции с заметками

storage/db.py             — SQLite helpers, init_db()

.claude/skills/           — Claude Code skills (формат Agent Skills) для прямого доступа к DB
  lists/SKILL.md          — /lists
  knowledge/SKILL.md      — /knowledge
```

## Key rules

**Навигация через кнопки** — InlineKeyboardMarkup для всех меню. Пользователь вводит текст только когда бот явно спрашивает.

**ConversationHandler** — каждый раздел (`/lists`, `/knowledge`) — отдельный ConversationHandler со своими состояниями.

**API не используется** в текущих сценариях. Весь поиск и навигация — через SQLite.

## DB schema

```sql
users       — telegram_id, username
lists       — user_id, list_name, item, done
notes       — user_id, title, content, tags, created_at
```

SQLite файл: `./data/assistant.db` (volume mount в Docker).

## Adding a new flow

1. Создать `bot/commands/myflow.py` — бизнес-логика (DB операции)
2. Создать `bot/handlers/myflow.py` — ConversationHandler (Telegram UI)
3. Зарегистрировать хендлер в `main.py`
4. Если нужны новые DB-таблицы — добавить в `storage/db.py → init_db()`
5. Опционально: добавить `.claude/skills/myflow/SKILL.md` для доступа из Claude Code

## Run locally

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env  # заполнить токены
python main.py        # Telegram bot (polling)
```

## Deploy

Docker Compose на дроплете `165.232.116.241`.
CI/CD: GitHub Actions → SSH → `git pull` → `docker compose build` → `docker compose up -d`.
Secrets: `SSH_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`.

## Claude Code skills

Используй `/lists` и `/knowledge` для работы с базой данных напрямую через SQLite.
Скиллы описаны в `.claude/skills/<name>/SKILL.md` (формат Agent Skills).
Claude может вызывать их автоматически по совпадению с `description`.
