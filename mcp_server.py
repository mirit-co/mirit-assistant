"""MCP server exposing assistant skills as Claude Code tools."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from storage.db import get_or_create_user, init_db
from skills.lists import ListsSkill
from skills.knowledge import KnowledgeSkill

init_db()

# Default owner user (telegram_id=0 means local/MCP access)
MCP_TELEGRAM_ID = int(os.environ.get("ASSISTANT_TELEGRAM_ID", "0"))
MCP_USERNAME = os.environ.get("ASSISTANT_USERNAME", "mcp_user")

_lists = ListsSkill()
_knowledge = KnowledgeSkill()


def _user_id() -> int:
    return get_or_create_user(MCP_TELEGRAM_ID, MCP_USERNAME)


mcp = FastMCP("assistant")


# ── Lists ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_add(list_name: str, item: str) -> str:
    """Add an item to a named list (books, movies, ideas, shopping, etc.)."""
    return _lists.execute("add", {"list_name": list_name, "item": item}, _user_id())


@mcp.tool()
def list_show(list_name: str) -> str:
    """Show all items in a named list."""
    return _lists.execute("show", {"list_name": list_name}, _user_id())


@mcp.tool()
def list_done(list_name: str, item: str) -> str:
    """Mark an item in a list as done/read/watched."""
    return _lists.execute("done", {"list_name": list_name, "item": item}, _user_id())


@mcp.tool()
def list_delete(list_name: str, item: str) -> str:
    """Remove an item from a list."""
    return _lists.execute("delete", {"list_name": list_name, "item": item}, _user_id())


@mcp.tool()
def list_all() -> str:
    """Show all list names the user has."""
    return _lists.execute("all_lists", {}, _user_id())


# ── Knowledge base ─────────────────────────────────────────────────────────────

@mcp.tool()
def knowledge_save(content: str, title: str = "", tags: str = "") -> str:
    """Save a note to the knowledge base."""
    return _knowledge.execute("save", {"content": content, "title": title, "tags": tags}, _user_id())


@mcp.tool()
def knowledge_search(query: str) -> str:
    """Search notes in the knowledge base by keyword or tag."""
    return _knowledge.execute("search", {"query": query}, _user_id())


@mcp.tool()
def knowledge_list(limit: int = 10) -> str:
    """Show recent notes (titles only)."""
    return _knowledge.execute("list", {"limit": limit}, _user_id())


@mcp.tool()
def knowledge_get(note_id: int) -> str:
    """Get full content of a note by its ID."""
    return _knowledge.execute("get", {"note_id": note_id}, _user_id())


if __name__ == "__main__":
    mcp.run()
