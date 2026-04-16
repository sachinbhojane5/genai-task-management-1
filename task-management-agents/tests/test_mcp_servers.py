"""Tests for MCP server tools."""

import pytest
from unittest.mock import AsyncMock, patch


class TestTaskMCPServer:
    """Tests for task MCP server tools."""

    @pytest.mark.asyncio
    async def test_create_task_tool(self):
        """Test create_task MCP tool."""
        with patch("src.mcp_servers.task_server.task_service") as mock_service:
            from src.mcp_servers.task_server import create_task
            from src.services.task_service import Task

            # Mock the service response
            mock_task = Task(
                id="task123",
                user_id="default_user",
                title="Test Task",
                description="Test Description",
            )
            mock_service.create_task = AsyncMock(return_value=mock_task)

            result = await create_task(
                title="Test Task",
                description="Test Description",
                priority="high",
            )

            assert result["title"] == "Test Task"
            assert result["id"] == "task123"

    @pytest.mark.asyncio
    async def test_list_tasks_tool(self):
        """Test list_tasks MCP tool."""
        with patch("src.mcp_servers.task_server.task_service") as mock_service:
            from src.mcp_servers.task_server import list_tasks
            from src.services.task_service import Task

            mock_tasks = [
                Task(id="1", user_id="default_user", title="Task 1"),
                Task(id="2", user_id="default_user", title="Task 2"),
            ]
            mock_service.list_tasks = AsyncMock(return_value=mock_tasks)

            result = await list_tasks(status="pending")

            assert len(result) == 2
            assert result[0]["title"] == "Task 1"


class TestNotesMCPServer:
    """Tests for notes MCP server tools."""

    @pytest.mark.asyncio
    async def test_create_note_tool(self):
        """Test create_note MCP tool."""
        with patch("src.mcp_servers.notes_server.notes_service") as mock_service:
            from src.mcp_servers.notes_server import create_note
            from src.services.notes_service import Note

            mock_note = Note(
                id="note123",
                user_id="default_user",
                title="Test Note",
                content="Content",
            )
            mock_service.create_note = AsyncMock(return_value=mock_note)

            result = await create_note(
                title="Test Note",
                content="Content",
                tags=["test"],
            )

            assert result["title"] == "Test Note"
            assert result["id"] == "note123"

    @pytest.mark.asyncio
    async def test_search_notes_tool(self):
        """Test search_notes MCP tool."""
        with patch("src.mcp_servers.notes_server.notes_service") as mock_service:
            from src.mcp_servers.notes_server import search_notes
            from src.services.notes_service import Note

            mock_notes = [
                Note(
                    id="1",
                    user_id="default_user",
                    title="Meeting Notes",
                    content="Important",
                )
            ]
            mock_service.search_notes = AsyncMock(return_value=mock_notes)

            result = await search_notes(query="meeting")

            assert len(result) == 1
            assert "meeting" in result[0]["title"].lower()


class TestCalendarMCPServer:
    """Tests for calendar MCP server tools."""

    @pytest.mark.asyncio
    async def test_check_availability_tool(self):
        """Test check_availability MCP tool."""
        with patch("src.mcp_servers.calendar_server.calendar_service") as mock_service:
            from src.mcp_servers.calendar_server import check_availability

            mock_slots = [
                {"start": "2024-03-15T09:00:00Z", "end": "2024-03-15T10:00:00Z"},
                {"start": "2024-03-15T14:00:00Z", "end": "2024-03-15T15:00:00Z"},
            ]
            mock_service.check_availability = AsyncMock(return_value=mock_slots)

            result = await check_availability(
                date="2024-03-15",
                duration_minutes=60,
            )

            assert len(result) == 2
            assert "start" in result[0]


class TestGmailMCPServer:
    """Tests for Gmail MCP server tools."""

    @pytest.mark.asyncio
    async def test_list_emails_tool(self):
        """Test list_emails MCP tool."""
        with patch("src.mcp_servers.gmail_server.gmail_service") as mock_service:
            from src.mcp_servers.gmail_server import list_emails
            from src.services.gmail_service import Email

            mock_emails = [
                Email(
                    id="email1",
                    thread_id="thread1",
                    subject="Test Email",
                    sender="test@example.com",
                    to="me@example.com",
                    date="2024-03-15",
                    snippet="Email preview...",
                )
            ]
            mock_service.list_emails = AsyncMock(return_value=mock_emails)

            result = await list_emails(query="is:unread")

            assert len(result) == 1
            assert result[0]["subject"] == "Test Email"

    @pytest.mark.asyncio
    async def test_create_task_from_email_tool(self):
        """Test create_task_from_email MCP tool."""
        with patch("src.mcp_servers.gmail_server.gmail_service") as mock_gmail, \
             patch("src.mcp_servers.gmail_server.task_service") as mock_task:
            from src.mcp_servers.gmail_server import create_task_from_email
            from src.services.gmail_service import Email
            from src.services.task_service import Task

            mock_email = Email(
                id="email1",
                thread_id="thread1",
                subject="Action Required: Review Document",
                sender="boss@company.com",
                to="me@company.com",
                date="2024-03-15",
                snippet="Please review the attached document...",
            )
            mock_gmail.read_email = AsyncMock(return_value=mock_email)

            mock_task_obj = Task(
                id="task1",
                user_id="default_user",
                title="Follow up: Action Required: Review Document",
            )
            mock_task.create_task = AsyncMock(return_value=mock_task_obj)

            result = await create_task_from_email(message_id="email1")

            assert "task" in result
            assert "source_email" in result
