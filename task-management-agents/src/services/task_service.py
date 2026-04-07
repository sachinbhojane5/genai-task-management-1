"""Task management service with Firestore backend."""

import os
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict
from google.cloud import firestore


@dataclass
class Task:
    """Task data model."""

    id: str
    user_id: str
    title: str
    description: str = ""
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "pending"  # pending, in_progress, completed, cancelled
    labels: list[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class TaskService:
    """Firestore-backed task management service."""

    def __init__(self, collection_name: str = "tasks"):
        self.collection_name = collection_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self._db: Optional[firestore.AsyncClient] = None

    @property
    def db(self) -> firestore.AsyncClient:
        if self._db is None:
            self._db = firestore.AsyncClient(project=self.project_id)
        return self._db

    async def create_task(
        self,
        user_id: str,
        title: str,
        description: str = "",
        due_date: Optional[str] = None,
        priority: str = "medium",
        labels: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            labels=labels or [],
        )

        await self.db.collection(self.collection_name).document(task.id).set(
            task.to_dict()
        )
        return task

    async def get_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Retrieve a task by ID."""
        doc = await self.db.collection(self.collection_name).document(task_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        if data.get("user_id") != user_id:
            return None

        return Task.from_dict(data)

    async def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> list[Task]:
        """List tasks with optional filters."""
        query = self.db.collection(self.collection_name).where(
            "user_id", "==", user_id
        )

        if status and status != "all":
            query = query.where("status", "==", status)
        if priority:
            query = query.where("priority", "==", priority)

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        docs = await query.get()
        return [Task.from_dict(doc.to_dict()) for doc in docs]

    async def update_task(
        self,
        task_id: str,
        user_id: str,
        updates: dict,
    ) -> Optional[Task]:
        """Update a task."""
        task = await self.get_task(task_id, user_id)
        if not task:
            return None

        # Filter allowed updates
        allowed_fields = {"title", "description", "due_date", "priority", "status", "labels"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        filtered_updates["updated_at"] = datetime.utcnow().isoformat()

        await self.db.collection(self.collection_name).document(task_id).update(
            filtered_updates
        )

        # Return updated task
        return await self.get_task(task_id, user_id)

    async def complete_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return await self.update_task(task_id, user_id, {"status": "completed"})

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task."""
        task = await self.get_task(task_id, user_id)
        if not task:
            return False

        await self.db.collection(self.collection_name).document(task_id).delete()
        return True
