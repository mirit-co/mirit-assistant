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

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "assistant.db"))
SKILLS_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "skills_registry")
