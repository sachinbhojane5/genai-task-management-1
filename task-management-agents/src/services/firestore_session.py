"""Custom Firestore-based SessionService for Google ADK."""

import os
from datetime import datetime
from typing import Optional
from google.cloud import firestore
from google.adk.sessions import BaseSessionService, Session, Event


class FirestoreSessionService(BaseSessionService):
    """
    Firestore-backed session service for ADK agents.

    Stores sessions and events in Firestore collections for persistence
    across server restarts and horizontal scaling.
    """

    def __init__(self, collection_name: str = "agent_sessions"):
        self.collection_name = collection_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self._db: Optional[firestore.AsyncClient] = None

    @property
    def db(self) -> firestore.AsyncClient:
        if self._db is None:
            self._db = firestore.AsyncClient(project=self.project_id)
        return self._db

    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: Optional[str] = None,
        state: Optional[dict] = None,
    ) -> Session:
        """Create a new session in Firestore."""
        session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state=state or {},
        )

        session_data = {
            "app_name": session.app_name,
            "user_id": session.user_id,
            "state": session.state,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await self.db.collection(self.collection_name).document(session.id).set(
            session_data
        )
        return session

    async def get_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> Optional[Session]:
        """Retrieve a session from Firestore."""
        doc = await self.db.collection(self.collection_name).document(session_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()

        # Verify ownership
        if data.get("app_name") != app_name or data.get("user_id") != user_id:
            return None

        session = Session(
            app_name=data["app_name"],
            user_id=data["user_id"],
            id=session_id,
            state=data.get("state", {}),
        )

        # Load events
        events_ref = (
            self.db.collection(self.collection_name)
            .document(session_id)
            .collection("events")
            .order_by("timestamp")
        )
        events_docs = await events_ref.get()

        for event_doc in events_docs:
            event_data = event_doc.to_dict()
            event = Event(
                author=event_data.get("author"),
                content=event_data.get("content"),
                actions=event_data.get("actions", []),
                timestamp=event_data.get("timestamp"),
            )
            session.events.append(event)

        return session

    async def list_sessions(
        self,
        app_name: str,
        user_id: str,
    ) -> list[Session]:
        """List all sessions for a user."""
        query = (
            self.db.collection(self.collection_name)
            .where("app_name", "==", app_name)
            .where("user_id", "==", user_id)
            .order_by("updated_at", direction=firestore.Query.DESCENDING)
        )

        docs = await query.get()
        sessions = []

        for doc in docs:
            data = doc.to_dict()
            session = Session(
                app_name=data["app_name"],
                user_id=data["user_id"],
                id=doc.id,
                state=data.get("state", {}),
            )
            sessions.append(session)

        return sessions

    async def delete_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
    ) -> None:
        """Delete a session and all its events."""
        session_ref = self.db.collection(self.collection_name).document(session_id)

        # Delete all events first
        events_ref = session_ref.collection("events")
        events_docs = await events_ref.get()
        for event_doc in events_docs:
            await event_doc.reference.delete()

        # Delete session document
        await session_ref.delete()

    async def append_event(
        self,
        session: Session,
        event: Event,
    ) -> Event:
        """Append an event to a session."""
        session_ref = self.db.collection(self.collection_name).document(session.id)

        event_data = {
            "author": event.author,
            "content": event.content,
            "actions": event.actions,
            "timestamp": event.timestamp or datetime.utcnow().isoformat(),
        }

        # Add event to subcollection
        await session_ref.collection("events").add(event_data)

        # Update session state and timestamp
        await session_ref.update(
            {
                "state": session.state,
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

        session.events.append(event)
        return event
