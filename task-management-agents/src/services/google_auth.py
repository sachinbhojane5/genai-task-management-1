"""Google OAuth and service account authentication service."""

import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.cloud import firestore

# OAuth scopes for Google Workspace APIs
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GoogleAuthService:
    """Handles Google OAuth 2.0 and service account authentication."""

    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client_id = os.getenv("OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET")
        self.app_url = os.getenv("APP_URL", "http://localhost:8080")
        self._db: Optional[firestore.AsyncClient] = None

    @property
    def db(self) -> firestore.AsyncClient:
        if self._db is None:
            self._db = firestore.AsyncClient(project=self.project_id)
        return self._db

    def create_oauth_flow(self, state: Optional[str] = None) -> Flow:
        """Create OAuth 2.0 flow for user authentication."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{self.app_url}/oauth/callback"],
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=state,
        )
        flow.redirect_uri = f"{self.app_url}/oauth/callback"
        return flow

    def get_authorization_url(self, user_id: str) -> tuple[str, str]:
        """Generate OAuth authorization URL for a user."""
        flow = self.create_oauth_flow(state=user_id)
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url, state

    async def exchange_code(self, code: str, user_id: str) -> Credentials:
        """Exchange authorization code for credentials."""
        flow = self.create_oauth_flow(state=user_id)
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store credentials in Firestore
        await self._store_credentials(user_id, credentials)
        return credentials

    async def _store_credentials(self, user_id: str, credentials: Credentials) -> None:
        """Store user credentials in Firestore."""
        cred_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        await self.db.collection("user_credentials").document(user_id).set(cred_data)

    async def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Retrieve and refresh user credentials from Firestore."""
        doc = await self.db.collection("user_credentials").document(user_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        credentials = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id", self.client_id),
            client_secret=data.get("client_secret", self.client_secret),
            scopes=data.get("scopes", SCOPES),
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            await self._store_credentials(user_id, credentials)

        return credentials

    @staticmethod
    def get_service_account_credentials() -> service_account.Credentials:
        """Get service account credentials for server-to-server auth."""
        # Uses Application Default Credentials
        credentials, _ = service_account.Credentials.from_service_account_info(
            info={},  # Will use ADC
            scopes=SCOPES,
        )
        return credentials
