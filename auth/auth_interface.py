"""
Authentication Interface (Abstract Base)
==========================================
Defines the contract every auth provider must implement.

Design Decisions:
- Abstract base class so we can swap providers (SQLite-local, Clerk, Auth0, etc.)
  without touching any calling code.
- Returns a simple AuthUser dataclass — the rest of the app only depends on this.
- No framework-specific types leak out of the auth boundary.

Upgrade Path:
  To switch to Clerk:
    1. Create auth/clerk_provider.py implementing AuthProvider.
    2. Verify JWTs via Clerk's Backend API (https://clerk.com/docs/reference/backend-api).
    3. Change the provider instantiation in app.py — nothing else changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthUser:
    """
    Canonical user representation used across the entire application.

    Every auth provider must map its native user object to this dataclass.
    """

    id: int                     # Internal DB primary key
    external_id: str            # Provider-specific ID (clerk_user_id, etc.)
    email: str
    full_name: str
    provider: str               # e.g. "local", "clerk"


class AuthProvider(ABC):
    """
    Abstract authentication provider.

    Subclasses implement the concrete auth mechanism (local DB,
    Clerk JWT verification, OAuth, etc.).
    """

    @abstractmethod
    def register(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """
        Register a new user.

        Returns
        -------
        (success, message, user_or_none)
        """
        ...

    @abstractmethod
    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """
        Authenticate an existing user.

        Returns
        -------
        (success, message, user_or_none)
        """
        ...

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        """Fetch user by internal DB id."""
        ...

    @abstractmethod
    def get_user_by_external_id(self, external_id: str) -> Optional[AuthUser]:
        """Fetch user by provider-specific external id."""
        ...
