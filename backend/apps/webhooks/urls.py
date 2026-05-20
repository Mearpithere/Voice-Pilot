from django.urls import path
from . import views

urlpatterns = [
    # Plivo webhooks
    path('plivo/inbound/',    views.PlivoInboundCallView.as_view(),    name='plivo_inbound'),
    path('plivo/status/',     views.PlivoCallStatusView.as_view(),     name='plivo_status'),
    path('plivo/recording/',  views.PlivoRecordingView.as_view(),      name='plivo_recording'),
    path('plivo/outbound/',   views.PlivoOutboundAnswerView.as_view(), name='plivo_outbound'),

    # LiveKit webhook (room events)
    path('livekit/',          views.LiveKitWebhookView.as_view(),      name='livekit_webhook'),
]
