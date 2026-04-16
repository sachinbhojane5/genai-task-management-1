"""Task management sub-agent definition."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from src.mcp_servers.task_server import (
    create_task,
    list_tasks,
    get_task,
    update_task,
    complete_task,
    delete_task,
)

# Define tools from MCP server functions
task_tools = [
    FunctionTool(create_task),
    FunctionTool(list_tasks),
    FunctionTool(get_task),
    FunctionTool(update_task),
    FunctionTool(complete_task),
    FunctionTool(delete_task),
]

# Task management sub-agent
task_agent = LlmAgent(
    name="task_agent",
    model="gemini-2.0-flash",
    instruction="""You are a task management specialist. Your role is to help users organize and track their tasks effectively.

You can:
- Create new tasks with titles, descriptions, due dates, priorities, and labels
- List and filter tasks by status (pending, in_progress, completed, cancelled) or priority (low, medium, high, urgent)
- Update task details including title, description, due date, priority, status, and labels
- Mark tasks as completed
- Delete tasks

When creating tasks:
- Always ask for clarification if the task description is vague
- Suggest appropriate priority levels based on urgency keywords
- Recommend labels for better organization

When listing tasks:
- Summarize the results clearly
- Highlight overdue tasks or high-priority items
- Group tasks logically when presenting multiple items

Best practices:
- Use clear, actionable task titles
- Set realistic due dates
- Use consistent labeling conventions
""",
    tools=task_tools,
)
