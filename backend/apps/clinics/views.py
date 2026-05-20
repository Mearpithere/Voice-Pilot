import asyncio
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Clinic
from .provisioning import deprovision_clinic, provision_clinic
from .serializers import ClinicCreateSerializer, ClinicSerializer


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class ClinicViewSet(ModelViewSet):
    queryset = Clinic.objects.all().order_by('name')

    def get_serializer_class(self):
        if self.action == 'create':
            return ClinicCreateSerializer
        return ClinicSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Clinic.objects.all()
        try:
            return Clinic.objects.filter(id=user.clinic_profile.clinic.id)
        except Exception:
            return Clinic.objects.none()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clinic = serializer.save()
        try:
            provision_clinic(clinic)
        except Exception as e:
            raise Exception(f"Provisioning failed: {e}")
        return Response(ClinicSerializer(clinic).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        clinic = self.get_object()
        deprovision_clinic(clinic)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def provision(self, request, pk=None):
        clinic = self.get_object()
        try:
            provision_clinic(clinic)
            return Response({'status': 'provisioned', 'phone_number': clinic.phone_number})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=['post'], url_path='web_call_token')
    def web_call_token(self, request, pk=None):
        """
        POST /api/clinics/{id}/web_call_token/
        Creates a LiveKit room for a browser-based call and returns an access token.
        Used by the WebCallButton component.
        """
        import uuid
        from apps.integrations.livekit.client import create_room, dispatch_agent, generate_sip_token
        from apps.calls.models import CallLog
        from django.utils import timezone

        clinic = self.get_object()
        call_uuid = str(uuid.uuid4())
        room_name = f"webcall-{call_uuid}"

        call_log = CallLog.objects.create(
            clinic=clinic,
            direction="inbound",
            caller_number="web",
            caller_name=f"Web caller",
            status="in_progress",
            outcome="unknown",
            started_at=timezone.now(),
        )

        try:
            _run_async(create_room(room_name, clinic.slug, str(call_log.id)))
            _run_async(dispatch_agent(room_name, str(call_log.id)))
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        token = generate_sip_token(room_name, f"web-{call_uuid[:8]}")
        return Response({
            'token': token,
            'room_name': room_name,
            'livekit_url': request.build_absolute_uri('/')[:-1],
        })
