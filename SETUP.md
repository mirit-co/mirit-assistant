# Setup Guide

## Prerequisites

- Ubuntu 22.04+ droplet
- Docker + Docker Compose ([установка](https://docs.docker.com/engine/install/ubuntu/))

---

## One-time Server Setup

```bash
# 1. Clone repo
git clone https://github.com/mirit-co/mirit-assistant.git ~/assistant
cd ~/assistant

# 2. Environment
cp .env.example .env
nano .env
# Заполни: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USERS

# 3. Запустить
docker compose up -d

# 4. Проверить логи
docker compose logs -f
```

---

## Полезные команды

```bash
# Статус
docker compose ps

# Логи
docker compose logs -f

# Перезапуск
docker compose restart

# Остановить
docker compose down
```

---

## CI/CD (GitHub Actions)

Secrets в GitHub → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `SSH_HOST` | IP дроплета |
| `SSH_USERNAME` | `root` |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ |

Каждый пуш в `main`: lint → SSH на дроплет → `git pull` → `docker compose build` → `docker compose up -d`.

---

## Database Backup

```bash
cp ~/assistant/data/assistant.db ~/assistant_backup_$(date +%Y%m%d).db
```

---

## Adding a New Skill

1. Create `skills_registry/myskill.md` with actions and descriptions
2. Create `skills/myskill.py` extending `BaseSkill`
3. Register in `dispatcher.py` SKILLS dict
4. Push — CI/CD пересоберёт и перезапустит контейнер

---

## Local Development (Mac)

```bash
cd /Users/rsalakhiev/Desktop/mirit-assistant
python -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
python -c "from storage.db import init_db; init_db()"
python mcp_server.py
```
