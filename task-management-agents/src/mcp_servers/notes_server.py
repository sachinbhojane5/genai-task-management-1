"""MCP server for notes management tools."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from src.services.notes_service import NotesService

# Initialize MCP server
notes_mcp = FastMCP("Notes Management Server")

# Initialize service
notes_service = NotesService()


def get_user_id() -> str:
    """Get current user ID from context."""
    return "default_user"


@notes_mcp.tool()
async def create_note(
    title: str,
    content: str = "",
    tags: Optional[list[str]] = None,
) -> dict:
    """Create a new note.

    Args:
        title: The note title
        content: The note content/body
        tags: List of tags for categorization

    Returns:
        The created note with its ID
    """
    user_id = get_user_id()
    note = await notes_service.create_note(
        user_id=user_id,
        title=title,
        content=content,
        tags=tags,
    )
    return note.to_dict()


@notes_mcp.tool()
async def list_notes(
    tag: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List notes with optional tag filter.

    Args:
        tag: Filter notes by a specific tag
        limit: Maximum number of notes to return

    Returns:
        List of notes matching the filter
    """
    user_id = get_user_id()
    notes = await notes_service.list_notes(
        user_id=user_id,
        tag=tag,
        limit=limit,
    )
    return [note.to_dict() for note in notes]


@notes_mcp.tool()
async def get_note(note_id: str) -> Optional[dict]:
    """Get a specific note by ID.

    Args:
        note_id: The unique note identifier

    Returns:
        The note details or None if not found
    """
    user_id = get_user_id()
    note = await notes_service.get_note(note_id, user_id)
    return note.to_dict() if note else None


@notes_mcp.tool()
async def search_notes(
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Search notes by content or tags.

    Args:
        query: Search query to match against title, content, and tags
        limit: Maximum number of results to return

    Returns:
        List of notes matching the search query
    """
    user_id = get_user_id()
    notes = await notes_service.search_notes(
        user_id=user_id,
        query_text=query,
        limit=limit,
    )
    return [note.to_dict() for note in notes]


@notes_mcp.tool()
async def update_note(
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Optional[dict]:
    """Update an existing note.

    Args:
        note_id: The unique note identifier
        title: New title (optional)
        content: New content (optional)
        tags: New tags list (optional)

    Returns:
        The updated note or None if not found
    """
    user_id = get_user_id()

    updates = {}
    if title is not None:
        updates["title"] = title
    if content is not None:
        updates["content"] = content
    if tags is not None:
        updates["tags"] = tags

    note = await notes_service.update_note(note_id, user_id, updates)
    return note.to_dict() if note else None


@notes_mcp.tool()
async def delete_note(note_id: str) -> dict:
    """Delete a note.

    Args:
        note_id: The unique note identifier

    Returns:
        Status of the deletion operation
    """
    user_id = get_user_id()
    success = await notes_service.delete_note(note_id, user_id)
    return {"success": success, "note_id": note_id}
