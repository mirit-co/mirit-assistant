# Setup Guide

## Prerequisites

- Ubuntu 22.04+ droplet
- Python 3.11+

---

## One-time Server Setup

```bash
# 1. Clone repo
git clone https://github.com/mirit-co/mirit-assistant.git ~/assistant

# 2. Virtualenv
python3 -m venv ~/assistant/venv
~/assistant/venv/bin/pip install -r ~/assistant/requirements.txt

# 3. Environment
cp ~/assistant/.env.example ~/assistant/.env
nano ~/assistant/.env
# Заполни: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ALLOWED_USERS

# 4. systemd service
cp ~/assistant/assistant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now assistant

# 5. Проверить логи
journalctl -u assistant -f
```

---

## CI/CD (GitHub Actions)

Secrets в GitHub → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `SSH_HOST` | IP дроплета |
| `SSH_USERNAME` | `root` |
| `SSH_PRIVATE_KEY` | Приватный SSH-ключ |

Каждый пуш в `main`: lint → SSH на дроплет → `git pull` → `pip install` → `systemctl restart assistant`.

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
4. Push — router picks up the new `.md` automatically on next request

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

The MCP server is auto-registered in `.claude/settings.json` — restart Claude Code to pick it up.
