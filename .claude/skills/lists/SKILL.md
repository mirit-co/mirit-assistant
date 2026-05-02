---
name: lists
description: Manage the user's named lists (books, movies, groceries, ideas, tasks, etc.) stored in the assistant SQLite DB. Use this skill whenever the user mentions any list by name, asks to add or remove an item, wants to see what's on a list, asks to mark something done, or says things like "add X to my Y list", "what's on my list", "show my lists", "delete X from", "check off", or "I finished X". Trigger even if the user doesn't say "list" explicitly — if they're clearly tracking a collection of items, use this skill.
allowed-tools: Bash(ssh *)
---

Work with the user's lists in the assistant database on the DigitalOcean droplet.

**DB lives on the droplet** — always access it via SSH:

```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db \"...\""
```

## Schema

```sql
users(id, telegram_id, username)
lists(id, user_id, list_name TEXT, item TEXT, done INTEGER, created_at TEXT)
```

## Step 1 — Get user_id

Always start by fetching the user_id (single-user setup):

```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT id FROM users LIMIT 1'"
```

Use the returned value as `$UID` in all subsequent queries.

## Operations

**Show all lists:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT list_name, COUNT(*) AS n FROM lists WHERE user_id=$UID GROUP BY list_name'"
```

**Show items in a list:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'SELECT item, done FROM lists WHERE user_id=$UID AND list_name=''books'' ORDER BY created_at'"
```

**Add an item:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'INSERT INTO lists (user_id, list_name, item) VALUES ($UID, ''books'', ''Dune'')'"
```

**Mark item done:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'UPDATE lists SET done=1 WHERE user_id=$UID AND list_name=''books'' AND item LIKE ''%Dune%'''"
```

**Delete an item:**
```bash
ssh -i ~/.ssh/kartuli_bot_deploy root@165.232.116.241 "sqlite3 ~/assistant/data/assistant.db 'DELETE FROM lists WHERE user_id=$UID AND list_name=''books'' AND item LIKE ''%Dune%'''"
```

## Notes

- List names are free-form strings (e.g. `books`, `movies`, `ideas`, `shopping`).
- Escape apostrophes in SQL with `''` (e.g. `'don''t'` → `''don''''t''`).
- After any mutation, show the updated list to the user.
