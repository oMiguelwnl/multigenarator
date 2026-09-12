"""Server-owned API credentials and explicit role permissions."""
from __future__ import annotations

import hmac
import json
import re
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256

from pydantic import SecretStr


class Role(str, Enum):
    ADMIN = "Admin"
    LINGUIST = "Linguist"
    CONTENT_CREATOR = "ContentCreator"
    USER = "User"
    WORKER = "Worker"


PERMISSIONS = {
    Role.ADMIN: frozenset({"read", "import", "ranking", "audio", "content", "anki", "worker", "cancel", "admin"}),
    Role.LINGUIST: frozenset({"read", "import", "ranking", "cancel"}),
    Role.CONTENT_CREATOR: frozenset({"read", "audio", "content", "anki", "cancel"}),
    Role.USER: frozenset({"read", "anki", "cancel"}),
    Role.WORKER: frozenset({"worker"}),
}


@dataclass(frozen=True)
class Principal:
    subject: str
    role: Role


class AccessPolicy:
    """Store credential hashes, never raw tokens or request-selected roles."""

    def __init__(self, credentials: SecretStr):
        try:
            raw = json.loads(credentials.get_secret_value())
            if not isinstance(raw, dict) or len(raw) > 1000:
                raise ValueError
            self._principals = []
            for token, value in raw.items():
                if not isinstance(token, str) or not token or len(token) > 512:
                    raise ValueError
                if not isinstance(value, dict) or set(value) != {"subject", "role"}:
                    raise ValueError
                subject = value["subject"]
                if not isinstance(subject, str) or re.fullmatch(r"[A-Za-z0-9_.@:-]{1,128}", subject) is None:
                    raise ValueError
                self._principals.append((sha256(token.encode()).digest(), Principal(subject, Role(value["role"]))))
        except (ValueError, TypeError, KeyError):
            raise ValueError("invalid native API credential configuration") from None

    def authenticate(self, token: str) -> Principal | None:
        digest = sha256(token.encode()).digest()
        result = None
        for expected, principal in self._principals:
            if hmac.compare_digest(expected, digest):
                result = principal
        return result

    def permits(self, principal: Principal, action: str) -> bool:
        return action in PERMISSIONS[principal.role]
