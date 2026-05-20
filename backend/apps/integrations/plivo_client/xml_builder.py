"""
Plivo XML response builders.
Plivo uses XML (similar to Twilio TwiML) to control call flow.
"""

import xml.etree.ElementTree as ET


def build_connect_to_livekit_xml(sip_uri: str) -> str:
    """
    Returns Plivo XML that dials into a LiveKit SIP ingress room.

    sip_uri format:  sip:{room_name}@{livekit_sip_domain}
    LiveKit SIP domain is found in your LiveKit Cloud project settings.

    Example:
        <Response>
          <Dial>
            <User>sip:clinic-sunrise-abc123@sip.livekit.cloud</User>
          </Dial>
        </Response>
    """
    response = ET.Element("Response")
    dial = ET.SubElement(response, "Dial")
    user = ET.SubElement(dial, "User")
    user.text = sip_uri
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(response, encoding="unicode")


def build_after_hours_xml(message: str) -> str:
    """
    Returns Plivo XML that speaks an after-hours message then hangs up.
    """
    response = ET.Element("Response")
    speak = ET.SubElement(response, "Speak", attrib={"voice": "Polly.Aditi", "language": "en-IN"})
    speak.text = message
    ET.SubElement(response, "Hangup")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(response, encoding="unicode")


def build_wait_xml(message: str = "Please hold while we connect your call.") -> str:
    """Short hold message while Django provisions a LiveKit room."""
    response = ET.Element("Response")
    speak = ET.SubElement(response, "Speak", attrib={"voice": "Polly.Aditi", "language": "en-IN"})
    speak.text = message
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(response, encoding="unicode")


def build_voicemail_xml(clinic_name: str) -> str:
    """
    Returns Plivo XML that prompts for a voicemail recording.
    """
    response = ET.Element("Response")
    speak = ET.SubElement(response, "Speak", attrib={"voice": "Polly.Aditi", "language": "en-IN"})
    speak.text = (
        f"You have reached {clinic_name}. "
        "Please leave a message after the beep and we will call you back."
    )
    ET.SubElement(response, "Record", attrib={
        "maxLength": "120",
        "transcriptionType": "auto",
        "playBeep": "true",
    })
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(response, encoding="unicode")
