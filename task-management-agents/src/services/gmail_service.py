"""Gmail API service."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dataclasses import dataclass
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from .google_auth import GoogleAuthService


@dataclass
class Email:
    """Email data model."""

    id: str
    thread_id: str
    subject: str
    sender: str
    to: str
    date: str
    snippet: str
    body: str = ""
    labels: list[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender,
            "to": self.to,
            "date": self.date,
            "snippet": self.snippet,
            "body": self.body,
            "labels": self.labels or [],
        }


class GmailService:
    """Gmail API client."""

    def __init__(self, auth_service: Optional[GoogleAuthService] = None):
        self.auth_service = auth_service or GoogleAuthService()

    def _get_service(self, credentials: Credentials):
        """Build the Gmail API service."""
        return build("gmail", "v1", credentials=credentials)

    def _get_header(self, headers: list, name: str) -> str:
        """Extract header value from message headers."""
        for header in headers:
            if header["name"].lower() == name.lower():
                return header["value"]
        return ""

    def _decode_body(self, payload: dict) -> str:
        """Decode email body from payload."""
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        # Handle multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if part["body"].get("data"):
                        return base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
                elif part["mimeType"] == "text/html":
                    if part["body"].get("data"):
                        return base64.urlsafe_b64decode(
                            part["body"]["data"]
                        ).decode("utf-8")
        return ""

    async def list_emails(
        self,
        user_id: str,
        query: Optional[str] = None,
        max_results: int = 10,
        label_ids: Optional[list[str]] = None,
    ) -> list[Email]:
        """List emails from inbox with optional search query."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        # Build query parameters
        params = {
            "userId": "me",
            "maxResults": max_results,
        }
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        results = service.users().messages().list(**params).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            email = await self.read_email(user_id, msg["id"], include_body=False)
            if email:
                emails.append(email)

        return emails

    async def read_email(
        self,
        user_id: str,
        message_id: str,
        include_body: bool = True,
    ) -> Optional[Email]:
        """Read full email content by ID."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        try:
            message = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full" if include_body else "metadata",
            ).execute()

            headers = message["payload"].get("headers", [])
            body = ""
            if include_body:
                body = self._decode_body(message["payload"])

            return Email(
                id=message["id"],
                thread_id=message["threadId"],
                subject=self._get_header(headers, "Subject"),
                sender=self._get_header(headers, "From"),
                to=self._get_header(headers, "To"),
                date=self._get_header(headers, "Date"),
                snippet=message.get("snippet", ""),
                body=body,
                labels=message.get("labelIds", []),
            )
        except Exception:
            return None

    async def send_email(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        html: bool = False,
    ) -> dict:
        """Send an email via Gmail."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        # Get user's email for From header
        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile["emailAddress"]

        # Create message
        if html:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "html"))
        else:
            message = MIMEText(body)

        message["to"] = to
        message["from"] = sender_email
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        # Encode and send
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        return {
            "id": result["id"],
            "thread_id": result["threadId"],
            "status": "sent",
        }

    async def create_draft(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
    ) -> dict:
        """Create an email draft in Gmail."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        # Get user's email
        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile["emailAddress"]

        # Create message
        message = MIMEText(body)
        message["to"] = to
        message["from"] = sender_email
        message["subject"] = subject
        if cc:
            message["cc"] = cc

        # Encode and create draft
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}},
        ).execute()

        return {
            "id": draft["id"],
            "message_id": draft["message"]["id"],
            "status": "draft",
        }

    async def search_emails(
        self,
        user_id: str,
        query: str,
        max_results: int = 20,
    ) -> list[Email]:
        """Search emails with Gmail query syntax."""
        return await self.list_emails(
            user_id=user_id,
            query=query,
            max_results=max_results,
        )

    async def mark_as_read(
        self,
        user_id: str,
        message_id: str,
    ) -> bool:
        """Mark an email as read."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            return False

        service = self._get_service(credentials)

        try:
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
            return True
        except Exception:
            return False
