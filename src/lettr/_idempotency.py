"""Idempotency key validation.

The key identifies one logical send. Reuse it when you retry and the API
returns the original result instead of delivering a second email.

**You choose the key; the SDK never generates one.** It only works if both
attempts use the same value, and the SDK does not retry - one ``send()`` is one
HTTP request - so the retry is yours, and only you know that two calls are the
same logical send. A key generated inside ``send()`` would differ on every
attempt and protect nothing while looking like it did.
"""

from __future__ import annotations

import re

from ._exceptions import ValidationError

IDEMPOTENCY_KEY_PATTERN = re.compile(r"\A[A-Za-z0-9._-]{1,255}\Z")
"""The format the API accepts: 1-255 characters of letters, digits, ``.``, ``_``, ``-``."""


def is_valid_idempotency_key(key: str) -> bool:
    """Whether a string is a usable idempotency key.

    Exported so callers deriving keys from their own ids - an order number, a
    job id - can check before sending rather than discovering it as a 422.
    """
    return IDEMPOTENCY_KEY_PATTERN.match(key) is not None


def validate_idempotency_key(key: str) -> None:
    """Raise :class:`ValidationError` if the key is malformed.

    Checked here so a bad key fails locally instead of costing a round trip.
    """
    if is_valid_idempotency_key(key):
        return

    raise ValidationError(
        message="Validation failed.",
        errors={
            "Idempotency-Key": ["Use 1 to 255 letters, digits, periods, underscores or hyphens."]
        },
    )
