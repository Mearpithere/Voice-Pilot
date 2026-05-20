from django.contrib import admin
from django.urls import path, include
from utils.auth_views import LoginView, LogoutView, MeView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/auth/login/',   LoginView.as_view(),  name='login'),
    path('api/auth/logout/',  LogoutView.as_view(), name='logout'),
    path('api/auth/me/',      MeView.as_view(),     name='me'),

    # Resources
    path('api/clinics/',      include('apps.clinics.urls')),
    path('api/calls/',        include('apps.calls.urls')),
    path('api/appointments/', include('apps.appointments.urls')),

    # Webhooks (no auth — validated by Plivo signature / LiveKit JWT)
    path('api/webhooks/',     include('apps.webhooks.urls')),
]
