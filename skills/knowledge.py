import os

from skills.base import BaseSkill
from storage.db import get_conn

_registry_path = os.path.join(os.path.dirname(__file__), "..", "skills_registry", "knowledge.md")


class KnowledgeSkill(BaseSkill):
    name = "knowledge"
    description = open(_registry_path).read()

    def execute(self, action: str, params: dict, user_id: int) -> str:
        if action == "save":
            return self._save(user_id, params)
        elif action == "search":
            return self._search(user_id, params.get("query", ""))
        elif action == "list":
            return self._list(user_id, params.get("limit", 10))
        elif action == "get":
            return self._get(user_id, params.get("note_id"))
        else:
            return f"Неизвестное действие: {action}"

    def _save(self, user_id: int, params: dict) -> str:
        content = params.get("content", "")
        if not content:
            return "Нет содержимого для сохранения."
        title = params.get("title", "")
        tags = params.get("tags", "")
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (user_id, title, content, tags) VALUES (?, ?, ?, ?)",
                (user_id, title, content, tags),
            )
            note_id = cursor.lastrowid
        title_display = f"«{title}»" if title else f"#note{note_id}"
        return f"💾 Сохранил заметку {title_display} (id: {note_id})"

    def _search(self, user_id: int, query: str) -> str:
        if not query:
            return "Укажи запрос для поиска."
        with get_conn() as conn:
            rows = conn.execute(
                """SELECT id, title, content, created_at FROM notes
                   WHERE user_id=? AND (content LIKE ? OR title LIKE ? OR tags LIKE ?)
                   ORDER BY created_at DESC LIMIT 5""",
                (user_id, f"%{query}%", f"%{query}%", f"%{query}%"),
            ).fetchall()
        if not rows:
            return f"Ничего не нашёл по запросу «{query}»."
        lines = []
        for row in rows:
            title = row["title"] or f"note #{row['id']}"
            date = row["created_at"][:10]
            preview = row["content"][:80].replace("\n", " ")
            lines.append(f"[{row['id']}] *{title}* ({date})\n    {preview}…")
        return f"🔍 Найдено {len(rows)} заметок:\n\n" + "\n\n".join(lines)

    def _list(self, user_id: int, limit: int) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at FROM notes WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        if not rows:
            return "База знаний пуста. Сохрани первую заметку!"
        lines = [
            f"[{r['id']}] {r['title'] or 'без названия'} — {r['created_at'][:10]}"
            for r in rows
        ]
        return f"📝 Последние заметки ({len(rows)}):\n" + "\n".join(lines)

    def _get(self, user_id: int, note_id) -> str:
        if not note_id:
            return "Укажи id заметки."
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id=? AND user_id=?", (note_id, user_id)
            ).fetchone()
        if not row:
            return f"Заметка #{note_id} не найдена."
        title = row["title"] or f"note #{row['id']}"
        tags = f"\nТеги: {row['tags']}" if row["tags"] else ""
        return f"📄 *{title}*{tags}\n\n{row['content']}"
