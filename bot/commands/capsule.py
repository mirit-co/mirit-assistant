import json
from pathlib import Path

from storage.db import get_conn

_BASE = Path(__file__).parent.parent.parent


def _user_slug(telegram_id: int) -> str:
    from config import RUSLAN_TELEGRAM_ID, MARIANA_TELEGRAM_ID
    if telegram_id and telegram_id == RUSLAN_TELEGRAM_ID:
        return "Ruslan"
    if telegram_id and telegram_id == MARIANA_TELEGRAM_ID:
        return "Mariana"
    return str(telegram_id)


def _capsule_dir(telegram_id: int) -> Path:
    return _BASE / "data" / "capsule" / _user_slug(telegram_id)


def _inventory_path(telegram_id: int) -> Path:
    return _BASE / "wardrobe" / _user_slug(telegram_id) / "inventory.json"

# Colors: (neut, fem, masc, plur). "n" for indeclinable (Navy).
_COLORS: dict = {
    "mint":         ("Мятное",      "Мятная",       "Мятный",       "Мятные"),
    "navy":         ("Navy",        "Navy",          "Navy",         "Navy"),
    "olive":        ("Оливковое",   "Оливковая",    "Оливковый",    "Оливковые"),
    "black":        ("Чёрное",      "Чёрная",       "Чёрный",       "Чёрные"),
    "beige":        ("Бежевое",     "Бежевая",      "Бежевый",      "Бежевые"),
    "mid_grey":     ("Серое",       "Серая",        "Серый",        "Серые"),
    "grey":         ("Серое",       "Серая",        "Серый",        "Серые"),
    "light_blue":   ("Голубое",     "Голубая",      "Голубой",      "Голубые"),
    "dark_grey":    ("Тёмно-серое", "Тёмно-серая",  "Тёмно-серый",  "Тёмно-серые"),
    "white":        ("Белое",       "Белая",        "Белый",        "Белые"),
    "burgundy":     ("Бордовое",    "Бордовая",     "Бордовый",     "Бордовые"),
    "charcoal":     ("Графитовое",  "Графитовая",   "Графитовый",   "Графитовые"),
    "forest_green": ("Тёмно-зелёное","Тёмно-зелёная","Тёмно-зелёный","Тёмно-зелёные"),
    "blue":         ("Синее",       "Синяя",        "Синий",        "Синие"),
    "green":        ("Зелёное",     "Зелёная",      "Зелёный",      "Зелёные"),
    "red":          ("Красное",     "Красная",      "Красный",      "Красные"),
    "brown":        ("Коричневое",  "Коричневая",   "Коричневый",   "Коричневые"),
    "denim_dark":   ("Тёмное",      "Тёмная",       "Тёмный",       "Тёмные"),
    "denim":        ("Синее",       "Синяя",        "Синий",        "Синие"),
    "cream":        ("Кремовое",    "Кремовая",     "Кремовый",     "Кремовые"),
}

# Subcategory: (Russian noun, grammatical gender: n/f/m/pl)
SUBCAT_MAP: dict = {
    "polo":           ("поло",           "n"),
    "tee":            ("футболка",       "f"),
    "button_down":    ("рубашка",        "f"),
    "shirt":          ("рубашка",        "f"),
    "sweatshirt":     ("свитшот",        "m"),
    "hoodie":         ("худи",           "n"),
    "zip_hoodie":     ("худи на молнии", "n"),
    "light_jacket":   ("худи",           "n"),
    "jeans_straight": ("джинсы",         "pl"),
    "jeans_relaxed":  ("джинсы",         "pl"),
    "jeans_slim":     ("джинсы",         "pl"),
    "jeans":          ("джинсы",         "pl"),
    "chinos":         ("чинос",          "pl"),
    "shorts":         ("шорты",          "pl"),
    "kimono":         ("кимоно",         "n"),
    "jacket":         ("куртка",         "f"),
    "blazer":         ("блейзер",        "m"),
    "cardigan":       ("кардиган",       "m"),
    "vest":           ("жилет",          "m"),
    "tank":           ("майка",          "f"),
}

_GENDER_IDX = {"n": 0, "f": 1, "m": 2, "pl": 3}

DAY_MAP = {
    "Mon": "Понедельник",
    "Tue": "Вторник",
    "Wed": "Среда",
    "Thu": "Четверг",
    "Fri": "Пятница",
    "Sat": "Суббота",
    "Sun": "Воскресенье",
}

_MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

_PRECIP_EMOJI = {
    "none": "☀️",
    "possible_light_rain": "🌦",
    "light_rain": "🌧",
    "rain": "🌧",
    "heavy_rain": "⛈",
    "cloudy": "☁️",
    "partly_cloudy": "⛅",
    "snow": "❄️",
    "fog": "🌫",
}


def _date_str(date_iso: str) -> str:
    """'2026-05-05' → '5 мая'"""
    try:
        parts = date_iso.split("-")
        day, month = int(parts[2]), int(parts[1])
        return f"{day} {_MONTHS_RU[month]}"
    except Exception:
        return date_iso


def capsule_date_range(capsule: dict) -> str:
    """Returns '5–11 мая' from weather_summary dates."""
    weather = capsule.get("weather_summary", [])
    if not weather:
        return ""
    first = _date_str(weather[0]["date"])
    last = _date_str(weather[-1]["date"])
    # If same month, compress: '5–11 мая'
    try:
        d1 = weather[0]["date"].split("-")
        d2 = weather[-1]["date"].split("-")
        if d1[1] == d2[1]:
            return f"{int(d1[2])}–{int(d2[2])} {_MONTHS_RU[int(d1[1])]}"
    except Exception:
        pass
    return f"{first} – {last}"


def load_current_capsule(telegram_id: int) -> dict | None:
    d = _capsule_dir(telegram_id)
    files = sorted(d.glob("*.json"), reverse=True)
    if not files:
        return None
    return json.loads(files[0].read_text(encoding="utf-8"))


def load_inventory(telegram_id: int) -> dict:
    path = _inventory_path(telegram_id)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data.get("items", [])}


def item_label(item: dict) -> str:
    subcat_key = item.get("subcategory", "")
    color_key = item.get("color_primary", "")
    subcat_entry = SUBCAT_MAP.get(subcat_key)
    if subcat_entry:
        noun, gender = subcat_entry
        color_forms = _COLORS.get(color_key)
        color = color_forms[_GENDER_IDX[gender]] if color_forms else color_key
    else:
        noun = subcat_key
        color = _COLORS.get(color_key, (color_key,))[0]
    return f"{color} {noun}".strip()


def get_pool_items(capsule: dict, inventory: dict) -> list:
    result = []
    for item_id in capsule.get("pool", []):
        inv_item = inventory.get(item_id)
        label = item_label(inv_item) if inv_item else item_id
        photo_url = inv_item.get("photo_url") if inv_item else None
        result.append((item_id, label, photo_url))
    return result


def get_checklist_state(user_id: int, week: str, pool_items: list) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT item_id, done FROM capsule_checklist WHERE user_id=? AND week=?",
            (user_id, week),
        ).fetchall()
    done_map = {row["item_id"]: bool(row["done"]) for row in rows}
    return [
        (item_id, label, done_map.get(item_id, False), photo_url)
        for item_id, label, photo_url in pool_items
    ]


def toggle_checklist_item(user_id: int, week: str, item_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO capsule_checklist (user_id, week, item_id, done) VALUES (?, ?, ?, 1)"
            " ON CONFLICT(user_id, week, item_id) DO UPDATE SET done = 1 - done",
            (user_id, week, item_id),
        )


def reset_checklist(user_id: int, week: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE capsule_checklist SET done=0 WHERE user_id=? AND week=?",
            (user_id, week),
        )


def format_weekly_overview(capsule: dict, inventory: dict) -> str:
    lines = []

    weather_by_day = {w["day"]: w for w in capsule.get("weather_summary", [])}

    for anchor in capsule.get("daily_anchors", []):
        day_key = anchor["day"]
        day_ru = DAY_MAP.get(day_key, day_key)
        weather = weather_by_day.get(day_key, {})
        date_label = _date_str(weather.get("date", "")) if weather.get("date") else ""
        precip = weather.get("precip", "none")
        emoji = _PRECIP_EMOJI.get(precip, "☀️")
        high = weather.get("high_c", "")
        temp_str = f"{emoji} {high}°C" if high != "" else anchor.get("temp", "")

        item_labels = []
        for iid in anchor.get("items", []):
            inv = inventory.get(iid)
            lbl = item_label(inv) if inv else iid
            url = inv.get("photo_url") if inv else None
            item_labels.append(f'<a href="{url}">{lbl}</a>' if url else lbl)
        caption = anchor.get("caption") or anchor.get("rationale", "")

        header = f"<b>{day_ru}, {date_label}</b> — {temp_str}" if date_label else f"<b>{day_ru}</b> — {temp_str}"
        lines.append(header)
        lines.append(" · ".join(item_labels))
        if caption:
            lines.append(f"<i>{caption}</i>")
        lines.append("")

    return "\n".join(lines).strip()
