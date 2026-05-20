"""
Google Calendar API client.

Uses a service account (JSON key file) that has been granted access
to each clinic's calendar. The clinic owner shares their Google Calendar
with the service account email during onboarding.

Setup steps for a new clinic:
1. Download service account JSON from Google Cloud Console.
2. Set GOOGLE_CALENDAR_CREDENTIALS_JSON path in .env
3. In Google Calendar, share the clinic's calendar with the
   service account email (edit permission).
4. Set clinic.google_calendar_id to that calendar's ID.
"""

import logging
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _build_service(calendar_id: str = None):
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CALENDAR_CREDENTIALS_JSON,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


class GoogleCalendarClient:
    def __init__(self, calendar_id: str):
        if not calendar_id:
            raise ValueError("calendar_id is required")
        self.calendar_id = calendar_id
        self.service = _build_service()

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        attendee_email: str = None,
        description: str = "",
    ) -> dict:
        """
        Create a calendar event and return the full event dict
        (contains 'id' and 'htmlLink').
        """
        body = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": str(start.tzinfo),
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": str(end.tzinfo),
            },
        }
        if attendee_email:
            body["attendees"] = [{"email": attendee_email}]

        event = (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=body, sendUpdates="all")
            .execute()
        )
        logger.info("Created calendar event: %s (%s)", summary, event.get("id"))
        return event

    def delete_event(self, event_id: str) -> None:
        """Delete a calendar event by ID."""
        self.service.events().delete(
            calendarId=self.calendar_id,
            eventId=event_id,
            sendUpdates="all",
        ).execute()
        logger.info("Deleted calendar event: %s", event_id)

    def list_events(self, time_min: datetime, time_max: datetime) -> list:
        """
        Return all events between time_min and time_max.
        Used by availability logic to find booked slots.
        """
        result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])
