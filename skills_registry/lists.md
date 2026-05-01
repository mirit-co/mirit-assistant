# Skill: lists

Manages named lists for the user. Each list has a name (e.g. "books", "movies", "ideas", "shopping").

## Actions

- **add**: Add an item to a list.
  Params: list_name (str), item (str)
  Example: "добавь Dune в список книг" → action=add, list_name=books, item=Dune

- **show**: Show all items in a list.
  Params: list_name (str)
  Example: "покажи мой список книг" → action=show, list_name=books

- **done**: Mark an item as done/read/watched.
  Params: list_name (str), item (str)
  Example: "отметь Dune как прочитанное" → action=done, list_name=books, item=Dune

- **delete**: Remove an item from a list.
  Params: list_name (str), item (str)

- **all_lists**: Show all list names the user has.
  Params: none

## Notes
- List names should be normalized to lowercase English: books, movies, ideas, shopping, etc.
- If user says "книги" → list_name=books; "фильмы" → list_name=movies; "идеи" → list_name=ideas
