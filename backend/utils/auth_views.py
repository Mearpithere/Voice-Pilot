"""
Custom login view that returns the token + user profile + clinic info in one response.
The frontend needs all three to bootstrap the dashboard.
"""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)

        clinic_data = None
        try:
            profile = user.clinic_profile
            clinic = profile.clinic
            clinic_data = {
                'id': str(clinic.id),
                'name': clinic.name,
                'slug': clinic.slug,
                'phone_number': clinic.phone_number,
                'timezone': clinic.timezone,
            }
        except Exception:
            pass  # superuser without a clinic profile

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            },
            'clinic': clinic_data,
        })


class LogoutView(APIView):
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'status': 'logged out'})


class MeView(APIView):
    """GET /api/auth/me/ — re-fetch current user + clinic after page reload."""

    def get(self, request):
        user = request.user
        clinic_data = None
        try:
            profile = user.clinic_profile
            clinic = profile.clinic
            clinic_data = {
                'id': str(clinic.id),
                'name': clinic.name,
                'slug': clinic.slug,
                'phone_number': clinic.phone_number,
                'timezone': clinic.timezone,
                'business_hours_start': str(clinic.business_hours_start),
                'business_hours_end': str(clinic.business_hours_end),
            }
        except Exception:
            pass

        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            },
            'clinic': clinic_data,
        })
