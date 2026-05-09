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

def _parse_ids(env_key: str) -> list[int]:
    return [
        int(v.strip()) for v in os.environ.get(env_key, "").split(",")
        if v.strip().isdigit()
    ]


RUSLAN_TELEGRAM_IDS = _parse_ids("RUSLAN_TELEGRAM_ID")
MARIANA_TELEGRAM_IDS = _parse_ids("MARIANA_TELEGRAM_ID")
RUSLAN_TELEGRAM_ID = RUSLAN_TELEGRAM_IDS[0] if RUSLAN_TELEGRAM_IDS else 0
MARIANA_TELEGRAM_ID = MARIANA_TELEGRAM_IDS[0] if MARIANA_TELEGRAM_IDS else 0
