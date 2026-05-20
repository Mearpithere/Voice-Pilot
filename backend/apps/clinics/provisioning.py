"""
Clinic provisioning — called when a new clinic is onboarded.

Steps:
1. Rent a Plivo phone number
2. Configure that number's webhooks → our Django endpoints
3. Save all IDs back to the Clinic record

The clinic owner still needs to:
- Share their Google Calendar with the service account email
- Set clinic.google_calendar_id via the settings dashboard
"""

import logging
from django.conf import settings
from apps.integrations.plivo_client import client as plivo

logger = logging.getLogger(__name__)


def provision_clinic(clinic) -> None:
    """
    Provision a Plivo phone number for the clinic and wire up webhooks.
    Safe to call multiple times — skips provisioning if number already exists.
    """
    if clinic.phone_number and clinic.twilio_phone_sid:
        logger.info("Clinic %s already provisioned, skipping", clinic.slug)
        return

    base_url = settings.PLIVO_WEBHOOK_BASE_URL

    # 1. Rent a number
    result = plivo.provision_phone_number(prefix="91")  # India numbers
    phone_number = result["number"]

    # 2. Wire webhooks
    plivo.configure_number_webhooks(
        phone_number=phone_number,
        answer_url=f"{base_url}/api/webhooks/plivo/inbound/",
        hangup_url=f"{base_url}/api/webhooks/plivo/status/",
    )

    # 3. Persist to Clinic
    clinic.phone_number = phone_number
    clinic.twilio_phone_sid = phone_number  # Plivo uses number as its own identifier
    clinic.save(update_fields=["phone_number", "twilio_phone_sid"])

    logger.info("Provisioned clinic %s with number %s", clinic.slug, phone_number)


def deprovision_clinic(clinic) -> None:
    """
    Release the Plivo number when a clinic is deactivated.
    """
    if clinic.phone_number:
        try:
            plivo.release_phone_number(clinic.phone_number)
            logger.info("Released number %s for clinic %s", clinic.phone_number, clinic.slug)
        except Exception as e:
            logger.error("Failed to release number %s: %s", clinic.phone_number, e)

    clinic.phone_number = ""
    clinic.twilio_phone_sid = ""
    clinic.is_active = False
    clinic.save(update_fields=["phone_number", "twilio_phone_sid", "is_active"])
