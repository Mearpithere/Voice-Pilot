"""
WhatsApp confirmation tasks.
Sends a booking confirmation via Plivo WhatsApp API after an appointment is booked.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


def _format_confirmation_message(appointment, clinic_name: str) -> str:
    date_str = appointment.scheduled_start.strftime("%A, %d %B %Y")
    time_str = appointment.scheduled_start.strftime("%I:%M %p")
    return (
        f"Hi {appointment.patient_name}! 👋\n\n"
        f"Your appointment at *{clinic_name}* is confirmed.\n\n"
        f"📅 *{date_str}*\n"
        f"🕐 *{time_str}*\n"
        f"🏥 *{appointment.appointment_type}*\n\n"
        f"Reply *CANCEL* to cancel your appointment.\n"
        f"See you soon!"
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=60,
             name='tasks.whatsapp_tasks.send_whatsapp_confirmation')
def send_whatsapp_confirmation(self, appointment_id: str):
    """
    Send a WhatsApp booking confirmation to the patient.
    """
    from apps.appointments.models import Appointment
    from apps.integrations.plivo_client import client as plivo

    try:
        appointment = Appointment.objects.select_related('clinic').get(id=appointment_id)
    except Appointment.DoesNotExist:
        logger.warning("Appointment %s not found for WhatsApp confirmation", appointment_id)
        return

    if appointment.whatsapp_sent:
        logger.info("WhatsApp already sent for appointment %s, skipping", appointment_id)
        return

    clinic = appointment.clinic
    patient_phone = appointment.patient_phone

    # Ensure phone has country code
    if not patient_phone.startswith('+'):
        patient_phone = '+91' + patient_phone.lstrip('0')

    message = _format_confirmation_message(appointment, clinic.name)

    try:
        message_uuid = plivo.send_whatsapp_message(
            to_number=patient_phone,
            message=message,
            from_number=clinic.phone_number,
        )
        appointment.whatsapp_sent = True
        appointment.whatsapp_message_sid = message_uuid
        appointment.save(update_fields=['whatsapp_sent', 'whatsapp_message_sid'])
        logger.info("WhatsApp confirmation sent to %s (uuid: %s)", patient_phone, message_uuid)
    except Exception as exc:
        logger.error("WhatsApp send failed for appointment %s: %s", appointment_id, exc)
        raise self.retry(exc=exc)
