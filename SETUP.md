# Setup Guide

## Prerequisites

- Ubuntu 22.04+ droplet
- Domain pointed at the droplet (for Telegram webhook HTTPS)
- Python 3.11+
- Nginx + Certbot

---

## One-time Server Setup

```bash
# 1. System user
useradd -r -s /bin/false assistant

# 2. Project directory
mkdir -p /opt/assistant/data

# 3. Clone repo
git clone https://github.com/YOUR_USERNAME/mirit-assistant.git /opt/assistant

# 4. Virtualenv
python3 -m venv /opt/assistant/venv
/opt/assistant/venv/bin/pip install -r /opt/assistant/requirements.txt

# 5. Environment
cp /opt/assistant/.env.example /opt/assistant/.env
# Edit .env with your actual values:
# TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, WEBHOOK_URL, WEBHOOK_SECRET, ALLOWED_USERS

# 6. Permissions
chown -R assistant:assistant /opt/assistant

# 7. systemd service
cp /opt/assistant/assistant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now assistant

# 8. Check logs
journalctl -u assistant -f
```

---

## Nginx Reverse Proxy

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

Get SSL cert:
```bash
certbot --nginx -d your-domain.com
```

---

## CI/CD (GitHub Actions)

Set these secrets in GitHub → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `SSH_HOST` | Droplet IP or hostname |
| `SSH_USERNAME` | SSH user (e.g. `root`) |
| `SSH_PRIVATE_KEY` | Private SSH key (server must have matching public key in `~/.ssh/authorized_keys`) |

Every push to `main` will:
1. Run `ruff check` linter
2. SSH into the droplet, `git pull`, reinstall deps, restart service

---

## Database Backup

```bash
cp /opt/assistant/data/assistant.db /backup/assistant_$(date +%Y%m%d).db
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

# Copy and fill env
cp .env.example .env

# Init DB
python -c "from storage.db import init_db; init_db()"

# Start MCP server (for Claude Code tools)
python mcp_server.py
```

The MCP server is auto-registered in `.claude/settings.json` — restart Claude Code to pick it up.
