"""Notes management service with Firestore backend."""

import os
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from google.cloud import firestore


@dataclass
class Note:
    """Note data model."""

    id: str
    user_id: str
    title: str
    content: str = ""
    tags: list[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class NotesService:
    """Firestore-backed notes service."""

    def __init__(self, collection_name: str = "notes"):
        self.collection_name = collection_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self._db: Optional[firestore.AsyncClient] = None

    @property
    def db(self) -> firestore.AsyncClient:
        if self._db is None:
            self._db = firestore.AsyncClient(project=self.project_id)
        return self._db

    async def create_note(
        self,
        user_id: str,
        title: str,
        content: str = "",
        tags: Optional[list[str]] = None,
    ) -> Note:
        """Create a new note."""
        note = Note(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            content=content,
            tags=tags or [],
        )

        await self.db.collection(self.collection_name).document(note.id).set(
            note.to_dict()
        )
        return note

    async def get_note(self, note_id: str, user_id: str) -> Optional[Note]:
        """Retrieve a note by ID."""
        doc = await self.db.collection(self.collection_name).document(note_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        if data.get("user_id") != user_id:
            return None

        return Note.from_dict(data)

    async def list_notes(
        self,
        user_id: str,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> list[Note]:
        """List notes with optional tag filter."""
        query = self.db.collection(self.collection_name).where(
            "user_id", "==", user_id
        )

        if tag:
            query = query.where("tags", "array_contains", tag)

        query = query.order_by("updated_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = await query.get()
        return [Note.from_dict(doc.to_dict()) for doc in docs]

    async def search_notes(
        self,
        user_id: str,
        query_text: str,
        limit: int = 20,
    ) -> list[Note]:
        """Search notes by content or tags.

        Note: This is a simple implementation. For production,
        consider using Firestore full-text search extensions or
        integrating with a search service like Algolia.
        """
        # Get all user's notes and filter client-side
        # For production, use a proper search index
        all_notes = await self.list_notes(user_id, limit=200)

        query_lower = query_text.lower()
        matching_notes = []

        for note in all_notes:
            # Check title, content, and tags
            if (
                query_lower in note.title.lower()
                or query_lower in note.content.lower()
                or any(query_lower in tag.lower() for tag in note.tags)
            ):
                matching_notes.append(note)
                if len(matching_notes) >= limit:
                    break

        return matching_notes

    async def update_note(
        self,
        note_id: str,
        user_id: str,
        updates: dict,
    ) -> Optional[Note]:
        """Update a note."""
        note = await self.get_note(note_id, user_id)
        if not note:
            return None

        # Filter allowed updates
        allowed_fields = {"title", "content", "tags"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        filtered_updates["updated_at"] = datetime.utcnow().isoformat()

        await self.db.collection(self.collection_name).document(note_id).update(
            filtered_updates
        )

        return await self.get_note(note_id, user_id)

    async def delete_note(self, note_id: str, user_id: str) -> bool:
        """Delete a note."""
        note = await self.get_note(note_id, user_id)
        if not note:
            return False

        await self.db.collection(self.collection_name).document(note_id).delete()
        return True
