from django.contrib import admin
from .models import CallLog, MissedCallQueue


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ['caller_number', 'clinic', 'direction', 'status', 'outcome', 'duration_seconds', 'created_at']
    list_filter = ['direction', 'status', 'outcome', 'clinic', 'crm_synced']
    search_fields = ['caller_number', 'caller_name', 'twilio_call_sid', 'vapi_call_id']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']


@admin.register(MissedCallQueue)
class MissedCallQueueAdmin(admin.ModelAdmin):
    list_display = ['caller_number', 'clinic', 'status', 'attempt_count', 'max_attempts', 'next_attempt_at', 'created_at']
    list_filter = ['status', 'clinic']
    search_fields = ['caller_number']
    readonly_fields = ['id', 'created_at']
    actions = ['retry_callbacks']

    @admin.action(description='Retry selected callbacks now')
    def retry_callbacks(self, request, queryset):
        from tasks.callback_tasks import schedule_callback
        count = 0
        for item in queryset.filter(status__in=['pending', 'attempted']):
            schedule_callback.delay(str(item.id))
            count += 1
        self.message_user(request, f'{count} callback(s) queued.')
