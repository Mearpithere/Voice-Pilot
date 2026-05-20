"""
Airtable CRM client.

Each clinic has its own table (named by clinic.airtable_table_name) inside
a shared Airtable base. Each row = one call record with patient + outcome info.

Expected Airtable table columns:
  Patient Name        | Single line text
  Patient Phone       | Phone number
  Call Date           | Date
  Call Direction      | Single line text
  Call Duration (sec) | Number
  Call Outcome        | Single select
  Appointment Date    | Date
  Appointment Type    | Single line text
  Summary             | Long text
  Recording URL       | URL
  Call ID             | Single line text  (our internal UUID — used for upserts)
"""

import logging
from pyairtable import Api
from django.conf import settings

logger = logging.getLogger(__name__)


class AirtableClient:
    def __init__(self, table_name: str):
        if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID:
            raise RuntimeError("Airtable credentials not configured")
        api = Api(settings.AIRTABLE_API_KEY)
        self.table = api.table(settings.AIRTABLE_BASE_ID, table_name)

    def upsert_call_record(self, call_log, appointment=None) -> str:
        """
        Create or update an Airtable record for this call.
        Uses 'Call ID' field as the unique key so re-runs are idempotent.
        Returns the Airtable record ID.
        """
        fields = {
            "Call ID": str(call_log.id),
            "Patient Name": call_log.caller_name or "Unknown",
            "Patient Phone": call_log.caller_number,
            "Call Date": call_log.started_at.date().isoformat() if call_log.started_at else "",
            "Call Direction": call_log.direction.capitalize(),
            "Call Duration (sec)": call_log.duration_seconds or 0,
            "Call Outcome": call_log.get_outcome_display(),
            "Summary": call_log.summary or "",
            "Recording URL": call_log.recording_url or "",
        }

        if appointment:
            fields["Appointment Date"] = appointment.scheduled_start.isoformat()
            fields["Appointment Type"] = appointment.appointment_type
            fields["Patient Name"] = appointment.patient_name

        # Upsert: match on Call ID field
        result = self.table.upsert(
            [{"fields": fields}],
            key_fields=["Call ID"],
        )

        records = result.get("createdRecords", []) + result.get("updatedRecords", [])
        record_id = records[0] if records else ""
        logger.info("Airtable upsert for call %s → record %s", call_log.id, record_id)
        return record_id

    def find_patient(self, phone_number: str) -> dict | None:
        """
        Look up a patient by phone number.
        Returns the most recent record or None if not found.
        Used by the agent to personalise the greeting for returning patients.
        """
        formula = f"{{Patient Phone}}='{phone_number}'"
        records = self.table.all(formula=formula, sort=["-Call Date"], max_records=1)
        if records:
            return records[0]["fields"]
        return None
