"""Tests for the services layer."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.task_service import TaskService, Task
from src.services.notes_service import NotesService, Note


class TestTaskService:
    """Tests for TaskService."""

    @pytest.fixture
    def task_service(self):
        """Create a TaskService with mocked Firestore."""
        with patch("src.services.task_service.firestore.AsyncClient"):
            service = TaskService()
            service._db = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_create_task(self, task_service):
        """Test creating a new task."""
        # Mock Firestore document set
        mock_doc = MagicMock()
        mock_doc.set = AsyncMock()
        task_service.db.collection.return_value.document.return_value = mock_doc

        task = await task_service.create_task(
            user_id="test_user",
            title="Test Task",
            description="Test Description",
            priority="high",
        )

        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == "high"
        assert task.status == "pending"
        assert task.user_id == "test_user"
        mock_doc.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_service):
        """Test listing tasks with filters."""
        # Mock Firestore query
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "id": "task1",
            "user_id": "test_user",
            "title": "Task 1",
            "description": "",
            "status": "pending",
            "priority": "medium",
            "labels": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.get = AsyncMock(return_value=[mock_doc])

        task_service.db.collection.return_value = mock_query

        tasks = await task_service.list_tasks(user_id="test_user")

        assert len(tasks) == 1
        assert tasks[0].title == "Task 1"


class TestNotesService:
    """Tests for NotesService."""

    @pytest.fixture
    def notes_service(self):
        """Create a NotesService with mocked Firestore."""
        with patch("src.services.notes_service.firestore.AsyncClient"):
            service = NotesService()
            service._db = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_create_note(self, notes_service):
        """Test creating a new note."""
        mock_doc = MagicMock()
        mock_doc.set = AsyncMock()
        notes_service.db.collection.return_value.document.return_value = mock_doc

        note = await notes_service.create_note(
            user_id="test_user",
            title="Test Note",
            content="Test Content",
            tags=["test", "demo"],
        )

        assert note.title == "Test Note"
        assert note.content == "Test Content"
        assert note.tags == ["test", "demo"]
        mock_doc.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_notes(self, notes_service):
        """Test searching notes."""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "id": "note1",
            "user_id": "test_user",
            "title": "Meeting Notes",
            "content": "Important meeting content",
            "tags": ["meeting"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.get = AsyncMock(return_value=[mock_doc])

        notes_service.db.collection.return_value = mock_query

        # Search for "meeting"
        notes = await notes_service.search_notes(
            user_id="test_user",
            query_text="meeting",
        )

        assert len(notes) == 1
        assert "meeting" in notes[0].title.lower()


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation(self):
        """Test Task dataclass creation."""
        task = Task(
            id="123",
            user_id="user1",
            title="My Task",
        )

        assert task.id == "123"
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.labels == []

    def test_task_to_dict(self):
        """Test Task serialization."""
        task = Task(
            id="123",
            user_id="user1",
            title="My Task",
            priority="high",
        )

        data = task.to_dict()

        assert data["id"] == "123"
        assert data["priority"] == "high"
        assert "created_at" in data


class TestNote:
    """Tests for Note dataclass."""

    def test_note_creation(self):
        """Test Note dataclass creation."""
        note = Note(
            id="123",
            user_id="user1",
            title="My Note",
            tags=["tag1", "tag2"],
        )

        assert note.id == "123"
        assert note.tags == ["tag1", "tag2"]

    def test_note_from_dict(self):
        """Test Note deserialization."""
        data = {
            "id": "123",
            "user_id": "user1",
            "title": "My Note",
            "content": "Content here",
            "tags": ["important"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        note = Note.from_dict(data)

        assert note.id == "123"
        assert note.content == "Content here"
