from storage.db import get_conn


class Docs:
    def execute(self, action: str, params: dict, user_id: int):
        if action == "save":
            return self._save(user_id, params)
        elif action == "list":
            return self._list(user_id, params.get("limit", 10))
        elif action == "search":
            return self._search(user_id, params.get("query", ""))
        elif action == "get":
            return self._get(user_id, params.get("doc_id", 0))
        elif action == "delete":
            return self._delete(user_id, params.get("doc_id", 0))
        return f"Неизвестное действие: {action}"

    def _save(self, user_id: int, params: dict) -> int:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO docs (user_id, title, file_id, file_type, tags) VALUES (?, ?, ?, ?, ?)",
                (user_id, params.get("title"), params["file_id"], params["file_type"], params.get("tags", "")),
            )
            return cursor.lastrowid

    def _list(self, user_id: int, limit: int):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, created_at FROM docs "
                "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()

    def _search(self, user_id: int, query: str):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, created_at FROM docs "
                "WHERE user_id=? AND (title LIKE ? OR tags LIKE ?) "
                "ORDER BY created_at DESC LIMIT 10",
                (user_id, f"%{query}%", f"%{query}%"),
            ).fetchall()

    def _get(self, user_id: int, doc_id: int):
        with get_conn() as conn:
            return conn.execute(
                "SELECT id, title, file_id, file_type, tags, created_at FROM docs "
                "WHERE id=? AND user_id=?",
                (doc_id, user_id),
            ).fetchone()

    def _delete(self, user_id: int, doc_id: int) -> str:
        with get_conn() as conn:
            conn.execute("DELETE FROM docs WHERE id=? AND user_id=?", (doc_id, user_id))
        return "ok"
