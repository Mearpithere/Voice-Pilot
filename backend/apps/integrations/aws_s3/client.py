"""
AWS S3 client for call recording storage.

Recordings flow:
1. Plivo records the call and POSTs the recording URL to our webhook.
2. The recording_tasks.py Celery task downloads it and uploads to S3.
3. We store the S3 key in CallLog.recording_s3_key.
4. The dashboard generates a fresh presigned URL on every playback request
   (avoids URL expiry issues).

S3 key format:  recordings/{clinic_id}/{call_log_id}.mp3
Retention:      90 days (set via S3 lifecycle rule in AWS console)
"""

import logging
import requests
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

PRESIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour — fresh URL generated on each playback


def _s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def upload_recording(clinic_id: str, call_log_id: str, source_url: str, auth: tuple = None) -> str:
    """
    Download a recording from `source_url` and upload it to S3.
    `auth` is an optional (username, password) tuple for authenticated downloads (e.g. Plivo).
    Returns the S3 object key.
    """
    s3_key = f"recordings/{clinic_id}/{call_log_id}.mp3"

    logger.info("Downloading recording from %s", source_url)
    resp = requests.get(source_url, auth=auth, timeout=60, stream=True)
    resp.raise_for_status()

    s3 = _s3_client()
    s3.upload_fileobj(
        resp.raw,
        settings.AWS_STORAGE_BUCKET_NAME,
        s3_key,
        ExtraArgs={"ContentType": "audio/mpeg", "ACL": "private"},
    )
    logger.info("Uploaded recording to S3: %s", s3_key)
    return s3_key


def generate_presigned_url(s3_key: str) -> str:
    """
    Generate a time-limited presigned URL for playback in the dashboard.
    Raises ClientError if the key does not exist.
    """
    s3 = _s3_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": s3_key,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
    )
    return url


def delete_recording(s3_key: str) -> None:
    """Delete a recording from S3 (called by 90-day cleanup task)."""
    s3 = _s3_client()
    try:
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        logger.info("Deleted S3 object: %s", s3_key)
    except ClientError as e:
        logger.warning("S3 delete failed for %s: %s", s3_key, e)


def recording_exists(s3_key: str) -> bool:
    """Check if a recording already exists in S3 (idempotency guard)."""
    s3 = _s3_client()
    try:
        s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError:
        return False
