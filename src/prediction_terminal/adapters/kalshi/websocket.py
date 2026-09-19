"""Capability gate. The shipped pipeline deliberately uses public REST polling."""

from .capabilities import CAPABILITIES


def status(settings):
    return {
        "mode": "POLLED",
        "reason": "Authenticated market stream is not enabled in this release.",
        "credentials_present": bool(
            settings.kalshi_api_key_id.get_secret_value() and settings.kalshi_private_key_path
        ),
        "capability": CAPABILITIES["websocket"],
    }
