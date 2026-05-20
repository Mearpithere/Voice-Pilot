"""
Plivo REST API wrapper.
Handles phone number provisioning, outbound calls, and SMS/WhatsApp.
"""

import logging
import plivo
from django.conf import settings

logger = logging.getLogger(__name__)


def _client() -> plivo.RestClient:
    return plivo.RestClient(
        auth_id=settings.PLIVO_AUTH_ID,
        auth_token=settings.PLIVO_AUTH_TOKEN,
    )


def provision_phone_number(prefix: str = "91") -> dict:
    """
    Search for and rent an available Plivo number for the given country prefix.
    Returns dict with 'number' and 'uuid' keys.
    """
    client = _client()

    # Search available numbers in India (country_iso=IN)
    response = client.numbers.search(
        country_iso="IN",
        pattern=prefix,
        type="local",
        limit=1,
    )
    if not response or not response.get("objects"):
        raise RuntimeError("No available Plivo numbers found for prefix: " + prefix)

    number_obj = response["objects"][0]
    number = number_obj["number"]

    # Rent the number
    client.numbers.buy(number=number)
    logger.info("Provisioned Plivo number: %s", number)
    return {"number": number}


def configure_number_webhooks(phone_number: str, answer_url: str, hangup_url: str) -> None:
    """
    Point a Plivo number's answer/hangup webhooks at our Django endpoints.
    """
    client = _client()
    client.numbers.update(
        number=phone_number,
        answer_url=answer_url,
        answer_method="POST",
        hangup_url=hangup_url,
        hangup_method="POST",
    )
    logger.info("Configured webhooks for %s → %s", phone_number, answer_url)


def release_phone_number(phone_number: str) -> None:
    """Unrent a Plivo number (called when a clinic is deactivated)."""
    client = _client()
    client.numbers.unrent(number=phone_number)
    logger.info("Released Plivo number: %s", phone_number)


def make_outbound_call(
    from_number: str,
    to_number: str,
    answer_url: str,
    hangup_url: str,
) -> str:
    """
    Initiate an outbound call (used for missed-call callbacks).
    Returns the Plivo call UUID.
    """
    client = _client()
    response = client.calls.create(
        from_=from_number,
        to_=to_number,
        answer_url=answer_url,
        answer_method="POST",
        hangup_url=hangup_url,
        hangup_method="POST",
    )
    call_uuid = response.get("request_uuid", "")
    logger.info("Outbound call initiated: %s → %s (uuid: %s)", from_number, to_number, call_uuid)
    return call_uuid


def send_whatsapp_message(to_number: str, message: str, from_number: str) -> str:
    """
    Send a WhatsApp message via Plivo's WhatsApp API.
    Returns the message UUID.
    """
    client = _client()
    response = client.messages.create(
        src=f"whatsapp:{from_number}",
        dst=f"whatsapp:{to_number}",
        text=message,
        type_="whatsapp",
    )
    return response.get("message_uuid", [""])[0]
