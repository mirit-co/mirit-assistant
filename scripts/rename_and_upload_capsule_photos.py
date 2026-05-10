"""
Rename capsule photos to canonical format and upload to GCS.

Format: {item_id}-{short_desc}_{user_slug}.png
- Reads inventory.json to build old->new filename mapping
- Renames files locally in data/capsula_photos/<user>/
- Uploads to GCS at 200x200
- Prints new photo_url for each item

Usage:
    python scripts/rename_and_upload_capsule_photos.py <user_slug>
"""
import io
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image
from google.cloud import storage

BUCKET_NAME = os.environ.get("GCS_BUCKET", "rstestbucketname")
THUMB_SIZE = (200, 200)
_BASE = Path(__file__).parent.parent


def resize_to_square(img: Image.Image, size: tuple) -> Image.Image:
    img.thumbnail(size, Image.LANCZOS)
    square = Image.new("RGB", size, (255, 255, 255))
    offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
    square.paste(img, offset)
    return square


def make_short_desc(item: dict) -> str:
    parts = []
    color = item.get("color_primary", "")
    if color:
        parts.append(color.replace(" ", "_").replace("/", "_"))
    subcat = item.get("subcategory", item.get("category", "item"))
    parts.append(subcat.replace(" ", "_"))
    return "_".join(parts)[:30]


def extract_original_filename(notes: str) -> str | None:
    """Extract IMG_XXXX from notes field."""
    m = re.search(r"(IMG_\d+)", notes or "")
    return m.group(1) if m else None


def main(user_slug: str):
    inventory_path = _BASE / "wardrobe" / user_slug / "inventory.json"
    photos_dir = _BASE / "data" / "capsula_photos" / user_slug

    with open(inventory_path) as f:
        inv = json.load(f)

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Build mapping: original_stem -> (item_id, new_stem)
    mapping: dict[str, tuple[str, str]] = {}
    for item in inv["items"]:
        notes = item.get("notes", "")
        orig = extract_original_filename(notes)
        if not orig:
            print(f"  SKIP {item['id']} — no IMG in notes", file=sys.stderr)
            continue
        short_desc = make_short_desc(item)
        user_lower = user_slug.lower()
        new_name = f"{item['id']}-{short_desc}_{user_lower}.png"
        if orig in mapping:
            # Multiple items share the same photo — keep first
            print(f"  NOTE: {item['id']} shares photo {orig} with {mapping[orig][0]}, skipping rename for duplicate")
            # Still update photo_url to point to the first item's renamed file
            item["photo_url"] = (
                f"https://storage.cloud.google.com/{BUCKET_NAME}/capsule/{user_slug}/{mapping[orig][1]}"
            )
            continue
        mapping[orig] = (item["id"], new_name)

    # Rename locally and upload
    updated_urls: dict[str, str] = {}  # item_id -> new photo_url

    for orig_stem, (item_id, new_name) in mapping.items():
        orig_path = photos_dir / f"{orig_stem}.png"
        if not orig_path.exists():
            # Try jpg
            orig_path_jpg = photos_dir / f"{orig_stem}.jpg"
            if orig_path_jpg.exists():
                orig_path = orig_path_jpg
            else:
                print(f"  MISSING: {orig_stem} for {item_id}", file=sys.stderr)
                continue

        new_path = photos_dir / new_name
        # Rename locally
        if orig_path != new_path:
            orig_path.rename(new_path)
            print(f"  RENAMED: {orig_path.name} -> {new_name}")

        # Upload to GCS at 200x200
        with Image.open(new_path) as img:
            img = img.convert("RGB")
            thumb = resize_to_square(img, THUMB_SIZE)

        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        buf.seek(0)

        blob_name = f"capsule/{user_slug}/{new_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(buf, content_type="image/png")

        new_url = f"https://storage.cloud.google.com/{BUCKET_NAME}/{blob_name}"
        updated_urls[item_id] = new_url
        print(f"  UPLOADED: {new_url}")

    # Update inventory.json with new photo_urls
    for item in inv["items"]:
        if item["id"] in updated_urls:
            item["photo_url"] = updated_urls[item["id"]]

    inv["updated_at"] = "2026-05-09T19:00:00Z"
    with open(inventory_path, "w") as f:
        json.dump(inv, f, ensure_ascii=False, indent=2)
    print(f"\nInventory updated: {inventory_path}")

    # Update capsule JSONs photo_urls
    capsule_dir = _BASE / "data" / "capsule" / user_slug
    for capsule_file in capsule_dir.glob("*.json"):
        with open(capsule_file) as f:
            cap = json.load(f)
        changed = False
        for anchor in cap.get("daily_anchors", []):
            for iid, old_url in list(anchor.get("photo_urls", {}).items()):
                if iid in updated_urls:
                    anchor["photo_urls"][iid] = updated_urls[iid]
                    changed = True
        if changed:
            with open(capsule_file, "w") as f:
                json.dump(cap, f, ensure_ascii=False, indent=2)
            print(f"Capsule updated: {capsule_file.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/rename_and_upload_capsule_photos.py <user_slug>")
        sys.exit(1)
    main(sys.argv[1])
