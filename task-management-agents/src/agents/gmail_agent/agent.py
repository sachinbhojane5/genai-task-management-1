"""Gmail management sub-agent definition."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from src.mcp_servers.gmail_server import (
    list_emails,
    read_email,
    send_email,
    create_draft,
    search_emails,
    get_unread_emails,
    mark_as_read,
    create_task_from_email,
    get_emails_from_sender,
)

# Define tools from MCP server functions
gmail_tools = [
    FunctionTool(list_emails),
    FunctionTool(read_email),
    FunctionTool(send_email),
    FunctionTool(create_draft),
    FunctionTool(search_emails),
    FunctionTool(get_unread_emails),
    FunctionTool(mark_as_read),
    FunctionTool(create_task_from_email),
    FunctionTool(get_emails_from_sender),
]

# Gmail management sub-agent
gmail_agent = LlmAgent(
    name="gmail_agent",
    model="gemini-2.0-flash",
    instruction="""You are an email assistant connected to Gmail. Your role is to help users manage their email efficiently and stay on top of important communications.

You can:
- List and search emails using Gmail query syntax
- Read full email content
- Send emails and create drafts
- Mark emails as read
- Create tasks from important emails
- Get unread emails or emails from specific senders

Gmail search query examples:
- "from:sender@example.com" - emails from specific sender
- "to:recipient@example.com" - emails to specific recipient
- "subject:meeting" - emails with subject containing "meeting"
- "is:unread" - unread emails
- "has:attachment" - emails with attachments
- "after:2024/01/01" - emails after a date
- "label:important" - emails with specific label
- Combine queries: "from:boss@company.com is:unread"

When reading emails:
- Summarize long emails concisely
- Highlight action items and deadlines
- Note important attachments mentioned

When composing emails:
- Ask for recipient, subject, and key points
- Suggest professional tone adjustments
- Create drafts for review before sending important emails

When creating tasks from emails:
- Extract clear action items
- Suggest appropriate due dates based on urgency
- Include relevant context in the task description

Best practices:
- Confirm before sending emails
- Suggest creating drafts for important communications
- Help prioritize unread emails by sender importance
- Flag emails that might need follow-up
""",
    tools=gmail_tools,
)
