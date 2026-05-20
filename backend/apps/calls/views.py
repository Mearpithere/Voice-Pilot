from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.integrations.aws_s3.client import generate_presigned_url
from .models import CallLog, MissedCallQueue
from .serializers import CallLogSerializer, MissedCallQueueSerializer


class CallLogViewSet(ReadOnlyModelViewSet):
    """
    GET  /api/calls/               list with filters
    GET  /api/calls/{id}/          detail (full transcript + recording)
    GET  /api/calls/{id}/recording/ fresh presigned S3 URL
    GET  /api/calls/stats/         aggregate dashboard stats
    """

    serializer_class = CallLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['caller_number', 'caller_name', 'summary']
    ordering_fields = ['created_at', 'duration_seconds']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = CallLog.objects.select_related('clinic').all()
        else:
            try:
                clinic = user.clinic_profile.clinic
                qs = CallLog.objects.filter(clinic=clinic).select_related('clinic')
            except Exception:
                return CallLog.objects.none()

        # Query param filters
        params = self.request.query_params
        outcome = params.get('outcome')
        direction = params.get('direction')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        clinic_id = params.get('clinic')

        if outcome:
            qs = qs.filter(outcome=outcome)
        if direction:
            qs = qs.filter(direction=direction)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if clinic_id and user.is_superuser:
            qs = qs.filter(clinic_id=clinic_id)

        return qs

    @action(detail=True, methods=['get'])
    def recording(self, request, pk=None):
        """GET /api/calls/{id}/recording/ — returns a fresh 1-hour presigned URL."""
        call = self.get_object()
        if not call.recording_s3_key:
            return Response(
                {'error': 'No recording available for this call.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            url = generate_presigned_url(call.recording_s3_key)
            return Response({'url': url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        GET /api/calls/stats/
        Returns aggregate stats for the dashboard.
        Optional query param: ?period=today|week|month (default: today)
        """
        period = request.query_params.get('period', 'today')
        now = timezone.now()

        if period == 'week':
            since = now - timedelta(days=7)
        elif period == 'month':
            since = now - timedelta(days=30)
        else:  # today
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)

        qs = self.get_queryset().filter(created_at__gte=since)

        total = qs.count()
        inbound = qs.filter(direction='inbound').count()
        outbound = qs.filter(direction='outbound').count()
        booked = qs.filter(outcome='booked').count()
        missed = qs.filter(outcome='missed').count()
        transferred = qs.filter(outcome='transferred').count()

        avg_duration = qs.filter(
            duration_seconds__isnull=False
        ).aggregate(avg=Avg('duration_seconds'))['avg']

        booking_rate = round((booked / inbound * 100), 1) if inbound > 0 else 0

        return Response({
            'period': period,
            'total_calls': total,
            'inbound': inbound,
            'outbound': outbound,
            'booked': booked,
            'missed': missed,
            'transferred': transferred,
            'booking_rate_pct': booking_rate,
            'avg_duration_seconds': round(avg_duration or 0),
            'avg_duration_minutes': round((avg_duration or 0) / 60, 1),
        })


class MissedCallQueueViewSet(ReadOnlyModelViewSet):
    """
    GET /api/calls/queue/    — pending callback queue
    """
    serializer_class = MissedCallQueueSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return MissedCallQueue.objects.select_related('clinic').all()
        try:
            clinic = user.clinic_profile.clinic
            return MissedCallQueue.objects.filter(clinic=clinic).select_related('clinic')
        except Exception:
            return MissedCallQueue.objects.none()
