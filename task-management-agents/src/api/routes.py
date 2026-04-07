"""Custom API routes for the task management system."""

import os
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from src.services.task_service import TaskService
from src.services.notes_service import NotesService
from src.services.calendar_service import CalendarService
from src.services.gmail_service import GmailService
from src.services.google_auth import GoogleAuthService
from src.auth.iam_middleware import get_current_user

router = APIRouter()

# Initialize services
task_service = TaskService()
notes_service = NotesService()
calendar_service = CalendarService()
gmail_service = GmailService()
auth_service = GoogleAuthService()


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


# Helper to get user_id from request
def get_user_id(request: Request) -> str:
    user = get_current_user(request)
    return user.get("user_id") or "default_user"


# === Chat endpoint (for direct agent interaction) ===
@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """
    Send a message to the orchestrator agent.

    This endpoint processes natural language requests and
    delegates to appropriate sub-agents.
    """
    user_id = get_user_id(request)

    # This would integrate with the ADK runner
    # For now, return a placeholder
    return ChatResponse(
        response=f"Received: {chat_request.message}. Agent processing not yet implemented.",
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
    tasks = await task_service.list_tasks(
        user_id=user_id,
        status=status,
        priority=priority,
        limit=limit,
    )
    return {"tasks": [task.to_dict() for task in tasks]}


@router.post("/tasks")
async def create_task(request: Request, task_request: TaskCreateRequest):
    """Create a new task."""
    user_id = get_user_id(request)
    task = await task_service.create_task(
        user_id=user_id,
        title=task_request.title,
        description=task_request.description,
        due_date=task_request.due_date,
        priority=task_request.priority,
        labels=task_request.labels,
    )
    return {"task": task.to_dict()}


@router.get("/tasks/{task_id}")
async def get_task(request: Request, task_id: str):
    """Get a specific task by ID."""
    user_id = get_user_id(request)
    task = await task_service.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.to_dict()}


@router.patch("/tasks/{task_id}")
async def update_task(request: Request, task_id: str, updates: dict):
    """Update a task."""
    user_id = get_user_id(request)
    task = await task_service.update_task(task_id, user_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.to_dict()}


@router.post("/tasks/{task_id}/complete")
async def complete_task(request: Request, task_id: str):
    """Mark a task as completed."""
    user_id = get_user_id(request)
    task = await task_service.complete_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.to_dict()}


@router.delete("/tasks/{task_id}")
async def delete_task(request: Request, task_id: str):
    """Delete a task."""
    user_id = get_user_id(request)
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
    notes = await notes_service.list_notes(
        user_id=user_id,
        tag=tag,
        limit=limit,
    )
    return {"notes": [note.to_dict() for note in notes]}


@router.post("/notes")
async def create_note(request: Request, note_request: NoteCreateRequest):
    """Create a new note."""
    user_id = get_user_id(request)
    note = await notes_service.create_note(
        user_id=user_id,
        title=note_request.title,
        content=note_request.content,
        tags=note_request.tags,
    )
    return {"note": note.to_dict()}


@router.get("/notes/search")
async def search_notes(request: Request, q: str, limit: int = 20):
    """Search notes by content or tags."""
    user_id = get_user_id(request)
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

    # Default to today and next 7 days
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = (date.today() + timedelta(days=7)).isoformat()

    try:
        events = await calendar_service.list_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {"events": [event.to_dict() for event in events]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/events/today")
async def get_todays_events(request: Request):
    """Get today's calendar events."""
    user_id = get_user_id(request)
    today = date.today().isoformat()

    try:
        events = await calendar_service.list_events(
            user_id=user_id,
            start_date=today,
            end_date=today,
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
        emails = await gmail_service.list_emails(
            user_id=user_id,
            query=query,
            max_results=max_results,
        )
        return {"emails": [email.to_dict() for email in emails]}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/emails/unread")
async def get_unread_emails(request: Request, max_results: int = 10):
    """Get unread emails from Gmail."""
    user_id = get_user_id(request)

    try:
        emails = await gmail_service.list_emails(
            user_id=user_id,
            query="is:unread",
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
    auth_url, state = auth_service.get_authorization_url(user_id)
    return {"authorization_url": auth_url, "state": state}


@router.get("/oauth/callback")
async def oauth_callback(request: Request, code: str, state: str):
    """Handle OAuth callback from Google."""
    try:
        credentials = await auth_service.exchange_code(code, state)
        return {
            "status": "success",
            "message": "Google account connected successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/oauth/status")
async def oauth_status(request: Request):
    """Check if user has connected their Google account."""
    user_id = get_user_id(request)
    credentials = await auth_service.get_credentials(user_id)
    return {
        "connected": credentials is not None,
        "user_id": user_id,
    }
