import uuid
from django.db import models
from apps.clinics.models import Clinic
from apps.calls.models import CallLog


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='appointments')
    call_log = models.ForeignKey(
        CallLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments'
    )

    # Patient details
    patient_name = models.CharField(max_length=255)
    patient_phone = models.CharField(max_length=20)
    patient_email = models.EmailField(blank=True)

    # Appointment details
    appointment_type = models.CharField(max_length=100, default='General Consultation')
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Google Calendar
    google_event_id = models.CharField(max_length=255, blank=True)
    google_calendar_link = models.URLField(blank=True)

    # WhatsApp confirmation
    whatsapp_sent = models.BooleanField(default=False)
    whatsapp_message_sid = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_start']

    def __str__(self):
        return f'{self.patient_name} – {self.appointment_type} on {self.scheduled_start:%Y-%m-%d %H:%M}'
