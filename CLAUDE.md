# mirit-assistant

Personal assistant Telegram bot with Claude Code slash commands for local DB access.

## Architecture

```
main.py                   — регистрация хендлеров, запуск polling
config.py                 — env vars (TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USERS)

bot/
  handlers/               — ConversationHandlers (Telegram UI, кнопки и состояния)
    lists.py              — /lists сценарий
    docs.py               — /docs сценарий
  commands/               — бизнес-логика (чтение/запись DB)
    lists.py              — операции со списками
    docs.py               — операции с документами

storage/db.py             — SQLite helpers, init_db()

.claude/skills/           — Claude Code skills (формат Agent Skills) для прямого доступа к DB
  lists/SKILL.md          — /lists
```

## Key rules

**Навигация через кнопки** — InlineKeyboardMarkup для всех меню. Пользователь вводит текст только когда бот явно спрашивает.

**ConversationHandler** — каждый раздел (`/lists`, `/docs`) — отдельный ConversationHandler со своими состояниями.

**API не используется** в текущих сценариях. Весь поиск и навигация — через SQLite.

**Тесты обязательны** — при добавлении нового функционала всегда добавлять E2E тесты в `tests/`.

## DB schema

```sql
users       — telegram_id, username
lists       — user_id, list_name, item, done
list_meta   — user_id, list_name, is_shared
docs        — user_id, title, file_id, file_type, tags, created_at
```

SQLite файл живёт **на дроплете**: `~/assistant/data/assistant.db`.
Локальная БД не используется. Все запросы — только через SSH:

## Adding a new flow

1. Создать `bot/commands/myflow.py` — бизнес-логика (DB операции)
2. Создать `bot/handlers/myflow.py` — ConversationHandler (Telegram UI)
3. Зарегистрировать хендлер в `main.py`
4. Если нужны новые DB-таблицы — добавить в `storage/db.py → init_db()`
5. Добавить E2E тесты в `tests/test_myflow.py` (обязательно)
6. Опционально: добавить `.claude/skills/myflow/SKILL.md` для доступа из Claude Code

## Run locally

```bash
python -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env  # заполнить токены
python main.py        # Telegram bot (polling)
```

## Тестирование перед деплоем

**Любую новую фичу сначала проверяй на тестовом боте. Только если всё работает — делай git push и деплой.**

Для проверки изменений локально используется отдельный тест-бот.
Токен хранится в `.env` как `TEST_TELEGRAM_BOT_TOKEN`.
Когда он задан — `config.py` автоматически использует его вместо `TELEGRAM_BOT_TOKEN`.

```bash
# 1. Убедись, что в .env есть токен тест-бота:
#    TEST_TELEGRAM_BOT_TOKEN=токен_тест_бота

# 2. Создай и активируй venv (один раз):
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 3. Запускай тест-бота:
venv/bin/python main.py

# 4. После тестов — останови бота (обязательно перед деплоем):
pkill -f "venv/bin/python main.py"
```

Рабочий процесс: **тест-бот локально → убедился → git push → деплой на дроплет**.

## Deploy

Docker Compose на дроплете `165.232.116.241`.
CI/CD: GitHub Actions → SSH → `git pull` → `docker compose build` → `docker compose up -d`.
Secrets: `SSH_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`.

## Подключения (важно — читай перед любой операцией)

### Git push
Remote должен быть SSH, не HTTPS:
```bash
git remote set-url origin git@github.com:mirit-co/mirit-assistant.git
```
SSH-ключ для GitHub: стандартный `~/.ssh/id_rsa` или `~/.ssh/id_ed25519`.

### SSH на дроплет
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241
```

### БД — только через SSH
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT ...'"
```
Никогда не использовать `sqlite3 data/assistant.db` локально — живой базы там нет.

### Логи Docker на дроплете
`docker compose logs --tail` и `-n` не работают. Использовать:
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "cd ~/assistant && docker compose logs 2>&1 | tail -50"
```

## Claude Code skills

Используй `/lists` для работы с базой данных напрямую через SQLite.
Скиллы описаны в `.claude/skills/<name>/SKILL.md` (формат Agent Skills).
Claude может вызывать их автоматически по совпадению с `description`.
