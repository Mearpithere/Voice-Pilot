from rest_framework import serializers
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'clinic', 'clinic_name', 'call_log',
            'patient_name', 'patient_phone', 'patient_email',
            'appointment_type', 'scheduled_start', 'scheduled_end',
            'status', 'status_display', 'notes',
            'google_event_id', 'google_calendar_link',
            'whatsapp_sent',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'clinic_name', 'status_display',
            'google_event_id', 'google_calendar_link',
            'whatsapp_sent', 'created_at', 'updated_at',
        ]


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Only status and notes are patchable by staff."""
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
