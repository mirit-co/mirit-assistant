"""
Validate inventory.json photo_id consistency.

Checks:
- photo_id field exists and non-empty for every item
- photo_url matches expected URL built from photo_id
- Warns if two items share same photo_id (shared photo — valid but logged)

Usage:
    python scripts/validate_inventory_photos.py [Mariana|Ruslan|all]
    Exits 0 if no ERRORs, 1 otherwise.
"""
import json
import sys
from pathlib import Path

BUCKET = "rstestbucketname"
_BASE = Path(__file__).parent.parent


def validate_user(user_slug: str) -> int:
    inventory_path = _BASE / "wardrobe" / user_slug / "inventory.json"
    if not inventory_path.exists():
        print(f"[{user_slug}] MISSING inventory.json")
        return 1

    with open(inventory_path) as f:
        data = json.load(f)

    errors = 0
    photo_id_map: dict[str, list[str]] = {}

    for item in data.get("items", []):
        iid = item["id"]
        photo_id = item.get("photo_id", "")
        photo_url = item.get("photo_url", "")

        if not photo_id:
            print(f"[{user_slug}] ERROR {iid}: missing photo_id")
            errors += 1
            continue

        expected_url = (
            f"https://storage.cloud.google.com/{BUCKET}/capsule/{user_slug}/{photo_id}.png"
        )
        if photo_url != expected_url:
            print(
                f"[{user_slug}] ERROR {iid}: photo_url mismatch\n"
                f"  expected: {expected_url}\n"
                f"  got:      {photo_url}"
            )
            errors += 1

        photo_id_map.setdefault(photo_id, []).append(iid)

    for pid, iids in photo_id_map.items():
        if len(iids) > 1:
            print(f"[{user_slug}] WARN  shared photo_id {pid}: {iids}")

    ok = len(data.get("items", [])) - errors
    print(f"[{user_slug}] {ok} OK, {errors} ERROR(s), {len(data.get('items', []))} total")
    return errors


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    users = ["Mariana", "Ruslan"] if target == "all" else [target]

    total_errors = 0
    for user in users:
        total_errors += validate_user(user)

    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
