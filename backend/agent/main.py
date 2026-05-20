"""
LiveKit agent entry point.

Run with:
    python -m agent.main dev        # local development
    python -m agent.main start      # production

The agent worker connects to LiveKit and waits for rooms to be created.
When Plivo sends an inbound call, Django creates a room and dispatches
this agent to it. The room metadata contains the clinic slug.
"""

import logging
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voicepilot.settings.development')
django.setup()

from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import cartesia, deepgram, google, silero
from django.conf import settings

from apps.clinics.models import Clinic
from apps.calls.models import CallLog
from .voice_agent import VoicePilotAgent

logger = logging.getLogger(__name__)


def prewarm(proc: JobProcess):
    """
    Called once when the worker process starts.
    Load the Silero VAD model into memory so the first call has no cold-start delay.
    """
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """
    Called for every new call (room). Reads clinic slug from room metadata,
    looks up the Clinic, then starts the voice pipeline.
    """
    await ctx.connect()

    # Room metadata is set to the clinic slug by the Django webhook
    clinic_slug = ctx.room.metadata or ""
    call_log_id = ctx.job.metadata or ""  # secondary metadata: CallLog UUID

    try:
        clinic = Clinic.objects.get(slug=clinic_slug, is_active=True)
    except Clinic.DoesNotExist:
        logger.error("No active clinic found for slug: %s", clinic_slug)
        return

    try:
        call_log = CallLog.objects.get(id=call_log_id)
    except (CallLog.DoesNotExist, Exception):
        # Fallback: create a minimal log entry
        call_log = CallLog.objects.create(
            clinic=clinic,
            direction="inbound",
            caller_number="unknown",
        )

    is_callback = call_log.direction == "outbound"

    agent = VoicePilotAgent(clinic=clinic, call_log=call_log, is_callback=is_callback)

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(
            model="nova-2",
            language="en-IN",          # Indian English — better accent handling
            api_key=settings.DEEPGRAM_API_KEY,
        ),
        llm=google.LLM(
            model="gemini-2.0-flash",
            api_key=settings.GOOGLE_AI_API_KEY,
        ),
        tts=cartesia.TTS(
            voice=settings.CARTESIA_VOICE_ID,
            api_key=settings.CARTESIA_API_KEY,
            model="sonic-english",
        ),
    )

    # Collect usage metrics and update CallLog when the session ends
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def on_metrics(mtrx: metrics.AgentMetrics):
        metrics.log_metrics(mtrx)
        usage_collector.collect(mtrx)

    async def on_session_end():
        summary = await usage_collector.aclose()
        logger.info(
            "Call %s ended. Input tokens: %s, TTS chars: %s",
            call_log_id,
            summary.llm_prompt_tokens,
            summary.tts_characters_count,
        )
        # Mark call as completed — transcript is updated by the Plivo status webhook
        call_log.status = "completed"
        call_log.save(update_fields=["status"])

    ctx.add_shutdown_callback(on_session_end)

    await session.start(agent=agent, room=ctx.room)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
