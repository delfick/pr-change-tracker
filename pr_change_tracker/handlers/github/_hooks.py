from __future__ import annotations

import hashlib
import hmac
from typing import Never

import attrs

from ... import storage
from . import _errors, _event


def determine_expected_signature(secret: str, body: bytes) -> str:
    hash_object = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return f"sha256={hash_object.hexdigest()}"


@attrs.frozen
class IncomingProcessor:
    _storage: storage.CommonStorage

    def process(self, incoming: _event.Incoming, /) -> Never:
        raise _errors.GithubWebhookDropped(reason="Unrecognised webhook event")
