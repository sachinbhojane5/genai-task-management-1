"""Custom API routes for the task management system."""

import logging
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Lazy-loaded services (initialized on first use)
_task_service = None
_notes_service = None
_calendar_service = None
_gmail_service = None
_auth_service = None


def get_task_service():
    global _task_service
    if _task_service is None:
        from src.services.task_service import TaskService
        _task_service = TaskService()
    return _task_service


def get_notes_service():
    global _notes_service
    if _notes_service is None:
        from src.services.notes_service import NotesService
        _notes_service = NotesService()
    return _notes_service


def get_calendar_service():
    global _calendar_service
    if _calendar_service is None:
        from src.services.calendar_service import CalendarService
        _calendar_service = CalendarService()
    return _calendar_service


def get_gmail_service():
    global _gmail_service
    if _gmail_service is None:
        from src.services.gmail_service import GmailService
        _gmail_service = GmailService()
    return _gmail_service


def get_auth_service():
    global _auth_service
    if _auth_service is None:
        from src.services.google_auth import GoogleAuthService
        _auth_service = GoogleAuthService()
    return _auth_service


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class TaskCreateRequest(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[str] = None
    priority: str = "medium"
    labels: Optional[list[str]] = None


class NoteCreateRequest(BaseModel):
    title: str
    content: str = ""
    tags: Optional[list[str]] = None


def get_user_id(request: Request) -> str:
    """Get user_id from request state or return default."""
    return getattr(request.state, "user_id", None) or "default_user"


# === Chat endpoint ===
@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """Send a message to the orchestrator agent."""
    user_id = get_user_id(request)
    return ChatResponse(
        response=f"Received: {chat_request.message}. Agent processing coming soon.",
        session_id=chat_request.session_id or "new-session",
    )


# === Task endpoints ===
@router.get("/tasks")
async def list_tasks(
    request: Request,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
):
    """List tasks for the current user."""
    user_id = get_user_id(request)
    try:
        task_service = get_task_service()
        tasks = await task_service.list_tasks(
            user_id=user_id,
            status=status,
            priority=priority,
            limit=limit,
        )
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def create_task(request: Request, task_request: TaskCreateRequest):
    """Create a new task."""
    user_id = get_user_id(request)
    try:
        task_service = get_task_service()
        task = await task_service.create_task(
            user_id=user_id,
            title=task_request.title,
            description=task_request.description,
            due_date=task_request.due_date,
            priority=task_request.priority,
            labels=task_request.labels,
        )
        return {"task": task.to_dict()}
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task(request: Request, task_id: str):
    """Get a specific task by ID."""
    user_id = get_user_id(request)
    task_service = get_task_service()
    task = await task_service.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.to_dict()}


@router.post("/tasks/{task_id}/complete")
async def complete_task(request: Request, task_id: str):
    """Mark a task as completed."""
    user_id = get_user_id(request)
    task_service = get_task_service()
    task = await task_service.complete_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.to_dict()}


@router.delete("/tasks/{task_id}")
async def delete_task(request: Request, task_id: str):
    """Delete a task."""
    user_id = get_user_id(request)
    task_service = get_task_service()
    success = await task_service.delete_task(task_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True}


# === Notes endpoints ===
@router.get("/notes")
async def list_notes(
    request: Request,
    tag: Optional[str] = None,
    limit: int = 50,
):
    """List notes for the current user."""
    user_id = get_user_id(request)
    try:
        notes_service = get_notes_service()
        notes = await notes_service.list_notes(
            user_id=user_id,
            tag=tag,
            limit=limit,
        )
        return {"notes": [note.to_dict() for note in notes]}
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes")
async def create_note(request: Request, note_request: NoteCreateRequest):
    """Create a new note."""
    user_id = get_user_id(request)
    try:
        notes_service = get_notes_service()
        note = await notes_service.create_note(
            user_id=user_id,
            title=note_request.title,
            content=note_request.content,
            tags=note_request.tags,
        )
        return {"note": note.to_dict()}
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/search")
async def search_notes(request: Request, q: str, limit: int = 20):
    """Search notes by content or tags."""
    user_id = get_user_id(request)
    notes_service = get_notes_service()
    notes = await notes_service.search_notes(
        user_id=user_id,
        query_text=q,
        limit=limit,
    )
    return {"notes": [note.to_dict() for note in notes]}


# === Calendar endpoints ===
@router.get("/events")
async def list_events(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """List calendar events from Google Calendar."""
    user_id = get_user_id(request)
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = (date.today() + timedelta(days=7)).isoformat()

    try:
        calendar_service = get_calendar_service()
        events = await calendar_service.list_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {"events": [event.to_dict() for event in events]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# === Email endpoints ===
@router.get("/emails")
async def list_emails(
    request: Request,
    query: Optional[str] = None,
    max_results: int = 10,
):
    """List emails from Gmail."""
    user_id = get_user_id(request)
    try:
        gmail_service = get_gmail_service()
        emails = await gmail_service.list_emails(
            user_id=user_id,
            query=query,
            max_results=max_results,
        )
        return {"emails": [email.to_dict() for email in emails]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# === OAuth endpoints ===
@router.get("/oauth/authorize")
async def oauth_authorize(request: Request):
    """Start OAuth flow for Google Workspace APIs."""
    user_id = get_user_id(request)
    auth_service = get_auth_service()
    auth_url, state = auth_service.get_authorization_url(user_id)
    return {"authorization_url": auth_url, "state": state}


@router.get("/oauth/callback")
async def oauth_callback(request: Request, code: str, state: str):
    """Handle OAuth callback from Google."""
    try:
        auth_service = get_auth_service()
        await auth_service.exchange_code(code, state)
        return {"status": "success", "message": "Google account connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/status")
async def oauth_status(request: Request):
    """Check if user has connected their Google account."""
    user_id = get_user_id(request)
    auth_service = get_auth_service()
    credentials = await auth_service.get_credentials(user_id)
    return {"connected": credentials is not None, "user_id": user_id}
