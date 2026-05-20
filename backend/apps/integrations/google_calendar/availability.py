"""
Availability logic — returns open appointment slots for a given date.

Algorithm:
1. Parse the requested date in the clinic's timezone.
2. Fetch all events from Google Calendar for that day.
3. Generate all possible slots between business_hours_start and business_hours_end
   at SLOT_DURATION_MINUTES intervals.
4. Filter out any slot that overlaps an existing event.
5. Return a list of human-readable time strings.
"""

import logging
from datetime import datetime, timedelta, date as date_type

import pytz

from apps.clinics.models import Clinic
from .client import GoogleCalendarClient

logger = logging.getLogger(__name__)

SLOT_DURATION_MINUTES = 30  # default appointment slot length


def get_available_slots(
    clinic: Clinic,
    date_str: str,
    duration_minutes: int = SLOT_DURATION_MINUTES,
) -> list[str]:
    """
    Returns a list of available time strings for `date_str` (YYYY-MM-DD format).
    Times are in the clinic's local timezone, formatted as "HH:MM" (24-hour).

    Returns empty list if no slots are available or calendar is not configured.
    """
    if not clinic.google_calendar_id:
        logger.warning("Clinic %s has no Google Calendar configured", clinic.slug)
        return []

    try:
        tz = pytz.timezone(clinic.timezone)
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Build day boundaries in clinic timezone
        day_start = tz.localize(
            datetime.combine(target_date, clinic.business_hours_start)
        )
        day_end = tz.localize(
            datetime.combine(target_date, clinic.business_hours_end)
        )

        # Fetch existing events
        cal = GoogleCalendarClient(clinic.google_calendar_id)
        events = cal.list_events(time_min=day_start, time_max=day_end)

        # Parse booked intervals (start, end) in UTC for consistent comparison
        booked = []
        for ev in events:
            ev_start_raw = ev.get("start", {}).get("dateTime")
            ev_end_raw = ev.get("end", {}).get("dateTime")
            if ev_start_raw and ev_end_raw:
                ev_start = datetime.fromisoformat(ev_start_raw).astimezone(pytz.utc)
                ev_end = datetime.fromisoformat(ev_end_raw).astimezone(pytz.utc)
                booked.append((ev_start, ev_end))

        # Generate candidate slots
        available = []
        current = day_start
        slot_delta = timedelta(minutes=duration_minutes)

        while current + slot_delta <= day_end:
            slot_end = current + slot_delta
            slot_utc_start = current.astimezone(pytz.utc)
            slot_utc_end = slot_end.astimezone(pytz.utc)

            # Check overlap with any booked event
            overlaps = any(
                slot_utc_start < b_end and slot_utc_end > b_start
                for b_start, b_end in booked
            )
            if not overlaps:
                available.append(current.strftime("%H:%M"))

            current = slot_end

        return available

    except Exception as e:
        logger.error("get_available_slots failed for clinic %s on %s: %s", clinic.slug, date_str, e)
        return []
