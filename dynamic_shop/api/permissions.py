"""Permissions customisées pour l'API."""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStaffOrReadOnly(BasePermission):
    """Autorise la lecture à tous et l'écriture uniquement au staff."""

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
