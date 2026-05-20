"""
Webhook views for Plivo (telephony) and LiveKit (room events).

Call flow for inbound calls:
  1. Patient calls Plivo number
  2. Plivo POST → PlivoInboundCallView
  3. Django checks business hours, creates CallLog, creates LiveKit room,
     dispatches agent, returns Plivo XML to connect audio to LiveKit SIP
  4. LiveKit agent handles the conversation
  5. Call ends → PlivoCallStatusView updates CallLog
  6. Plivo POSTs recording URL → PlivoRecordingView queues S3 upload
  7. LiveKit room_finished event → LiveKitWebhookView marks call complete
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime

import pytz
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.calls.models import CallLog, MissedCallQueue
from apps.clinics.models import Clinic
from apps.integrations.livekit.client import create_room, dispatch_agent
from apps.integrations.plivo_client.xml_builder import (
    build_after_hours_xml,
    build_connect_to_livekit_xml,
    build_voicemail_xml,
)
from .validators import validate_plivo_signature

logger = logging.getLogger(__name__)

LIVEKIT_SIP_DOMAIN = "sip.livekit.cloud"


def _run_async(coro):
    """Run an async function from a sync Django view."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _is_within_business_hours(clinic: Clinic) -> bool:
    """Return True if current time is within the clinic's business hours."""
    tz = pytz.timezone(clinic.timezone)
    now_local = datetime.now(tz).time()
    return clinic.business_hours_start <= now_local <= clinic.business_hours_end


@method_decorator(csrf_exempt, name='dispatch')
class PlivoInboundCallView(View):
    """
    POST /api/webhooks/plivo/inbound/
    Called by Plivo when a patient dials the clinic's number.
    """

    def post(self, request):
        if not validate_plivo_signature(request):
            return HttpResponse("Forbidden", status=403)

        to_number = request.POST.get("To", "")
        from_number = request.POST.get("From", "")
        call_uuid = request.POST.get("CallUUID", str(uuid.uuid4()))

        # Look up clinic by Plivo number
        try:
            clinic = Clinic.objects.get(phone_number=to_number, is_active=True)
        except Clinic.DoesNotExist:
            logger.error("No clinic found for number: %s", to_number)
            return HttpResponse(build_voicemail_xml("our clinic"), content_type="text/xml")

        # After-hours check
        if not _is_within_business_hours(clinic):
            # Create a missed call log
            CallLog.objects.create(
                clinic=clinic,
                direction="inbound",
                caller_number=from_number,
                twilio_call_sid=call_uuid,
                status="completed",
                outcome="missed",
                started_at=timezone.now(),
                ended_at=timezone.now(),
            )
            xml = build_after_hours_xml(
                clinic.after_hours_message or
                f"Thank you for calling {clinic.name}. We are currently closed. "
                f"Our hours are {clinic.business_hours_start.strftime('%I:%M %p')} to "
                f"{clinic.business_hours_end.strftime('%I:%M %p')}. Please call back during business hours."
            )
            return HttpResponse(xml, content_type="text/xml")

        # Create CallLog
        call_log = CallLog.objects.create(
            clinic=clinic,
            direction="inbound",
            caller_number=from_number,
            twilio_call_sid=call_uuid,
            status="in_progress",
            outcome="unknown",
            started_at=timezone.now(),
        )

        # Create LiveKit room + dispatch agent
        room_name = f"call-{call_uuid}"
        try:
            _run_async(create_room(room_name, clinic.slug, str(call_log.id)))
            _run_async(dispatch_agent(room_name, str(call_log.id)))
        except Exception as e:
            logger.error("LiveKit room creation failed for call %s: %s", call_uuid, e)
            # Fallback: voicemail
            call_log.outcome = "voicemail"
            call_log.save(update_fields=["outcome"])
            return HttpResponse(build_voicemail_xml(clinic.name), content_type="text/xml")

        # SIP URI: sip:{room_name}@{project_sip_domain}
        # The project SIP domain comes from LiveKit project settings
        project_id = settings.LIVEKIT_URL.split("//")[1].split(".")[0]  # e.g. "onco-life-x2pjcdzt"
        # Extract just the project hash part for SIP
        sip_uri = f"sip:{room_name}@{project_id}.{LIVEKIT_SIP_DOMAIN}"

        xml = build_connect_to_livekit_xml(sip_uri)
        return HttpResponse(xml, content_type="text/xml")


@method_decorator(csrf_exempt, name='dispatch')
class PlivoCallStatusView(View):
    """
    POST /api/webhooks/plivo/status/
    Called by Plivo on every call status change (ringing, answered, completed, etc.)
    """

    def post(self, request):
        if not validate_plivo_signature(request):
            return HttpResponse("Forbidden", status=403)

        call_uuid = request.POST.get("CallUUID", "")
        call_status = request.POST.get("CallStatus", "")
        duration = request.POST.get("Duration", 0)
        from_number = request.POST.get("From", "")
        to_number = request.POST.get("To", "")

        try:
            call_log = CallLog.objects.get(twilio_call_sid=call_uuid)
        except CallLog.DoesNotExist:
            logger.warning("CallLog not found for UUID: %s", call_uuid)
            return HttpResponse("OK")

        if call_status in ("no-answer", "busy", "failed"):
            call_log.status = "completed"
            call_log.outcome = "missed"
            call_log.ended_at = timezone.now()
            call_log.save(update_fields=["status", "outcome", "ended_at"])

            # Queue a callback attempt
            try:
                clinic = call_log.clinic
                queue_entry = MissedCallQueue.objects.create(
                    clinic=clinic,
                    caller_number=from_number or call_log.caller_number,
                    original_call=call_log,
                    next_attempt_at=timezone.now(),
                )
                from tasks.callback_tasks import schedule_callback
                schedule_callback.apply_async(
                    args=[str(queue_entry.id)],
                    countdown=300,  # first attempt after 5 min
                )
                logger.info("Queued callback for missed call from %s", call_log.caller_number)
            except Exception as e:
                logger.error("Failed to queue callback: %s", e)

        elif call_status == "completed":
            call_log.status = "completed"
            call_log.duration_seconds = int(duration or 0)
            call_log.ended_at = timezone.now()
            call_log.save(update_fields=["status", "duration_seconds", "ended_at"])

        return HttpResponse("OK")


@method_decorator(csrf_exempt, name='dispatch')
class PlivoRecordingView(View):
    """
    POST /api/webhooks/plivo/recording/
    Called by Plivo after it finishes recording a call.
    """

    def post(self, request):
        if not validate_plivo_signature(request):
            return HttpResponse("Forbidden", status=403)

        call_uuid = request.POST.get("CallUUID", "")
        recording_url = request.POST.get("RecordUrl", "")

        if not recording_url:
            return HttpResponse("OK")

        try:
            call_log = CallLog.objects.get(twilio_call_sid=call_uuid)
        except CallLog.DoesNotExist:
            logger.warning("CallLog not found for recording webhook: %s", call_uuid)
            return HttpResponse("OK")

        # Queue S3 upload
        from tasks.recording_tasks import upload_recording_to_s3
        upload_recording_to_s3.delay(str(call_log.id), recording_url)

        return HttpResponse("OK")


@method_decorator(csrf_exempt, name='dispatch')
class PlivoOutboundAnswerView(View):
    """
    POST /api/webhooks/plivo/outbound/
    Answer URL for outbound callback calls — connects them to a LiveKit agent room.
    """

    def post(self, request):
        if not validate_plivo_signature(request):
            return HttpResponse("Forbidden", status=403)

        call_uuid = request.POST.get("CallUUID", "")
        to_number = request.POST.get("To", "")

        # Find the pending callback queue entry
        queue_entry = (
            MissedCallQueue.objects
            .filter(caller_number=to_number, status="attempted")
            .order_by("-created_at")
            .first()
        )

        if not queue_entry:
            return HttpResponse(build_voicemail_xml("the clinic"), content_type="text/xml")

        clinic = queue_entry.clinic

        # Create or reuse call log
        call_log = CallLog.objects.create(
            clinic=clinic,
            direction="outbound",
            caller_number=to_number,
            twilio_call_sid=call_uuid,
            status="in_progress",
            outcome="unknown",
            started_at=timezone.now(),
        )

        room_name = f"callback-{call_uuid}"
        try:
            _run_async(create_room(room_name, clinic.slug, str(call_log.id)))
            _run_async(dispatch_agent(room_name, str(call_log.id)))
        except Exception as e:
            logger.error("LiveKit room creation failed for outbound call %s: %s", call_uuid, e)
            return HttpResponse(build_voicemail_xml(clinic.name), content_type="text/xml")

        project_id = settings.LIVEKIT_URL.split("//")[1].split(".")[0]
        sip_uri = f"sip:{room_name}@{project_id}.{LIVEKIT_SIP_DOMAIN}"
        xml = build_connect_to_livekit_xml(sip_uri)
        return HttpResponse(xml, content_type="text/xml")


@method_decorator(csrf_exempt, name='dispatch')
class LiveKitWebhookView(View):
    """
    POST /api/webhooks/livekit/
    Receives room lifecycle events from LiveKit Cloud.
    Configure this URL in LiveKit Cloud → Settings → Webhooks.

    Events we handle:
      room_finished   — call ended, sync to Airtable
      participant_left — detect if human left early
    """

    def post(self, request):
        # LiveKit signs webhooks with the API secret
        auth_header = request.headers.get("Authorization", "")
        if not self._verify_livekit_token(auth_header):
            return HttpResponse("Forbidden", status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse("Bad Request", status=400)

        event = payload.get("event", "")
        room = payload.get("room", {})
        room_name = room.get("name", "")

        logger.info("LiveKit event: %s for room: %s", event, room_name)

        if event == "room_finished":
            self._handle_room_finished(room_name, room)

        return HttpResponse("OK")

    def _verify_livekit_token(self, auth_header: str) -> bool:
        """
        Verify the LiveKit webhook JWT token.
        In DEBUG mode, skip verification for local testing.
        """
        if settings.DEBUG:
            return True
        if not auth_header.startswith("Bearer "):
            return False
        token = auth_header.split(" ", 1)[1]
        try:
            from livekit.api import TokenVerifier
            verifier = TokenVerifier(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            verifier.verify(token)
            return True
        except Exception as e:
            logger.warning("LiveKit token verification failed: %s", e)
            return False

    def _handle_room_finished(self, room_name: str, room_data: dict):
        """
        Room finished = call ended. Find the CallLog and queue CRM sync.
        """
        # room_name format: "call-{plivo_call_uuid}" or "callback-{uuid}"
        call_uuid = room_name.replace("call-", "").replace("callback-", "")
        try:
            call_log = CallLog.objects.get(twilio_call_sid=call_uuid)
        except CallLog.DoesNotExist:
            logger.warning("CallLog not found for finished room: %s", room_name)
            return

        if call_log.status != "completed":
            call_log.status = "completed"
            call_log.ended_at = timezone.now()
            call_log.save(update_fields=["status", "ended_at"])

        # Queue Airtable CRM sync
        if call_log.clinic.airtable_table_name:
            from tasks.crm_tasks import sync_call_to_airtable
            sync_call_to_airtable.delay(str(call_log.id))
