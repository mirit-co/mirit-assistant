# Skill: knowledge

Saves notes and lets the user search through them. Think of it as a personal knowledge base.

## Actions

- **save**: Save a note.
  Params: content (str), title (str, optional), tags (str, optional, comma-separated)
  Example: "сохрани заметку: dbt best practices — всегда используй sources" → action=save, content=..., title=dbt best practices

- **search**: Search notes by keyword or tag.
  Params: query (str)
  Example: "найди всё про dbt" → action=search, query=dbt

- **list**: Show recent notes (titles only).
  Params: limit (int, default 10)

- **get**: Get full content of a specific note.
  Params: note_id (int)

## Notes
- Tags are optional but useful for filtering.
- Search checks both content and title.
