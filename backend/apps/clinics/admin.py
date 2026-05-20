from django.contrib import admin
from .models import Clinic, ClinicUser


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'phone_number', 'timezone', 'is_active', 'created_at']
    list_filter = ['is_active', 'timezone']
    search_fields = ['name', 'phone_number', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('id', 'name', 'slug', 'is_active')}),
        ('Telephony', {'fields': ('phone_number', 'twilio_phone_sid', 'vapi_assistant_id', 'vapi_phone_number_id')}),
        ('Integrations', {'fields': ('google_calendar_id', 'airtable_table_name')}),
        ('Schedule', {'fields': ('timezone', 'business_hours_start', 'business_hours_end', 'after_hours_message')}),
        ('FAQs', {'fields': ('custom_faqs',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(ClinicUser)
class ClinicUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'clinic', 'role']
    list_filter = ['role', 'clinic']
    search_fields = ['user__username', 'clinic__name']
