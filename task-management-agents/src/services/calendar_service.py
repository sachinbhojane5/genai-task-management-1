"""Google Calendar API service."""

from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from .google_auth import GoogleAuthService


@dataclass
class CalendarEvent:
    """Calendar event data model."""

    id: str
    title: str
    start_time: str
    end_time: str
    description: str = ""
    location: str = ""
    attendees: list[str] = None
    html_link: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees or [],
            "html_link": self.html_link,
        }


class CalendarService:
    """Google Calendar API client."""

    def __init__(self, auth_service: Optional[GoogleAuthService] = None):
        self.auth_service = auth_service or GoogleAuthService()

    def _get_service(self, credentials: Credentials):
        """Build the Calendar API service."""
        return build("calendar", "v3", credentials=credentials)

    async def create_event(
        self,
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        location: str = "",
        attendees: Optional[list[str]] = None,
        calendar_id: str = "primary",
    ) -> CalendarEvent:
        """Create a calendar event."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        event_body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC",
            },
        }

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            sendUpdates="all" if attendees else "none",
        ).execute()

        return CalendarEvent(
            id=event["id"],
            title=event.get("summary", ""),
            start_time=event["start"].get("dateTime", event["start"].get("date")),
            end_time=event["end"].get("dateTime", event["end"].get("date")),
            description=event.get("description", ""),
            location=event.get("location", ""),
            attendees=[a["email"] for a in event.get("attendees", [])],
            html_link=event.get("htmlLink", ""),
        )

    async def list_events(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        calendar_id: str = "primary",
        max_results: int = 50,
    ) -> list[CalendarEvent]:
        """List calendar events in a date range."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        # Convert dates to RFC3339 format
        time_min = f"{start_date}T00:00:00Z"
        time_max = f"{end_date}T23:59:59Z"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])

        return [
            CalendarEvent(
                id=event["id"],
                title=event.get("summary", ""),
                start_time=event["start"].get("dateTime", event["start"].get("date")),
                end_time=event["end"].get("dateTime", event["end"].get("date")),
                description=event.get("description", ""),
                location=event.get("location", ""),
                attendees=[a["email"] for a in event.get("attendees", [])],
                html_link=event.get("htmlLink", ""),
            )
            for event in events
        ]

    async def check_availability(
        self,
        user_id: str,
        date: str,
        duration_minutes: int,
        calendar_id: str = "primary",
    ) -> list[dict]:
        """Find available time slots on a given date."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        # Query free/busy for the day
        time_min = f"{date}T08:00:00Z"  # Start from 8 AM
        time_max = f"{date}T18:00:00Z"  # End at 6 PM

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}],
        }

        freebusy = service.freebusy().query(body=body).execute()
        busy_times = freebusy["calendars"][calendar_id].get("busy", [])

        # Find available slots
        available_slots = []
        current_time = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
        end_of_day = datetime.fromisoformat(time_max.replace("Z", "+00:00"))
        duration = timedelta(minutes=duration_minutes)

        busy_periods = [
            (
                datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
            )
            for b in busy_times
        ]

        while current_time + duration <= end_of_day:
            slot_end = current_time + duration
            is_available = True

            for busy_start, busy_end in busy_periods:
                # Check if slot overlaps with busy time
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_available = False
                    current_time = busy_end
                    break

            if is_available:
                available_slots.append({
                    "start": current_time.isoformat(),
                    "end": slot_end.isoformat(),
                })
                current_time = slot_end
            elif current_time == slot_end:
                current_time += timedelta(minutes=30)  # Move forward if stuck

        return available_slots

    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        """Delete a calendar event."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        try:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
            ).execute()
            return True
        except Exception:
            return False

    async def get_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Optional[CalendarEvent]:
        """Get a specific calendar event."""
        credentials = await self.auth_service.get_credentials(user_id)
        if not credentials:
            raise ValueError(f"No credentials found for user {user_id}")

        service = self._get_service(credentials)

        try:
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id,
            ).execute()

            return CalendarEvent(
                id=event["id"],
                title=event.get("summary", ""),
                start_time=event["start"].get("dateTime", event["start"].get("date")),
                end_time=event["end"].get("dateTime", event["end"].get("date")),
                description=event.get("description", ""),
                location=event.get("location", ""),
                attendees=[a["email"] for a in event.get("attendees", [])],
                html_link=event.get("htmlLink", ""),
            )
        except Exception:
            return None
