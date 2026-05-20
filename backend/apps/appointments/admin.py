from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'patient_phone', 'clinic', 'appointment_type', 'scheduled_start', 'status', 'whatsapp_sent']
    list_filter = ['status', 'clinic', 'whatsapp_sent', 'appointment_type']
    search_fields = ['patient_name', 'patient_phone', 'patient_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-scheduled_start']
