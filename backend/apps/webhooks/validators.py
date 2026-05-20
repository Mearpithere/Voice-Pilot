"""
Webhook signature validators.
Plivo signs every request with an HMAC-SHA256 of the full URL + sorted POST params.
"""

import hashlib
import hmac
import base64
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def validate_plivo_signature(request) -> bool:
    """
    Validate that a webhook request genuinely came from Plivo.
    Returns True if valid, False otherwise.
    In development (DEBUG=True) always returns True so ngrok testing works.
    """
    from django.conf import settings as s
    if s.DEBUG:
        return True

    signature = request.headers.get("X-Plivo-Signature-V2", "")
    nonce = request.headers.get("X-Plivo-Signature-V2-Nonce", "")

    if not signature or not nonce:
        logger.warning("Missing Plivo signature headers")
        return False

    uri = request.build_absolute_uri()
    message = uri + nonce
    expected = base64.b64encode(
        hmac.new(
            settings.PLIVO_AUTH_TOKEN.encode(),
            message.encode(),
            hashlib.sha256,
        ).digest()
    ).decode()

    valid = hmac.compare_digest(expected, signature)
    if not valid:
        logger.warning("Plivo signature mismatch for %s", uri)
    return valid
