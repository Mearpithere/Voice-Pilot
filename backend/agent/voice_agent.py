"""
VoicePilot LiveKit voice agent.

Pipeline: Caller audio → Deepgram STT → Gemini 2.0 Flash → Cartesia TTS → Caller audio

Each incoming call gets its own Agent instance. The clinic context is passed in
via the LiveKit room metadata (clinic slug) set by the Django webhook when the
call arrives.
"""

import logging
import os
import django
from typing import Annotated

# Bootstrap Django so we can use ORM models inside the agent process
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voicepilot.settings.development')
django.setup()

from livekit.agents import Agent, function_tool, RunContext
from django.conf import settings

from apps.clinics.models import Clinic
from apps.calls.models import CallLog
from apps.integrations.google_calendar.availability import get_available_slots
from apps.integrations.google_calendar.client import GoogleCalendarClient
from apps.appointments.models import Appointment
from .prompts import build_system_prompt, build_callback_prompt

logger = logging.getLogger(__name__)


class VoicePilotAgent(Agent):
    """
    One instance per call. Holds clinic context and the active CallLog.
    Tools are defined as async methods decorated with @function_tool —
    Gemini sees them as function-calling tools automatically.
    """

    def __init__(self, clinic: Clinic, call_log: CallLog, is_callback: bool = False):
        prompt = build_callback_prompt(clinic) if is_callback else build_system_prompt(clinic)
        super().__init__(instructions=prompt)
        self.clinic = clinic
        self.call_log = call_log

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    async def on_enter(self) -> None:
        await self.session.say(
            f"Hello, thank you for calling {self.clinic.name}. "
            "I'm Maya, your AI assistant. How can I help you today?"
        )

    # ── Tools ─────────────────────────────────────────────────────────────────

    @function_tool
    async def check_availability(
        self,
        context: RunContext,
        date: Annotated[str, "Date to check in YYYY-MM-DD format"],
        appointment_type: Annotated[str, "Type of appointment, e.g. General Checkup, Dental Cleaning"],
    ) -> str:
        """Check available appointment slots for a given date."""
        try:
            slots = get_available_slots(self.clinic, date)
            if not slots:
                return f"There are no available slots on {date}. Would you like to try another date?"
            slot_list = ", ".join(slots[:6])  # Read at most 6 slots aloud
            return f"Available times on {date}: {slot_list}. Which time works for you?"
        except Exception as e:
            logger.error("check_availability failed: %s", e)
            return "I'm having trouble checking the schedule right now. Please hold a moment."

    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        patient_name: Annotated[str, "Full name of the patient"],
        patient_phone: Annotated[str, "Patient phone number with country code"],
        appointment_type: Annotated[str, "Type of appointment"],
        date: Annotated[str, "Date in YYYY-MM-DD format"],
        time: Annotated[str, "Time in HH:MM 24-hour format"],
        duration_minutes: Annotated[int, "Duration in minutes, default 30"] = 30,
        patient_email: Annotated[str, "Patient email address, optional"] = "",
    ) -> str:
        """Book an appointment slot for the patient on Google Calendar."""
        from datetime import datetime, timedelta
        import pytz

        try:
            tz = pytz.timezone(self.clinic.timezone)
            start_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            start_dt = tz.localize(start_naive)
            end_dt = start_dt + timedelta(minutes=duration_minutes)

            cal = GoogleCalendarClient(self.clinic.google_calendar_id)
            event = cal.create_event(
                summary=f"{appointment_type} — {patient_name}",
                start=start_dt,
                end=end_dt,
                attendee_email=patient_email or None,
                description=f"Booked via VoicePilot AI. Patient phone: {patient_phone}",
            )

            appointment = Appointment.objects.create(
                clinic=self.clinic,
                call_log=self.call_log,
                patient_name=patient_name,
                patient_phone=patient_phone,
                patient_email=patient_email,
                appointment_type=appointment_type,
                scheduled_start=start_dt,
                scheduled_end=end_dt,
                google_event_id=event.get("id", ""),
                google_calendar_link=event.get("htmlLink", ""),
                status="scheduled",
            )

            # Update call log outcome
            self.call_log.outcome = "booked"
            self.call_log.save(update_fields=["outcome"])

            # Enqueue WhatsApp confirmation
            if patient_phone:
                from tasks.whatsapp_tasks import send_whatsapp_confirmation
                send_whatsapp_confirmation.delay(str(appointment.id))

            # Human-friendly confirmation
            from datetime import datetime as dt
            pretty_date = start_dt.strftime("%A, %B %-d")
            pretty_time = start_dt.strftime("%-I:%M %p")
            return (
                f"All done! I've booked a {appointment_type} for {patient_name} "
                f"on {pretty_date} at {pretty_time}. "
                f"You'll receive a WhatsApp confirmation shortly. Is there anything else I can help with?"
            )

        except Exception as e:
            logger.error("book_appointment failed: %s", e)
            return "I'm sorry, I wasn't able to complete the booking. Please call back or ask me to try again."

    @function_tool
    async def cancel_appointment(
        self,
        context: RunContext,
        patient_phone: Annotated[str, "Patient phone number to look up existing appointment"],
    ) -> str:
        """Cancel the most recent upcoming appointment for the patient."""
        from django.utils import timezone

        try:
            appt = (
                Appointment.objects
                .filter(
                    clinic=self.clinic,
                    patient_phone=patient_phone,
                    status="scheduled",
                    scheduled_start__gte=timezone.now(),
                )
                .order_by("scheduled_start")
                .first()
            )
            if not appt:
                return "I couldn't find an upcoming appointment for that phone number. Could you double-check the number?"

            # Remove from Google Calendar
            if appt.google_event_id:
                try:
                    cal = GoogleCalendarClient(self.clinic.google_calendar_id)
                    cal.delete_event(appt.google_event_id)
                except Exception as cal_err:
                    logger.warning("Google Calendar delete failed: %s", cal_err)

            appt.status = "cancelled"
            appt.save(update_fields=["status"])
            self.call_log.outcome = "cancelled"
            self.call_log.save(update_fields=["outcome"])

            pretty_date = appt.scheduled_start.strftime("%A, %B %-d")
            pretty_time = appt.scheduled_start.strftime("%-I:%M %p")
            return (
                f"Done — I've cancelled the {appt.appointment_type} appointment on "
                f"{pretty_date} at {pretty_time}. Would you like to reschedule?"
            )

        except Exception as e:
            logger.error("cancel_appointment failed: %s", e)
            return "I wasn't able to cancel that appointment right now. Please call back and we'll sort it out."

    @function_tool
    async def transfer_to_human(
        self,
        context: RunContext,
        reason: Annotated[str, "Brief reason for transfer"] = "Patient requested",
    ) -> str:
        """Transfer the call to a human staff member."""
        self.call_log.outcome = "transferred"
        self.call_log.save(update_fields=["outcome"])
        # Signal to the room that a transfer is needed — the webhook handler
        # picks this up and initiates a Plivo blind transfer to the clinic's
        # staff number.
        await context.room.local_participant.publish_data(
            b'{"event": "transfer_requested"}',
            reliable=True,
        )
        return "Please hold for just a moment while I connect you to our staff."

    @function_tool
    async def opt_out_of_callbacks(
        self,
        context: RunContext,
    ) -> str:
        """Mark the patient as opted out of future callback attempts."""
        from apps.calls.models import MissedCallQueue
        MissedCallQueue.objects.filter(
            clinic=self.clinic,
            caller_number=self.call_log.caller_number,
            status__in=["pending", "attempted"],
        ).update(status="opted_out")
        return "No problem — I've removed you from our callback list. Have a great day!"
