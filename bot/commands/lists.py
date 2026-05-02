from storage.db import get_conn


class Lists:
    def execute(self, action: str, params: dict, user_id: int) -> str:
        if action == "add":
            return self._add(user_id, params.get("list_name", "misc"), params.get("item", ""))
        elif action == "show":
            return self._show(user_id, params.get("list_name", ""))
        elif action == "done":
            return self._done(user_id, params.get("list_name", ""), params.get("item", ""))
        elif action == "delete":
            return self._delete(user_id, params.get("list_name", ""), params.get("item", ""))
        elif action == "all_lists":
            return self._all_lists(user_id)
        elif action == "toggle":
            return self._toggle(user_id, params.get("list_name", ""), params.get("item_id", 0))
        elif action == "reset_all":
            return self._reset_all(user_id, params.get("list_name", ""))
        return f"Неизвестное действие: {action}"

    def _add(self, user_id: int, list_name: str, item: str) -> str:
        if not item:
            return "Не указан элемент для добавления."
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO lists (user_id, list_name, item) VALUES (?, ?, ?)",
                (user_id, list_name, item),
            )
        return f"✅ Добавил «{item}» в список *{list_name}*"

    def _show(self, user_id: int, list_name: str) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT item, done FROM lists WHERE user_id=? AND list_name=? ORDER BY created_at",
                (user_id, list_name),
            ).fetchall()
        if not rows:
            return f"Список *{list_name}* пуст."
        lines = []
        for i, row in enumerate(rows, 1):
            mark = "✓" if row["done"] else "○"
            lines.append(f"{i}. {mark} {row['item']}")
        return f"📋 *{list_name}* ({len(rows)}):\n" + "\n".join(lines)

    def _done(self, user_id: int, list_name: str, item: str) -> str:
        with get_conn() as conn:
            result = conn.execute(
                "UPDATE lists SET done=1 WHERE user_id=? AND list_name=? AND item LIKE ?",
                (user_id, list_name, f"%{item}%"),
            )
        if result.rowcount == 0:
            return f"Не нашёл «{item}» в списке {list_name}."
        return f"✅ Отметил «{item}» как выполненное"

    def _delete(self, user_id: int, list_name: str, item: str) -> str:
        with get_conn() as conn:
            conn.execute(
                "DELETE FROM lists WHERE user_id=? AND list_name=? AND item LIKE ?",
                (user_id, list_name, f"%{item}%"),
            )
        return f"🗑 Удалил «{item}» из списка {list_name}"

    def _toggle(self, user_id: int, list_name: str, item_id: int) -> str:
        with get_conn() as conn:
            conn.execute(
                "UPDATE lists SET done = 1 - done WHERE id=? AND user_id=? AND list_name=?",
                (item_id, user_id, list_name),
            )
        return "ok"

    def _reset_all(self, user_id: int, list_name: str) -> str:
        with get_conn() as conn:
            conn.execute(
                "UPDATE lists SET done=0 WHERE user_id=? AND list_name=?",
                (user_id, list_name),
            )
        return "ok"

    def _all_lists(self, user_id: int) -> str:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT list_name, COUNT(*) as cnt FROM lists WHERE user_id=? GROUP BY list_name",
                (user_id,),
            ).fetchall()
        if not rows:
            return "У тебя пока нет списков."
        lines = [f"• {row['list_name']} ({row['cnt']} элем.)" for row in rows]
        return "📚 Твои списки:\n" + "\n".join(lines)
