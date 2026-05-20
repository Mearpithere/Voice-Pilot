from django.utils import timezone
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentUpdateSerializer


class AppointmentViewSet(ModelViewSet):
    """
    GET    /api/appointments/             list with filters
    GET    /api/appointments/{id}/        detail
    PATCH  /api/appointments/{id}/        update status/notes
    GET    /api/appointments/today/       today's appointments (dashboard widget)
    POST   /api/appointments/{id}/resend_whatsapp/  resend confirmation
    """

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient_name', 'patient_phone', 'appointment_type']
    ordering_fields = ['scheduled_start', 'created_at']
    ordering = ['scheduled_start']
    http_method_names = ['get', 'patch', 'head', 'options']  # no POST/PUT/DELETE from API

    def get_serializer_class(self):
        if self.action in ('partial_update',):
            return AppointmentUpdateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = Appointment.objects.select_related('clinic', 'call_log').all()
        else:
            try:
                clinic = user.clinic_profile.clinic
                qs = Appointment.objects.filter(clinic=clinic).select_related('clinic', 'call_log')
            except Exception:
                return Appointment.objects.none()

        params = self.request.query_params
        appt_status = params.get('status')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        appointment_type = params.get('type')

        if appt_status:
            qs = qs.filter(status=appt_status)
        if date_from:
            qs = qs.filter(scheduled_start__date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_start__date__lte=date_to)
        if appointment_type:
            qs = qs.filter(appointment_type__icontains=appointment_type)

        return qs

    @action(detail=False, methods=['get'])
    def today(self, request):
        """GET /api/appointments/today/ — for dashboard widget."""
        today = timezone.now().date()
        qs = self.get_queryset().filter(
            scheduled_start__date=today,
        ).exclude(status='cancelled').order_by('scheduled_start')
        serializer = AppointmentSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resend_whatsapp(self, request, pk=None):
        """POST /api/appointments/{id}/resend_whatsapp/"""
        appointment = self.get_object()
        appointment.whatsapp_sent = False
        appointment.save(update_fields=['whatsapp_sent'])
        from tasks.whatsapp_tasks import send_whatsapp_confirmation
        send_whatsapp_confirmation.delay(str(appointment.id))
        return Response({'status': 'queued'})
