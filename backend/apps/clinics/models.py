import uuid
from django.db import models
from django.contrib.auth.models import User


class Clinic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=100)

    # Twilio / telephony
    phone_number = models.CharField(max_length=20, unique=True, blank=True)
    twilio_phone_sid = models.CharField(max_length=64, blank=True)

    # VAPI
    vapi_assistant_id = models.CharField(max_length=64, blank=True)
    vapi_phone_number_id = models.CharField(max_length=64, blank=True)

    # Integrations
    google_calendar_id = models.CharField(max_length=255, blank=True)
    airtable_table_name = models.CharField(max_length=255, blank=True)

    # Schedule & personalisation
    timezone = models.CharField(max_length=64, default='Asia/Kolkata')
    business_hours_start = models.TimeField(default='09:00')
    business_hours_end = models.TimeField(default='18:00')
    after_hours_message = models.TextField(
        blank=True,
        default='Thank you for calling. Our clinic is currently closed. Please call back during business hours or leave a message.'
    )
    custom_faqs = models.JSONField(default=list, blank=True)  # [{q, a}, ...]

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ClinicUser(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('staff', 'Staff')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clinic_profile')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f'{self.user.username} – {self.clinic.name} ({self.role})'
