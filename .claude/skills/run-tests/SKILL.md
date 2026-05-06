---
name: run-tests
description: Run E2E tests for the mirit-assistant Telegram bot. Use this skill whenever the user asks to run tests, check if tests pass, verify a feature works, or says things like "запускай тесты", "прогони тесты", "проверь тесты". The skill handles the full lifecycle: kill stale bot processes, start a clean bot, run pytest, kill the bot after.
allowed-tools: Bash
---

# Запуск тестов

## Когда запускать, а когда нет

**Запускай полные тесты** если изменилось что-то из:
- Логика хендлеров (`bot/handlers/`)
- Бизнес-логика команд (`bot/commands/`)
- Схема БД (`storage/db.py`)
- Навигация / кнопки / тексты в UI
- `main.py` — регистрация хендлеров

**Можно пропустить тесты** если изменилось только:
- Переменные окружения / секреты (`.env`, токены, ключи API)
- Конфигурация деплоя (`Dockerfile`, `docker-compose.yml`, GitHub Actions)
- Документация (`CLAUDE.md`, `README`, скиллы)
- `config.py` без изменений логики (только новая переменная)
- Зависимости (`requirements.txt`) без смены мажорных версий

---

Тесты E2E работают против живого Telegram-бота. Бот должен быть запущен **ровно одним процессом** перед запуском pytest. Накопление процессов — главая причина сбоев (409 Conflict от Telegram).

## Полный порядок действий

### Шаг 1 — Найди и убей все процессы бота

Telegram возвращает `409 Conflict` если несколько процессов одновременно используют один токен. Это происходит в двух случаях:
- Накопились процессы бота с прошлых сессий (ищи **по рабочей директории**)
- Ты уже запускал тест-бота в этой сессии и не убил его (проверяй `$BOT_PID`)

**Тест-бот (`TEST_TELEGRAM_BOT_TOKEN`) и продакшн бот (`TELEGRAM_BOT_TOKEN`) — разные токены.** Продакшн бот работает на дроплете и никогда не мешает тестам. 409 от тест-бота означает только локальный конфликт.

```bash
# Найти все python-процессы и их рабочие директории
ps aux | grep python | grep -v grep | awk '{print $2}' | while read pid; do
  dir=$(lsof -p $pid -a -d cwd 2>/dev/null | awk 'NR==2{print $9}')
  echo "$pid: $dir"
done
```

Убить все процессы, у которых рабочая директория совпадает с `/Users/rsalakhiev/Desktop/mirit-assistant`:

```bash
kill <PID1> <PID2> ... 2>/dev/null
sleep 5  # дать Telegram освободить сессию
```

### Шаг 2 — Запусти бота

```bash
cd /Users/rsalakhiev/Desktop/mirit-assistant
venv/bin/python main.py > /tmp/bot.log 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID"
```

Подожди чистого старта (убедись что нет 409):

```bash
sleep 5
grep -E "Application started|409 Conflict" /tmp/bot.log | tail -5
```

Если видишь `409 Conflict` — значит ещё остались процессы. Повтори шаг 1 с более долгой паузой (`sleep 8`).

### Шаг 3 — Запусти тесты

```bash
cd /Users/rsalakhiev/Desktop/mirit-assistant
venv/bin/pytest tests/ -v 2>&1
```

Для конкретного файла:

```bash
venv/bin/pytest tests/test_docs.py -v 2>&1
venv/bin/pytest tests/test_smoke.py -v 2>&1
```

### Шаг 4 — ОБЯЗАТЕЛЬНО убей бота после тестов

**Это критично.** Каждый незакрытый процесс будет вызывать 409 в следующей сессии.

```bash
kill $BOT_PID 2>/dev/null
echo "Bot stopped"
```

Если `$BOT_PID` не сохранился — найди и убей по директории (см. шаг 1).

---

## Диагностика

**409 Conflict в логах бота** → запущено несколько процессов. Найди все через `lsof` по рабочей директории.

**TimeoutError в тестах** → бот не успел ответить. Проверь `/tmp/bot.log` — нет ли краша.

**`assert row` — пользователь не создан в DB** → бот не получил `/lists` команду. Убедись что тест-бот доступен (правильный `TEST_TELEGRAM_BOT_TOKEN` в `.env`).
