# mirit-assistant

Personal assistant Telegram bot with Claude Code MCP interface.

## Architecture

```
main.py              — регистрация хендлеров, запуск polling
config.py            — env vars (TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USERS)
router.py            — вызов Claude API для смыслового поиска
dispatcher.py        — маппинг skill → класс (используется из MCP)

handlers/
  lists.py           — ConversationHandler для /lists (без API)
  knowledge.py       — ConversationHandler для /knowledge (API только в поиске)

skills/
  lists.py           — бизнес-логика списков (read/write DB)
  knowledge.py       — бизнес-логика базы знаний (read/write DB)

storage/db.py        — SQLite helpers, init_db()
skills_registry/     — .md-описания навыков для роутера
mcp_server.py        — MCP-сервер для Claude Code (те же навыки как tools)
```

## Key rules

**API вызывается только явно** — не на каждое сообщение. Свободный текст обрабатывается только когда пользователь находится в конкретном состоянии сценария (например, шаг "Найти" в /knowledge). Случайные сообщения вне сценария игнорируются.

**Навигация через кнопки** — InlineKeyboardMarkup для всех меню. Пользователь вводит текст только когда бот явно спрашивает.

**ConversationHandler** — каждый раздел (`/lists`, `/knowledge`) — отдельный ConversationHandler со своими состояниями. Состояния изолированы между разделами.

## DB schema

```sql
users       — telegram_id, username
lists       — user_id, list_name, item, done
notes       — user_id, title, content, tags, created_at
```

SQLite файл: `./data/assistant.db` (volume mount в Docker).

## Adding a new flow

1. Создать `handlers/myflow.py` с `ConversationHandler`
2. Описать состояния (целые числа) и переходы между ними
3. API вызывать только в состояниях, где нужен смысловой поиск
4. Зарегистрировать в `main.py`
5. Если нужны новые DB-таблицы — добавить в `storage/db.py → init_db()`
6. Если нужен новый skill для MCP — добавить в `skills/` и `dispatcher.py`

Схема всех сценариев и правила включения API: `FLOWS.md`

## Run locally

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env  # заполнить токены
python main.py        # Telegram bot (polling)
python mcp_server.py  # MCP tools для Claude Code
```

## Deploy

Docker Compose на дроплете `165.232.116.241`.
CI/CD: GitHub Actions → SSH → `git pull` → `docker compose build` → `docker compose up -d`.
Secrets: `SSH_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`.

## MCP tools (Claude Code)

`list_add`, `list_show`, `list_all`, `list_done`, `list_delete`,
`knowledge_save`, `knowledge_search`, `knowledge_list`, `knowledge_get`
