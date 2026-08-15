"""Small, explicit RBAC boundary for the REX proof of concept."""

from __future__ import annotations

from dataclasses import dataclass


ROLES = {"ADMIN", "SUPERVISOR", "OPERATOR", "VIEWER"}
PERMISSIONS = {
    "ADMIN": {"read", "write", "sync", "manage"},
    "SUPERVISOR": {"read", "write", "sync"},
    "OPERATOR": {"read", "write", "sync"},
    "VIEWER": {"read"},
}


@dataclass(frozen=True)
class Actor:
    actor_id: str
    role: str

    def can(self, permission: str) -> bool:
        return permission in PERMISSIONS.get(self.role, set())


def actor_from_headers(actor_id: str | None, role: str | None) -> Actor:
    normalized_role = (role or "VIEWER").upper()
    if normalized_role not in ROLES:
        normalized_role = "VIEWER"
    return Actor(actor_id or "anonymous", normalized_role)
