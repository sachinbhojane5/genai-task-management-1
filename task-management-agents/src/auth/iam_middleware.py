"""Cloud IAM authentication middleware for FastAPI."""

import os
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Google Cloud IAM tokens.

    When deployed on Cloud Run with authentication enabled,
    incoming requests include an Authorization header with
    a Bearer token that can be validated.

    For local development, authentication can be bypassed.
    """

    def __init__(self, app, skip_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/docs", "/openapi.json"]
        self.is_production = os.getenv("K_SERVICE") is not None  # Cloud Run env var

    async def dispatch(self, request: Request, call_next):
        # Skip auth for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Skip auth in development mode
        if not self.is_production:
            # Set default user for development
            request.state.user_id = os.getenv("DEV_USER_ID", "dev_user")
            request.state.user_email = os.getenv("DEV_USER_EMAIL", "dev@localhost")
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid Authorization header"},
            )

        token = auth_header.split(" ")[1]

        try:
            # Validate the token
            user_info = self._validate_token(token)
            request.state.user_id = user_info.get("sub")
            request.state.user_email = user_info.get("email")
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"error": f"Invalid token: {str(e)}"},
            )

        return await call_next(request)

    def _validate_token(self, token: str) -> dict:
        """Validate Google ID token and return user info."""
        # For Cloud Run, validate against Google's token endpoint
        request_adapter = requests.Request()

        # The audience should be the Cloud Run service URL
        # In production, this would be set to your service URL
        audience = os.getenv("CLOUD_RUN_SERVICE_URL", "")

        try:
            # Verify the token
            id_info = id_token.verify_oauth2_token(
                token,
                request_adapter,
                audience=audience if audience else None,
            )
            return id_info
        except ValueError as e:
            raise ValueError(f"Token validation failed: {e}")


def get_current_user(request: Request) -> dict:
    """Helper to get current user from request state."""
    return {
        "user_id": getattr(request.state, "user_id", None),
        "email": getattr(request.state, "user_email", None),
    }
