import json
from pathlib import Path

from storage.db import get_conn

_BASE = Path(__file__).parent.parent.parent


def _user_slug(telegram_id: int) -> str:
    from config import RUSLAN_TELEGRAM_IDS, MARIANA_TELEGRAM_IDS
    if telegram_id and telegram_id in RUSLAN_TELEGRAM_IDS:
        return "Ruslan"
    if telegram_id and telegram_id in MARIANA_TELEGRAM_IDS:
        return "Mariana"
    return str(telegram_id)


def _capsule_dir(telegram_id: int) -> Path:
    return _BASE / "data" / "capsule" / _user_slug(telegram_id)


def _inventory_path(telegram_id: int) -> Path:
    return _BASE / "wardrobe" / _user_slug(telegram_id) / "inventory.json"


# Subcategory → Russian noun
SUBCAT_MAP: dict = {
    # tops
    "polo": "поло", "tee": "футболка", "longsleeve": "лонгслив",
    "button_down": "рубашка", "shirt": "рубашка", "blouse": "блуза",
    "top": "топ", "tank": "топ", "sweater": "свитер", "sweatshirt": "свитшот",
    # layers
    "hoodie": "худи", "zip_hoodie": "худи", "light_jacket": "худи",
    "vest_boho": "жилет", "vest_suit": "жилет", "vest_quilted": "стёганый жилет",
    "vest_knit": "вязаный жилет", "vest_button": "жилет",
    "cardigan": "кардиган", "vest": "жилет",
    # bottoms
    "jeans_straight": "джинсы", "jeans_relaxed": "джинсы", "jeans_slim": "джинсы",
    "jeans": "джинсы", "chinos": "чинос", "shorts": "шорты",
    "trousers": "брюки", "skirt": "юбка",
    # dresses
    "maxi_dress": "платье", "midi_dress": "платье", "mini_dress": "платье",
    "dress": "платье", "set": "комплект",
    # outerwear
    "kimono": "кимоно", "jacket": "куртка", "shirt_jacket": "рубашка-жакет",
    "blazer": "блейзер", "vest_puffer": "пуховый жилет", "fleece_jacket": "флисовая куртка",
    # shoes
    "sneakers": "кеды", "flats": "балетки", "sandals": "сандалии",
    "mules": "мюли", "clogs": "сабо", "hiking_boots": "ботинки", "boots": "ботинки",
    # accessories
    "bag_crossbody": "сумка", "bag_tote": "сумка", "bag_shoulder": "сумка",
    "bag_crochet": "вязаная сумка", "bag_mini": "мини-сумка",
    "bag_belt": "поясная сумка", "bag_net": "сетчатая сумка",
    "scarf": "шарф", "scarf_twilly": "твилли", "belt": "ремень",
    "cap": "кепка", "hat_straw": "шляпа",
}

DAY_MAP = {
    "Mon": "Понедельник",
    "Tue": "Вторник",
    "Wed": "Среда",
    "Thu": "Четверг",
    "Fri": "Пятница",
    "Sat": "Суббота",
    "Sun": "Воскресенье",
    "Пн": "Понедельник",
    "Вт": "Вторник",
    "Ср": "Среда",
    "Чт": "Четверг",
    "Пт": "Пятница",
    "Сб": "Суббота",
    "Вс": "Воскресенье",
}

_MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

_PRECIP_EMOJI = {
    "none":                "☀️",
    "trace":               "🌤",
    "possible_light_rain": "🌦",
    "light_rain":          "🌧",
    "slight_rain":         "🌦",
    "rain":                "🌧",
    "heavy_rain":          "⛈",
    "thunderstorm":        "⛈",
    "cloudy":              "☁️",
    "partly_cloudy":       "⛅",
    "snow":                "❄️",
    "fog":                 "🌫",
}


def _date_str(date_iso: str) -> str:
    try:
        parts = date_iso.split("-")
        day, month = int(parts[2]), int(parts[1])
        return f"{day} {_MONTHS_RU[month]}"
    except Exception:
        return date_iso


def capsule_date_range(capsule: dict) -> str:
    # New format: week_label field
    if capsule.get("week_label"):
        return capsule["week_label"]
    # Old format: weather_summary list
    weather = capsule.get("weather_summary", [])
    if not weather:
        return ""
    try:
        d1 = weather[0]["date"].split("-")
        d2 = weather[-1]["date"].split("-")
        if d1[1] == d2[1]:
            return f"{int(d1[2])}–{int(d2[2])} {_MONTHS_RU[int(d1[1])]}"
    except Exception:
        pass
    return f"{_date_str(weather[0]['date'])} – {_date_str(weather[-1]['date'])}"


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
    noun = SUBCAT_MAP.get(subcat_key, subcat_key)
    color = color_key.replace("_", " ").capitalize() if color_key else ""
    return f"{color} {noun}".strip()


def get_pool_items(capsule: dict, inventory: dict) -> list:
    pool = capsule.get("pool", [])
    # New format: pool is a dict with category keys containing lists of {id, label, photo_url}
    if isinstance(pool, dict):
        ids = []
        for category_items in pool.values():
            for entry in category_items:
                ids.append(entry["id"])
        pool = ids
    result = []
    for item_id in pool:
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

    ws = capsule.get("weather_summary", [])
    weather_by_day = {w["day"]: w for w in ws} if isinstance(ws, list) else {}

    for anchor in capsule.get("daily_anchors", []):
        day_key = anchor.get("day", "")
        day_ru = DAY_MAP.get(day_key, day_key)

        # New format: weather and date embedded in anchor
        if "weather" in anchor and "date" in anchor:
            date_label = anchor["date"]
            temp_str = anchor["weather"]
        else:
            # Old format: separate weather_summary list
            weather = weather_by_day.get(day_key, {})
            date_label = _date_str(weather.get("date", "")) if weather.get("date") else ""
            precip = weather.get("precip", "none")
            emoji = _PRECIP_EMOJI.get(precip, "☀️")
            high = weather.get("high_c", "")
            temp_str = f"{emoji} {high}°C" if high != "" else anchor.get("temp", "")

        photo_urls = anchor.get("photo_urls", {})

        def _render_items(ids: list) -> str:
            parts = []
            for iid in ids:
                inv = inventory.get(iid)
                lbl = item_label(inv) if inv else iid
                url = photo_urls.get(iid) or (inv.get("photo_url") if inv else None)
                parts.append(f'<a href="{url}">{lbl}</a>' if url else lbl)
            return " · ".join(parts)

        caption = anchor.get("caption") or anchor.get("rationale", "")
        header = f"<b>{day_ru}, {date_label}</b> — {temp_str}" if date_label else f"<b>{day_ru}</b> — {temp_str}"
        lines.append(header)

        morning = anchor.get("morning")
        afternoon = anchor.get("afternoon")
        if morning and afternoon:
            m_items = morning.get("items", [])
            a_items = afternoon.get("items", [])
            if m_items == a_items:
                lines.append(_render_items(m_items))
            else:
                m_lbl = morning.get("temp_label", "🌅 утро")
                a_lbl = afternoon.get("temp_label", "☀️ день")
                lines.append(f"{m_lbl}: {_render_items(m_items)}")
                lines.append(f"{a_lbl}: {_render_items(a_items)}")
        else:
            lines.append(_render_items(anchor.get("items", [])))

        if caption:
            lines.append(f"<i>{caption}</i>")
        editor_note = anchor.get("editor_note")
        if editor_note:
            lines.append(f"💋 <i>{editor_note}</i>")
        lines.append("")

    return "\n".join(lines).strip()
