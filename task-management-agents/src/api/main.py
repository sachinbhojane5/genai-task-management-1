"""FastAPI application entry point for the multi-agent system."""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.iam_middleware import IAMAuthMiddleware
from src.api.routes import router
from src.services.firestore_session import FirestoreSessionService

# Load environment variables
load_dotenv()

# Application metadata
APP_TITLE = "Task Management Agents"
APP_DESCRIPTION = """
Multi-agent AI system for managing tasks, calendar, notes, and email.

Built with Google ADK (Agent Development Kit) and MCP (Model Context Protocol).

## Features
- **Task Management**: Create, update, and track tasks
- **Calendar Integration**: Google Calendar events and scheduling
- **Notes**: Create and search notes
- **Email**: Gmail integration for reading and sending emails

## Authentication
This API uses Google Cloud IAM for authentication.
Include a valid Bearer token in the Authorization header.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("Starting Task Management Agents...")
    print(f"Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")

    yield

    # Shutdown
    print("Shutting down Task Management Agents...")


# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add IAM authentication middleware
app.add_middleware(IAMAuthMiddleware)

# Include custom routes
app.include_router(router)


# ADK integration - using get_fast_api_app pattern
def create_adk_app():
    """
    Create ADK-enhanced FastAPI app.

    This function can be used to create a fully ADK-managed app
    with automatic agent routing.
    """
    try:
        from google.adk.server import get_fast_api_app

        return get_fast_api_app(
            agents_dir="src/agents/orchestrator",
            session_service=FirestoreSessionService(),
            allow_origins=["*"],
            web=True,
            trace_to_cloud=os.getenv("K_SERVICE") is not None,  # Enable in Cloud Run
        )
    except ImportError:
        print("Warning: google-adk not installed, using basic FastAPI app")
        return app


# Health check endpoint (defined here to ensure it's always available)
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": "0.1.0",
    }
