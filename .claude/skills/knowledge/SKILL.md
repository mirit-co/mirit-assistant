---
name: knowledge
description: Search, read, save, and manage notes in the user's personal knowledge base stored in the assistant SQLite DB. Use this skill whenever the user wants to save something to remember, look something up from their notes, ask "do I have a note about X", recall information stored earlier, list recent notes, browse by category/tag, or says things like "remember this", "save this", "what did I save about", "find my note on", "show notes about". Trigger even if the user just says "remember" or "I want to save" — if they're storing or retrieving personal information, use this skill.
allowed-tools: Bash(ssh *)
---

Work with the user's knowledge base on the DigitalOcean droplet.

**DB lives on the droplet** — always access it via SSH:

```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db \"...\""
```

## Schema

```sql
users(id, telegram_id, username)
notes(id, user_id, title TEXT, content TEXT, tags TEXT, created_at TEXT)
```

Tags serve as category keys (e.g. `georgian-contacts`, `recipes`, `notes`).

## Step 1 — Get user_id

Always start by fetching the user_id (single-user setup):

```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT id FROM users LIMIT 1'"
```

Use the returned value as `$UID` in all subsequent queries.

## Operations

**List recent notes:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT id, title, created_at FROM notes WHERE user_id=$UID ORDER BY created_at DESC LIMIT 10'"
```

**Search by keyword:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT id, title, substr(content, 1, 100) FROM notes WHERE user_id=$UID AND (title LIKE ''%query%'' OR content LIKE ''%query%'' OR tags LIKE ''%query%'') ORDER BY created_at DESC LIMIT 5'"
```

**Filter by category (tag):**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT id, title, created_at FROM notes WHERE user_id=$UID AND tags LIKE ''%georgian-contacts%'' ORDER BY created_at DESC'"
```

**Read a full note:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT title, content, tags FROM notes WHERE id=42 AND user_id=$UID'"
```

**Save a note:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'INSERT INTO notes (user_id, title, content, tags) VALUES ($UID, ''Title'', ''Content here'', ''notes'')'"
```

**Delete a note:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'DELETE FROM notes WHERE id=42 AND user_id=$UID'"
```

## Notes

- `title` is optional; `content` is required.
- Tags are comma-separated strings used for category filtering.
- Escape apostrophes with `''` in SQL strings.
- When saving, suggest a tag/category if the user didn't specify one.
