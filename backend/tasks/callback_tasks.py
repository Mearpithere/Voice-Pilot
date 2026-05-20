"""
Missed-call auto-callback tasks.

Flow:
1. PlivoCallStatusView detects no-answer → creates MissedCallQueue → calls schedule_callback
2. schedule_callback fires after countdown, initiates outbound Plivo call
3. Plivo calls the patient → PlivoOutboundAnswerView → LiveKit agent (callback prompt)
4. On call end: queue entry marked 'reached' or re-enqueued for next attempt
5. After max_attempts: status set to 'exhausted'
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

RETRY_INTERVALS_MINUTES = [5, 30, 120]   # gaps between attempts 1, 2, 3


@shared_task(bind=True, max_retries=0, name='tasks.callback_tasks.schedule_callback')
def schedule_callback(self, missed_call_queue_id: str):
    """
    Attempt one outbound callback for a MissedCallQueue entry.
    Re-enqueues itself with a longer delay if the attempt fails or goes unanswered.
    """
    from apps.calls.models import MissedCallQueue
    from apps.integrations.plivo_client import client as plivo

    try:
        entry = MissedCallQueue.objects.select_related('clinic').get(id=missed_call_queue_id)
    except MissedCallQueue.DoesNotExist:
        logger.warning("MissedCallQueue %s not found, skipping", missed_call_queue_id)
        return

    if entry.status in ('reached', 'exhausted', 'opted_out'):
        return

    if entry.attempt_count >= entry.max_attempts:
        entry.status = 'exhausted'
        entry.save(update_fields=['status'])
        logger.info("Callback exhausted for %s after %d attempts", entry.caller_number, entry.attempt_count)
        return

    clinic = entry.clinic
    base_url = settings.PLIVO_WEBHOOK_BASE_URL

    try:
        plivo.make_outbound_call(
            from_number=clinic.phone_number,
            to_number=entry.caller_number,
            answer_url=f"{base_url}/api/webhooks/plivo/outbound/",
            hangup_url=f"{base_url}/api/webhooks/plivo/status/",
        )
        entry.attempt_count += 1
        entry.status = 'attempted'
        entry.last_attempt_at = timezone.now()

        # Schedule next retry if we haven't hit the limit
        if entry.attempt_count < entry.max_attempts:
            delay_minutes = RETRY_INTERVALS_MINUTES[
                min(entry.attempt_count, len(RETRY_INTERVALS_MINUTES) - 1)
            ]
            next_attempt = timezone.now() + timedelta(minutes=delay_minutes)
            entry.next_attempt_at = next_attempt
            entry.save(update_fields=['attempt_count', 'status', 'last_attempt_at', 'next_attempt_at'])

            schedule_callback.apply_async(
                args=[missed_call_queue_id],
                countdown=delay_minutes * 60,
            )
            logger.info(
                "Callback attempt %d for %s, next retry in %d min",
                entry.attempt_count, entry.caller_number, delay_minutes
            )
        else:
            entry.save(update_fields=['attempt_count', 'status', 'last_attempt_at'])

    except Exception as e:
        logger.error("Outbound call failed for %s: %s", entry.caller_number, e)
        entry.save(update_fields=['attempt_count', 'status', 'last_attempt_at'])


@shared_task(name='tasks.callback_tasks.process_missed_calls_queue')
def process_missed_calls_queue():
    """
    Periodic task (every 15 min via Celery Beat).
    Picks up any pending entries whose next_attempt_at is due.
    Safety net in case the initial schedule_callback task was dropped.
    """
    from apps.calls.models import MissedCallQueue

    due = MissedCallQueue.objects.filter(
        status__in=['pending', 'attempted'],
        next_attempt_at__lte=timezone.now(),
    ).exclude(attempt_count__gte=3)

    count = 0
    for entry in due:
        schedule_callback.delay(str(entry.id))
        count += 1

    if count:
        logger.info("Queued %d pending callbacks from sweep", count)
