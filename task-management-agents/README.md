# Task Management Agents

A multi-agent AI system for managing tasks, calendar, notes, and email using Google's Agent Development Kit (ADK) and Model Context Protocol (MCP).

## Features

- **Multi-Agent Architecture**: Orchestrator coordinates specialized sub-agents
- **Task Management**: Create, update, and track tasks with priorities and due dates
- **Calendar Integration**: Google Calendar API for real event management
- **Notes**: Create and search notes with tags
- **Email**: Gmail integration for reading and sending emails
- **API-Based**: FastAPI REST API deployed on Cloud Run
- **Secure**: Google Cloud IAM authentication

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI REST API                           │
│              (Cloud Run + Cloud IAM Authentication)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                           │
│              (Primary LlmAgent - Coordinates)                   │
└─────────────────────────────────────────────────────────────────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Calendar │  │   Task   │  │  Notes   │  │  Gmail   │
│  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## Prerequisites

- Python 3.11+
- Google Cloud Project with:
  - Firestore (Native mode)
  - Google Calendar API
  - Gmail API
  - Cloud Run
  - Vertex AI

## Quick Start

### 1. Clone and Install

```bash
cd task-management-agents
pip install uv
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Google Cloud project details
```

### 3. Google Cloud Setup

```bash
# Set project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable \
  firestore.googleapis.com \
  run.googleapis.com \
  aiplatform.googleapis.com \
  calendar-json.googleapis.com \
  gmail.googleapis.com

# Create Firestore database
gcloud firestore databases create --location=us-central1

# Authenticate
gcloud auth application-default login
```

### 4. Run Locally

```bash
# Run the API server
uv run uvicorn src.api.main:app --reload

# Or use ADK web interface
uv run adk web src/agents/orchestrator
```

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Review budget report", "priority": "high"}'

# List tasks
curl http://localhost:8000/tasks
```

## Deployment

### Deploy to Cloud Run

```bash
# Create service account
gcloud iam service-accounts create task-agent-sa \
  --display-name="Task Management Agent"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:task-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:task-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Deploy
gcloud run deploy task-management-agents \
  --source . \
  --region us-central1 \
  --no-allow-unauthenticated \
  --service-account=task-agent-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Grant access
gcloud run services add-iam-policy-binding task-management-agents \
  --region=us-central1 \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker"
```

## API Endpoints

### Chat
- `POST /chat` - Send message to orchestrator agent

### Tasks
- `GET /tasks` - List tasks
- `POST /tasks` - Create task
- `GET /tasks/{id}` - Get task
- `PATCH /tasks/{id}` - Update task
- `POST /tasks/{id}/complete` - Complete task
- `DELETE /tasks/{id}` - Delete task

### Notes
- `GET /notes` - List notes
- `POST /notes` - Create note
- `GET /notes/search?q=query` - Search notes

### Calendar
- `GET /events` - List calendar events
- `GET /events/today` - Get today's events

### Email
- `GET /emails` - List emails
- `GET /emails/unread` - Get unread emails

### OAuth
- `GET /oauth/authorize` - Start Google OAuth flow
- `GET /oauth/callback` - OAuth callback
- `GET /oauth/status` - Check connection status

## Example Workflows

### Multi-Step Task Creation

```
User: "Schedule a meeting for tomorrow at 2pm about Q2 planning, 
       create a task to prepare the deck, and save notes about key topics"

Orchestrator:
1. calendar_agent → Creates Google Calendar event
2. task_agent → Creates task "Prepare Q2 planning deck"
3. notes_agent → Creates note with key topics
```

### Email to Task Pipeline

```
User: "Check my emails about the Johnson project and create tasks for action items"

Orchestrator:
1. gmail_agent → Searches emails for "Johnson project"
2. gmail_agent → Reads relevant emails
3. task_agent → Creates tasks from action items
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Project Structure

```
task-management-agents/
├── src/
│   ├── agents/           # ADK agents
│   │   ├── orchestrator/ # Primary coordinator
│   │   ├── task_agent/
│   │   ├── calendar_agent/
│   │   ├── notes_agent/
│   │   └── gmail_agent/
│   ├── mcp_servers/      # MCP tool servers
│   ├── services/         # Business logic
│   ├── auth/             # Authentication
│   └── api/              # FastAPI app
├── tests/
├── pyproject.toml
├── Dockerfile
└── README.md
```

## License

MIT
