"""
LiveKit API client.

Used by Django (not the agent) to:
- Create rooms for incoming calls
- Dispatch the agent to a room
- Generate SIP participant tokens
- Look up active rooms
"""

import logging
from livekit import api
from django.conf import settings

logger = logging.getLogger(__name__)


def _livekit_api() -> api.LiveKitAPI:
    return api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )


async def create_room(room_name: str, clinic_slug: str, call_log_id: str) -> dict:
    """
    Create a LiveKit room for an incoming call.

    room_name    — unique per call, e.g. "call-{twilio_call_uuid}"
    clinic_slug  — stored as room metadata so the agent knows which clinic
    call_log_id  — stored as room metadata so the agent can load the CallLog
    """
    lk = _livekit_api()
    room = await lk.room.create_room(
        api.CreateRoomRequest(
            name=room_name,
            metadata=clinic_slug,           # agent reads this
            empty_timeout=300,              # auto-delete after 5 min if empty
            max_participants=10,
        )
    )
    logger.info("Created LiveKit room: %s (clinic: %s)", room_name, clinic_slug)
    return {"room_name": room.name, "sid": room.sid}


async def dispatch_agent(room_name: str, call_log_id: str) -> None:
    """
    Tell the LiveKit agent worker to join this room.
    The agent worker must already be running (started via `python -m agent.main start`).
    """
    lk = _livekit_api()
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="voicepilot",        # must match WorkerOptions(name=...) in main.py
            room=room_name,
            metadata=call_log_id,           # agent reads this to load CallLog
        )
    )
    logger.info("Dispatched agent to room: %s", room_name)


def generate_sip_token(room_name: str, participant_identity: str) -> str:
    """
    Generate a LiveKit access token for a SIP participant (the Plivo caller).
    This token is embedded in the SIP URI so LiveKit admits the call.
    """
    token = (
        api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(participant_identity)
        .with_name("Caller")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )
    return token


async def list_active_rooms() -> list:
    """Return all currently active rooms (used by dashboard / monitoring)."""
    lk = _livekit_api()
    response = await lk.room.list_rooms(api.ListRoomsRequest())
    return [{"name": r.name, "num_participants": r.num_participants} for r in response.rooms]


async def delete_room(room_name: str) -> None:
    """Force-close a room (e.g. after call ends or agent transfer)."""
    lk = _livekit_api()
    await lk.room.delete_room(api.DeleteRoomRequest(room=room_name))
    logger.info("Deleted LiveKit room: %s", room_name)
