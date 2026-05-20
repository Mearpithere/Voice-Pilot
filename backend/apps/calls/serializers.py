from rest_framework import serializers
from .models import CallLog, MissedCallQueue


class CallLogSerializer(serializers.ModelSerializer):
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    outcome_display = serializers.CharField(source='get_outcome_display', read_only=True)
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = CallLog
        fields = [
            'id', 'clinic', 'clinic_name',
            'direction', 'caller_number', 'caller_name',
            'status', 'outcome', 'outcome_display',
            'duration_seconds', 'duration_minutes',
            'recording_url', 'transcript', 'summary',
            'crm_synced',
            'started_at', 'ended_at', 'created_at',
        ]
        read_only_fields = fields

    def get_duration_minutes(self, obj):
        if obj.duration_seconds is None:
            return None
        return round(obj.duration_seconds / 60, 1)


class MissedCallQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissedCallQueue
        fields = [
            'id', 'clinic', 'caller_number',
            'status', 'attempt_count', 'max_attempts',
            'last_attempt_at', 'next_attempt_at', 'created_at',
        ]
        read_only_fields = fields
