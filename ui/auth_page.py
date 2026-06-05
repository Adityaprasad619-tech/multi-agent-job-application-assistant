"""
Authentication UI Component
=============================
Streamlit-native login/register forms.

Design Decisions:
- Self-contained component — call render_auth_page() and it handles everything.
- Uses st.tabs for login/register toggle (clean, no page reload).
- Password validation rules enforced client-side before hitting the provider.
- After successful auth, sets session state and triggers a rerun to show the main app.
"""

from __future__ import annotations

import streamlit as st

from auth.auth_interface import AuthProvider
from auth.session import set_authenticated_user


def render_auth_page(auth_provider: AuthProvider) -> None:
    """
    Render the full login / register page.

    Called from app.py when the user is not authenticated.
    """
    # Center the auth form
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.markdown("## Job Application Assistant")
        st.markdown("Sign in to access your personalized job search dashboard.")
        st.markdown("---")

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            _render_login(auth_provider)

        with tab_register:
            _render_register(auth_provider)


def _render_login(provider: AuthProvider) -> None:
    """Login form."""
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please fill in both fields.")
            return

        success, message, user = provider.login(email, password)
        if success and user:
            set_authenticated_user(user)
            st.success(message)
            st.rerun()
        else:
            st.error(message)


def _render_register(provider: AuthProvider) -> None:
    """Registration form."""
    with st.form("register_form", clear_on_submit=False):
        full_name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted:
        # Validation
        if not all([full_name, email, password, confirm]):
            st.error("All fields are required.")
            return
        if password != confirm:
            st.error("Passwords do not match.")
            return
        if len(password) < 8:
            st.error("Password must be at least 8 characters.")
            return

        success, message, user = provider.register(email, password, full_name)
        if success and user:
            set_authenticated_user(user)
            st.success(message)
            st.rerun()
        else:
            st.error(message)
