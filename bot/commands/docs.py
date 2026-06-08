from storage.db import get_conn

# Canonical tags shown on the first screen, in display order.
TAGS = ["Руслан", "Марьяна", "Антон", "Авто"]

# Aliases → canonical tag, used for auto-tagging by document title/caption.
_TAG_ALIASES = {
    "руслан": "Руслан",
    "марьяна": "Марьяна",
    "мариана": "Марьяна",
    "марианна": "Марьяна",
    "антон": "Антон",
    "авто": "Авто",
}


def normalize_tags(raw: str) -> list[str]:
    """Split a stored tags string into a clean ordered list of canonical tags."""
    if not raw:
        return []
    seen = []
    for part in raw.split(","):
        t = part.strip()
        if not t:
            continue
        canon = _TAG_ALIASES.get(t.lower(), t)
        if canon not in seen:
            seen.append(canon)
    return seen


def auto_tags_from_title(title: str) -> list[str]:
    """Guess tags from a document title/caption by matching known aliases."""
    if not title:
        return []
    low = title.lower()
    found = []
    for alias, canon in _TAG_ALIASES.items():
        if alias in low and canon not in found:
            found.append(canon)
    # preserve canonical display order
    return [t for t in TAGS if t in found]


class Docs:
    def execute(self, action: str, params: dict, user_id: int):
        if action == "save":
            return self._save(user_id, params)
        elif action == "list":
            return self._list(params.get("limit", 10), params.get("offset", 0))
        elif action == "count":
            return self._count()
        elif action == "search":
            return self._search(params.get("query", ""))
        elif action == "get":
            return self._get(params.get("doc_id", 0))
        elif action == "by_tag":
            return self._by_tag(params.get("tag", ""))
        elif action == "tag_counts":
            return self._tag_counts()
        elif action == "set_tags":
            return self._set_tags(params.get("doc_id", 0), params.get("tags", ""))
        elif action == "delete":
            return self._delete(params.get("doc_id", 0))
        return f"Неизвестное действие: {action}"

    # --- writes ---

    def _save(self, user_id: int, params: dict) -> int:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO docs (user_id, title, file_id, file_type, tags) VALUES (?, ?, ?, ?, ?)",
                (user_id, params.get("title"), params["file_id"], params["file_type"], params.get("tags", "")),
            )
            return cursor.lastrowid

    def _set_tags(self, doc_id: int, tags: str) -> str:
        with get_conn() as conn:
            conn.execute("UPDATE docs SET tags=? WHERE id=?", (tags, doc_id))
        return "ok"

    def _delete(self, doc_id: int) -> str:
        with get_conn() as conn:
            conn.execute("DELETE FROM docs WHERE id=?", (doc_id,))
        return "ok"

    # --- reads (shared pool — not scoped by user_id) ---

    def _list(self, limit: int, offset: int = 0):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, tags, created_at FROM docs "
                "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

    def _count(self) -> int:
        with get_conn() as conn:
            return conn.execute("SELECT COUNT(*) AS c FROM docs").fetchone()["c"]

    def _search(self, query: str):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, tags, created_at FROM docs "
                "WHERE title LIKE ? OR tags LIKE ? "
                "ORDER BY created_at DESC, id DESC LIMIT 20",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()

    def _get(self, doc_id: int):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, tags, created_at FROM docs WHERE id=?",
                (doc_id,),
            ).fetchone()

    def _by_tag(self, tag: str):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, file_id, file_type, tags, created_at FROM docs "
                "WHERE tags LIKE ? ORDER BY created_at DESC, id DESC",
                (f"%{tag}%",),
            ).fetchall()
        # LIKE may over-match (e.g. substring); confirm via normalized tag list
        return [r for r in rows if tag in normalize_tags(r["tags"])]

    def _tag_counts(self) -> dict:
        """Return {tag: count} for canonical tags that have ≥1 document."""
        with get_conn() as conn:
            rows = conn.execute("SELECT tags FROM docs").fetchall()
        counts = {t: 0 for t in TAGS}
        for r in rows:
            for t in normalize_tags(r["tags"]):
                if t in counts:
                    counts[t] += 1
        return {t: c for t, c in counts.items() if c > 0}
