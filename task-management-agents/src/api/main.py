"""FastAPI application entry point for the multi-agent system."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application metadata
APP_TITLE = "Task Management Agents"
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    logger.info("Starting Task Management Agents...")
    logger.info(f"Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'not set')}")
    yield
    logger.info("Shutting down Task Management Agents...")


# Create FastAPI application
app = FastAPI(
    title=APP_TITLE,
    description="Multi-agent AI system for managing tasks, calendar, notes, and email.",
    version=APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint - must work for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Task Management Agents API",
        "docs": "/docs",
        "health": "/health",
    }


# Include routes - wrapped in try/except to handle import errors gracefully
try:
    from src.api.routes import router
    app.include_router(router)
    logger.info("Routes loaded successfully")
except Exception as e:
    logger.error(f"Failed to load routes: {e}")
    # App will still start with basic endpoints
