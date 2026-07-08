from __future__ import annotations

import hmac

from videoforge.exceptions import WebhookAuthError


def verify_signature(payload: bytes, signature_header: str | None, secret: bytes) -> bool:
    if signature_header is None:
        raise WebhookAuthError("Missing signature header")

    expected = hmac.new(secret, payload, "sha256").hexdigest()
    provided = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(expected, provided):
        raise WebhookAuthError("Signature mismatch")

    return True
