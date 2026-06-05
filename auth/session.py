"""
Streamlit Session Manager
==========================
Manages authentication state within Streamlit's session_state.

Design Decisions:
- All auth state is stored in st.session_state (Streamlit's native mechanism).
- Provides clean get/set/clear helpers so auth logic isn't scattered across UI code.
- Decoupled from the auth provider — works with local, Clerk, or any future provider.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from auth.auth_interface import AuthUser


# Session state keys (namespaced to avoid collisions)
_KEY_USER = "auth_user"
_KEY_AUTHENTICATED = "auth_is_authenticated"


def set_authenticated_user(user: AuthUser) -> None:
    """Store the authenticated user in Streamlit session state."""
    st.session_state[_KEY_USER] = user
    st.session_state[_KEY_AUTHENTICATED] = True


def get_current_user() -> Optional[AuthUser]:
    """Return the current authenticated user, or None."""
    if st.session_state.get(_KEY_AUTHENTICATED):
        return st.session_state.get(_KEY_USER)
    return None


def is_authenticated() -> bool:
    """Check if a user is currently logged in."""
    return bool(st.session_state.get(_KEY_AUTHENTICATED, False))


def logout() -> None:
    """Clear authentication state."""
    st.session_state.pop(_KEY_USER, None)
    st.session_state.pop(_KEY_AUTHENTICATED, None)


def require_auth() -> AuthUser:
    """
    Gate function — returns the current user or stops the Streamlit script.

    Usage in any page:
        user = require_auth()
        # everything below only runs if authenticated
    """
    user = get_current_user()
    if not user:
        st.warning("Please sign in to continue.")
        st.stop()
    return user
