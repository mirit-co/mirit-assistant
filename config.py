import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TEST_TELEGRAM_BOT_TOKEN") or os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ALLOWED_USERS = [
    int(uid.strip())
    for uid in os.environ.get("ALLOWED_USERS", "").split(",")
    if uid.strip()
]

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "assistant.db"))
