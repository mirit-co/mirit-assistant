"""
Upload new capsule photos to GCS with 100x100 resize.

Usage:
    python scripts/upload_capsule_photos.py <user_slug>

Example:
    python scripts/upload_capsule_photos.py Mariana

Reads PNG/JPG files from data/capsula_photos/<user_slug>/,
resizes each to fit within 100x100 (keeping aspect ratio, white-padded to square),
and uploads to GCS bucket at capsule/<user_slug>/<filename>.

Requires:
    - GCS_BUCKET env var (or defaults to rstestbucketname)
    - GOOGLE_APPLICATION_CREDENTIALS env var pointing to service account JSON
    - pip install Pillow google-cloud-storage
"""
import io
import os
import sys
from pathlib import Path

from PIL import Image
from google.cloud import storage

BUCKET_NAME = os.environ.get("GCS_BUCKET", "rstestbucketname")
THUMB_SIZE = (200, 200)
_BASE = Path(__file__).parent.parent


def resize_to_square(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img.thumbnail(size, Image.LANCZOS)
    square = Image.new("RGB", size, (255, 255, 255))
    offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
    square.paste(img, offset)
    return square


def upload_photos(user_slug: str) -> None:
    photos_dir = _BASE / "data" / "capsula_photos" / user_slug
    if not photos_dir.exists():
        print(f"Directory not found: {photos_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(photos_dir.glob("*.png")) + sorted(photos_dir.glob("*.jpg")) + sorted(photos_dir.glob("*.jpeg"))
    if not files:
        print(f"No image files found in {photos_dir}", file=sys.stderr)
        sys.exit(1)

    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    for filepath in files:
        with Image.open(filepath) as img:
            img = img.convert("RGB")
            thumb = resize_to_square(img, THUMB_SIZE)

        buf = io.BytesIO()
        thumb.save(buf, format="PNG", optimize=True)
        buf.seek(0)

        blob_name = f"capsule/{user_slug}/{filepath.name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_file(buf, content_type="image/png")

        print(f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/upload_capsule_photos.py <user_slug>", file=sys.stderr)
        sys.exit(1)
    upload_photos(sys.argv[1])
