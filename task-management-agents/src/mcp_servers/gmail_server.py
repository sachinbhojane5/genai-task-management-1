"""MCP server for Gmail tools."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from src.services.gmail_service import GmailService
from src.services.task_service import TaskService

# Initialize MCP server
gmail_mcp = FastMCP("Gmail Management Server")

# Initialize services
gmail_service = GmailService()
task_service = TaskService()


def get_user_id() -> str:
    """Get current user ID from context."""
    return "default_user"


@gmail_mcp.tool()
async def list_emails(
    query: Optional[str] = None,
    max_results: int = 10,
) -> list[dict]:
    """List emails from Gmail inbox with optional search query.

    Args:
        query: Gmail search query (e.g., "from:boss@company.com", "is:unread")
        max_results: Maximum number of emails to return

    Returns:
        List of email summaries
    """
    user_id = get_user_id()
    emails = await gmail_service.list_emails(
        user_id=user_id,
        query=query,
        max_results=max_results,
    )
    return [email.to_dict() for email in emails]


@gmail_mcp.tool()
async def read_email(message_id: str) -> Optional[dict]:
    """Read full email content by ID.

    Args:
        message_id: The unique email message identifier

    Returns:
        Full email content including body, or None if not found
    """
    user_id = get_user_id()
    email = await gmail_service.read_email(
        user_id=user_id,
        message_id=message_id,
        include_body=True,
    )
    return email.to_dict() if email else None


@gmail_mcp.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
) -> dict:
    """Send an email via Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        cc: CC recipient email address (optional)

    Returns:
        Send confirmation with message ID
    """
    user_id = get_user_id()
    result = await gmail_service.send_email(
        user_id=user_id,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
    )
    return result


@gmail_mcp.tool()
async def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
) -> dict:
    """Create an email draft in Gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body content
        cc: CC recipient email address (optional)

    Returns:
        Draft creation confirmation with draft ID
    """
    user_id = get_user_id()
    result = await gmail_service.create_draft(
        user_id=user_id,
        to=to,
        subject=subject,
        body=body,
        cc=cc,
    )
    return result


@gmail_mcp.tool()
async def search_emails(
    query: str,
    max_results: int = 20,
) -> list[dict]:
    """Search emails using Gmail query syntax.

    Gmail query examples:
    - "from:sender@example.com" - emails from specific sender
    - "to:recipient@example.com" - emails to specific recipient
    - "subject:meeting" - emails with subject containing "meeting"
    - "is:unread" - unread emails
    - "has:attachment" - emails with attachments
    - "after:2024/01/01" - emails after a date
    - "label:important" - emails with specific label

    Args:
        query: Gmail search query
        max_results: Maximum number of results to return

    Returns:
        List of matching emails
    """
    user_id = get_user_id()
    emails = await gmail_service.search_emails(
        user_id=user_id,
        query=query,
        max_results=max_results,
    )
    return [email.to_dict() for email in emails]


@gmail_mcp.tool()
async def get_unread_emails(max_results: int = 10) -> list[dict]:
    """Get unread emails from inbox.

    Args:
        max_results: Maximum number of emails to return

    Returns:
        List of unread email summaries
    """
    user_id = get_user_id()
    emails = await gmail_service.list_emails(
        user_id=user_id,
        query="is:unread",
        max_results=max_results,
    )
    return [email.to_dict() for email in emails]


@gmail_mcp.tool()
async def mark_as_read(message_id: str) -> dict:
    """Mark an email as read.

    Args:
        message_id: The unique email message identifier

    Returns:
        Status of the operation
    """
    user_id = get_user_id()
    success = await gmail_service.mark_as_read(
        user_id=user_id,
        message_id=message_id,
    )
    return {"success": success, "message_id": message_id}


@gmail_mcp.tool()
async def create_task_from_email(
    message_id: str,
    due_date: Optional[str] = None,
    priority: str = "medium",
) -> dict:
    """Extract email content and create a task from it.

    Reads the email and creates a task with the email subject as title
    and a summary of the email content as description.

    Args:
        message_id: The email message ID to create task from
        due_date: Optional due date for the task (YYYY-MM-DD)
        priority: Task priority (low, medium, high, urgent)

    Returns:
        The created task details
    """
    user_id = get_user_id()

    # Read the email
    email = await gmail_service.read_email(
        user_id=user_id,
        message_id=message_id,
        include_body=True,
    )

    if not email:
        return {"error": "Email not found", "message_id": message_id}

    # Create task from email
    task = await task_service.create_task(
        user_id=user_id,
        title=f"Follow up: {email.subject}",
        description=f"From: {email.sender}\nDate: {email.date}\n\n{email.snippet}",
        due_date=due_date,
        priority=priority,
        labels=["email", "follow-up"],
    )

    return {
        "task": task.to_dict(),
        "source_email": {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
        },
    }


@gmail_mcp.tool()
async def get_emails_from_sender(
    sender_email: str,
    max_results: int = 10,
) -> list[dict]:
    """Get emails from a specific sender.

    Args:
        sender_email: The sender's email address
        max_results: Maximum number of emails to return

    Returns:
        List of emails from the specified sender
    """
    return await search_emails(
        query=f"from:{sender_email}",
        max_results=max_results,
    )
