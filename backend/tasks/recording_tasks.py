"""
Call recording tasks.
Downloads recording from Plivo and uploads to S3 for permanent storage.
"""

import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300,
             name='tasks.recording_tasks.upload_recording_to_s3')
def upload_recording_to_s3(self, call_log_id: str, source_url: str):
    """
    Download recording from Plivo and upload to S3.
    Updates CallLog.recording_url with the S3 presigned URL.
    """
    from apps.calls.models import CallLog
    from apps.integrations.aws_s3.client import (
        upload_recording,
        generate_presigned_url,
        recording_exists,
    )

    try:
        call_log = CallLog.objects.select_related('clinic').get(id=call_log_id)
    except CallLog.DoesNotExist:
        logger.warning("CallLog %s not found for S3 upload", call_log_id)
        return

    s3_key = f"recordings/{call_log.clinic.id}/{call_log_id}.mp3"

    # Idempotency — skip if already uploaded
    if call_log.recording_s3_key or recording_exists(s3_key):
        logger.info("Recording already in S3 for call %s, skipping", call_log_id)
        if not call_log.recording_url:
            call_log.recording_url = generate_presigned_url(s3_key)
            call_log.save(update_fields=['recording_url'])
        return

    try:
        # Plivo recordings require auth to download
        auth = (settings.PLIVO_AUTH_ID, settings.PLIVO_AUTH_TOKEN)
        uploaded_key = upload_recording(
            clinic_id=str(call_log.clinic.id),
            call_log_id=call_log_id,
            source_url=source_url,
            auth=auth,
        )
        presigned_url = generate_presigned_url(uploaded_key)

        call_log.recording_s3_key = uploaded_key
        call_log.recording_url = presigned_url
        call_log.save(update_fields=['recording_s3_key', 'recording_url'])
        logger.info("Recording uploaded to S3 for call %s: %s", call_log_id, uploaded_key)

    except Exception as exc:
        logger.error("S3 upload failed for call %s: %s", call_log_id, exc)
        raise self.retry(exc=exc)


@shared_task(name='tasks.recording_tasks.cleanup_old_recordings')
def cleanup_old_recordings():
    """
    Daily task — deletes S3 recordings older than 90 days and clears the URL from DB.
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.calls.models import CallLog
    from apps.integrations.aws_s3.client import delete_recording

    cutoff = timezone.now() - timedelta(days=90)
    old_calls = CallLog.objects.filter(
        recording_s3_key__isnull=False,
        created_at__lt=cutoff,
    ).exclude(recording_s3_key='')

    count = 0
    for call in old_calls:
        try:
            delete_recording(call.recording_s3_key)
            call.recording_s3_key = ''
            call.recording_url = ''
            call.save(update_fields=['recording_s3_key', 'recording_url'])
            count += 1
        except Exception as e:
            logger.warning("Could not delete recording %s: %s", call.recording_s3_key, e)

    logger.info("Cleaned up %d old recordings from S3", count)
