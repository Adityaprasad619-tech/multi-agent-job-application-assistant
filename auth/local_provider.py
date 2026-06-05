"""
Local Authentication Provider
===============================
SQLite + bcrypt auth — works immediately with no external service.

Design Decisions:
- bcrypt for password hashing (industry standard, adaptive cost factor).
- external_id is a UUID4 string, mimicking how Clerk would issue user IDs.
  This keeps the DB schema identical regardless of provider.
- All user state lives in the same SQLite database as job data.
- Provider string is "local" — queries can filter if multiple providers coexist.
"""

from __future__ import annotations

import uuid
from typing import Optional

import bcrypt
from loguru import logger

from auth.auth_interface import AuthProvider, AuthUser
from database.db_manager import DatabaseManager


class LocalAuthProvider(AuthProvider):
    """Authenticate users against the local SQLite users table."""

    PROVIDER_NAME = "local"

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # AuthProvider implementation
    # ------------------------------------------------------------------
    def register(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """Create a new local user with hashed password."""
        email = email.strip().lower()

        # Check for duplicate email
        existing = self.db.get_user_by_email(email)
        if existing:
            return False, "An account with this email already exists.", None

        # Hash password
        hashed = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=12),
        ).decode("utf-8")

        # Generate external id (like a Clerk user id)
        external_id = f"local_{uuid.uuid4().hex}"

        user_id = self.db.create_user(
            external_id=external_id,
            email=email,
            full_name=full_name,
            password_hash=hashed,
            provider=self.PROVIDER_NAME,
        )

        user = AuthUser(
            id=user_id,
            external_id=external_id,
            email=email,
            full_name=full_name,
            provider=self.PROVIDER_NAME,
        )
        logger.info("User registered: {} ({})", email, external_id)
        return True, "Account created successfully.", user

    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """Verify credentials and return the user."""
        email = email.strip().lower()
        row = self.db.get_user_by_email(email)

        if not row:
            return False, "No account found with this email.", None

        stored_hash = row["password_hash"]
        if not bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        ):
            return False, "Incorrect password.", None

        user = self._row_to_user(row)
        logger.info("User logged in: {}", email)
        return True, "Login successful.", user

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        row = self.db.get_user_by_internal_id(user_id)
        return self._row_to_user(row) if row else None

    def get_user_by_external_id(self, external_id: str) -> Optional[AuthUser]:
        row = self.db.get_user_by_external(external_id)
        return self._row_to_user(row) if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_user(row: dict) -> AuthUser:
        return AuthUser(
            id=row["id"],
            external_id=row["external_id"],
            email=row["email"],
            full_name=row["full_name"],
            provider=row["provider"],
        )
