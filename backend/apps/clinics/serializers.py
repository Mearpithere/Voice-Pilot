from rest_framework import serializers
from .models import Clinic, ClinicUser


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'slug', 'phone_number',
            'vapi_assistant_id', 'vapi_phone_number_id',
            'google_calendar_id', 'airtable_table_name',
            'timezone', 'business_hours_start', 'business_hours_end',
            'after_hours_message', 'custom_faqs',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'phone_number', 'twilio_phone_sid',
            'vapi_assistant_id', 'vapi_phone_number_id',
            'created_at', 'updated_at',
        ]


class ClinicCreateSerializer(serializers.ModelSerializer):
    """Used only for POST /api/clinics/ — triggers full provisioning."""
    class Meta:
        model = Clinic
        fields = ['name', 'slug', 'timezone', 'business_hours_start',
                  'business_hours_end', 'after_hours_message', 'custom_faqs',
                  'google_calendar_id', 'airtable_table_name']


class ClinicUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ClinicUser
        fields = ['id', 'username', 'email', 'clinic', 'role']
