"""
Airtable CRM sync tasks.
Called after every completed call to push call + appointment data to Airtable.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=120,
             name='tasks.crm_tasks.sync_call_to_airtable')
def sync_call_to_airtable(self, call_log_id: str):
    """
    Sync a single CallLog (and its linked Appointment if any) to Airtable.
    Idempotent — the Airtable client uses upsert keyed on Call ID.
    """
    from apps.calls.models import CallLog
    from apps.integrations.airtable.client import AirtableClient

    try:
        call_log = CallLog.objects.select_related('clinic').get(id=call_log_id)
    except CallLog.DoesNotExist:
        logger.warning("CallLog %s not found for Airtable sync", call_log_id)
        return

    clinic = call_log.clinic
    if not clinic.airtable_table_name:
        logger.info("Clinic %s has no Airtable table configured, skipping sync", clinic.slug)
        return

    # Get linked appointment if any
    appointment = call_log.appointments.order_by('-created_at').first()

    try:
        client = AirtableClient(clinic.airtable_table_name)
        record_id = client.upsert_call_record(call_log, appointment)
        call_log.crm_synced = True
        call_log.crm_record_id = record_id
        call_log.save(update_fields=['crm_synced', 'crm_record_id'])
        logger.info("Synced call %s to Airtable record %s", call_log_id, record_id)
    except Exception as exc:
        logger.error("Airtable sync failed for call %s: %s", call_log_id, exc)
        raise self.retry(exc=exc)


@shared_task(name='tasks.crm_tasks.sync_unsynced_calls')
def sync_unsynced_calls():
    """
    Hourly sweep — picks up any calls that failed to sync on the first attempt.
    """
    from apps.calls.models import CallLog

    unsynced = CallLog.objects.filter(
        crm_synced=False,
        status='completed',
        clinic__airtable_table_name__isnull=False,
    ).exclude(clinic__airtable_table_name='').order_by('-created_at')[:50]

    count = 0
    for call in unsynced:
        sync_call_to_airtable.delay(str(call.id))
        count += 1

    if count:
        logger.info("Queued %d unsynced calls for Airtable retry", count)
