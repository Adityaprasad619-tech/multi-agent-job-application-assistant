"""
Clerk Authentication Provider (Stub)
======================================
Placeholder for future Clerk integration.

When ready to use Clerk:
1. pip install clerk-backend-api  (or use requests to call Clerk's REST API)
2. Implement the methods below using Clerk's Backend API:
   - Verify session tokens / JWTs
   - Fetch user details from Clerk
   - Sync user records to local SQLite

Clerk API docs: https://clerk.com/docs/reference/backend-api

NOTE: Clerk is designed for React/Next.js frontends. For a Streamlit app,
you would need to:
  - Host a small auth page (React/HTML) that handles Clerk sign-in
  - Pass the session token back to Streamlit via query params or cookies
  - Verify the token server-side using Clerk's Backend API

This stub is included so the architecture is ready if/when you add a
JS-based frontend or migrate away from Streamlit.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from auth.auth_interface import AuthProvider, AuthUser
from database.db_manager import DatabaseManager


class ClerkAuthProvider(AuthProvider):
    """
    Clerk-backed authentication provider.

    Requires CLERK_SECRET_KEY for Backend API calls.
    Currently a stub — raises NotImplementedError.
    """

    PROVIDER_NAME = "clerk"

    def __init__(
        self,
        db: DatabaseManager,
        secret_key: str,
        publishable_key: str,
    ) -> None:
        self.db = db
        self.secret_key = secret_key
        self.publishable_key = publishable_key
        logger.info("ClerkAuthProvider initialized (stub mode)")

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """
        Clerk handles registration via its hosted UI.
        This method would sync a Clerk-created user to local DB.
        """
        raise NotImplementedError(
            "Clerk registration is handled by the Clerk frontend widget. "
            "Use sync_clerk_user() after Clerk sign-up completes."
        )

    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[bool, str, Optional[AuthUser]]:
        """
        Clerk handles login via its hosted UI.
        This method would verify a Clerk session token.
        """
        raise NotImplementedError(
            "Clerk login is handled by the Clerk frontend widget. "
            "Use verify_session_token() to validate a session."
        )

    def get_user_by_id(self, user_id: int) -> Optional[AuthUser]:
        row = self.db.get_user_by_internal_id(user_id)
        return self._row_to_user(row) if row else None

    def get_user_by_external_id(self, external_id: str) -> Optional[AuthUser]:
        row = self.db.get_user_by_external(external_id)
        return self._row_to_user(row) if row else None

    # ------------------------------------------------------------------
    # Future: Clerk-specific methods
    # ------------------------------------------------------------------
    def verify_session_token(self, token: str) -> Optional[AuthUser]:
        """
        TODO: Verify a Clerk session JWT and return the user.

        Steps:
        1. Decode JWT using Clerk's JWKS endpoint.
        2. Extract clerk_user_id from the 'sub' claim.
        3. Look up or create the user in local DB.
        4. Return AuthUser.
        """
        raise NotImplementedError("Clerk JWT verification not yet implemented.")

    def sync_clerk_user(
        self,
        clerk_user_id: str,
        email: str,
        full_name: str,
    ) -> AuthUser:
        """
        TODO: Sync a Clerk user to local DB after sign-up/sign-in.

        This ensures we have a local record for FK relationships.
        """
        raise NotImplementedError("Clerk user sync not yet implemented.")

    @staticmethod
    def _row_to_user(row: dict) -> AuthUser:
        return AuthUser(
            id=row["id"],
            external_id=row["external_id"],
            email=row["email"],
            full_name=row["full_name"],
            provider=row["provider"],
        )
