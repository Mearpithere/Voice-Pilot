from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Clinic
from .provisioning import deprovision_clinic, provision_clinic
from .serializers import ClinicCreateSerializer, ClinicSerializer


class ClinicViewSet(ModelViewSet):
    """
    CRUD for clinics plus provisioning actions.

    GET    /api/clinics/               list
    POST   /api/clinics/               create + auto-provision Plivo number
    GET    /api/clinics/{id}/          retrieve
    PATCH  /api/clinics/{id}/          update settings
    DELETE /api/clinics/{id}/          deactivate + release Plivo number
    POST   /api/clinics/{id}/provision/ re-provision (if number lost)
    """

    queryset = Clinic.objects.all().order_by('name')

    def get_serializer_class(self):
        if self.action == 'create':
            return ClinicCreateSerializer
        return ClinicSerializer

    def get_queryset(self):
        # Non-superusers only see their own clinic
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
            # Roll back — don't leave a half-provisioned clinic
            raise Exception(f"Provisioning failed: {e}")

        return Response(
            ClinicSerializer(clinic).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        clinic = self.get_object()
        deprovision_clinic(clinic)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def provision(self, request, pk=None):
        """POST /api/clinics/{id}/provision/ — manually re-provision."""
        clinic = self.get_object()
        try:
            provision_clinic(clinic)
            return Response({'status': 'provisioned', 'phone_number': clinic.phone_number})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
