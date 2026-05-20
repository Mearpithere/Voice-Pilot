import uuid
from django.db import models
from apps.clinics.models import Clinic


class CallLog(models.Model):
    DIRECTION_CHOICES = [('inbound', 'Inbound'), ('outbound', 'Outbound')]
    OUTCOME_CHOICES = [
        ('booked', 'Appointment Booked'),
        ('faq', 'FAQ Answered'),
        ('missed', 'Missed'),
        ('callback_scheduled', 'Callback Scheduled'),
        ('voicemail', 'Voicemail'),
        ('transferred', 'Transferred to Staff'),
        ('cancelled', 'Appointment Cancelled'),
        ('unknown', 'Unknown'),
    ]
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='calls')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='inbound')
    caller_number = models.CharField(max_length=20)
    caller_name = models.CharField(max_length=255, blank=True)

    # External IDs
    twilio_call_sid = models.CharField(max_length=64, blank=True, db_index=True)
    vapi_call_id = models.CharField(max_length=64, blank=True, db_index=True)

    # Call outcome
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES, default='unknown')
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Recording & transcript
    recording_url = models.URLField(blank=True)
    recording_s3_key = models.CharField(max_length=512, blank=True)
    transcript = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # CRM sync
    crm_synced = models.BooleanField(default=False)
    crm_record_id = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.direction} call from {self.caller_number} [{self.outcome}]'


class MissedCallQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('attempted', 'Attempted'),
        ('reached', 'Reached'),
        ('exhausted', 'Exhausted'),
        ('opted_out', 'Opted Out'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='missed_call_queue')
    caller_number = models.CharField(max_length=20)
    original_call = models.ForeignKey(
        CallLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='callback_queue'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempt_count = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Missed call callback: {self.caller_number} ({self.status})'
