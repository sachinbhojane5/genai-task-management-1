"""MCP server for task management tools."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from src.services.task_service import TaskService

# Initialize MCP server
task_mcp = FastMCP("Task Management Server")

# Initialize service (will be set with user context at runtime)
task_service = TaskService()


def get_user_id() -> str:
    """Get current user ID from context.

    In production, this would be extracted from the request context.
    """
    # This will be replaced with actual user context injection
    return "default_user"


@task_mcp.tool()
async def create_task(
    title: str,
    description: str = "",
    due_date: Optional[str] = None,
    priority: str = "medium",
    labels: Optional[list[str]] = None,
) -> dict:
    """Create a new task.

    Args:
        title: The task title
        description: Detailed description of the task
        due_date: Due date in ISO format (YYYY-MM-DD)
        priority: Priority level (low, medium, high, urgent)
        labels: List of labels/tags for the task

    Returns:
        The created task with its ID
    """
    user_id = get_user_id()
    task = await task_service.create_task(
        user_id=user_id,
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
        labels=labels,
    )
    return task.to_dict()


@task_mcp.tool()
async def list_tasks(
    status: str = "all",
    priority: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List tasks with optional filters.

    Args:
        status: Filter by status (all, pending, in_progress, completed, cancelled)
        priority: Filter by priority (low, medium, high, urgent)
        limit: Maximum number of tasks to return

    Returns:
        List of tasks matching the filters
    """
    user_id = get_user_id()
    tasks = await task_service.list_tasks(
        user_id=user_id,
        status=status if status != "all" else None,
        priority=priority,
        limit=limit,
    )
    return [task.to_dict() for task in tasks]


@task_mcp.tool()
async def get_task(task_id: str) -> Optional[dict]:
    """Get a specific task by ID.

    Args:
        task_id: The unique task identifier

    Returns:
        The task details or None if not found
    """
    user_id = get_user_id()
    task = await task_service.get_task(task_id, user_id)
    return task.to_dict() if task else None


@task_mcp.tool()
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    labels: Optional[list[str]] = None,
) -> Optional[dict]:
    """Update an existing task.

    Args:
        task_id: The unique task identifier
        title: New title (optional)
        description: New description (optional)
        due_date: New due date in ISO format (optional)
        priority: New priority level (optional)
        status: New status (optional)
        labels: New labels list (optional)

    Returns:
        The updated task or None if not found
    """
    user_id = get_user_id()

    # Build updates dict with only provided values
    updates = {}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if due_date is not None:
        updates["due_date"] = due_date
    if priority is not None:
        updates["priority"] = priority
    if status is not None:
        updates["status"] = status
    if labels is not None:
        updates["labels"] = labels

    task = await task_service.update_task(task_id, user_id, updates)
    return task.to_dict() if task else None


@task_mcp.tool()
async def complete_task(task_id: str) -> Optional[dict]:
    """Mark a task as completed.

    Args:
        task_id: The unique task identifier

    Returns:
        The updated task or None if not found
    """
    user_id = get_user_id()
    task = await task_service.complete_task(task_id, user_id)
    return task.to_dict() if task else None


@task_mcp.tool()
async def delete_task(task_id: str) -> dict:
    """Delete a task.

    Args:
        task_id: The unique task identifier

    Returns:
        Status of the deletion operation
    """
    user_id = get_user_id()
    success = await task_service.delete_task(task_id, user_id)
    return {"success": success, "task_id": task_id}
