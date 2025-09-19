import streamlit as st
from supabase import Client
from data.db_ipv4 import get_db  # per-user client

SESSION_KEY_USER = "supabase_user_id"
SESSION_KEY_SESSION = "supabase_session"


def is_authenticated() -> bool:
    """Check if user is logged in by looking at session_state."""
    return SESSION_KEY_USER in st.session_state


def get_current_profile_id():
    """Return the current user's Supabase profile ID (stored in session_state)."""
    return st.session_state.get(SESSION_KEY_USER)


def login_user(auth_resp):
    """
    Save the Supabase session and user_id to st.session_state.
    Accepts either:
        - AuthResponse (from sign_in/sign_up), or
        - Supabase User object (from crud.authenticate_user)
    """
    if not auth_resp:
        raise ValueError("Invalid auth response from Supabase")

    # If auth_resp has .session and .user, it’s a full AuthResponse
    if hasattr(auth_resp, "session") and hasattr(auth_resp, "user"):
        session = auth_resp.session
        st.session_state[SESSION_KEY_SESSION] = {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }
        st.session_state[SESSION_KEY_USER] = auth_resp.user.id
    else:
        # Fallback: only a User object
        st.session_state[SESSION_KEY_USER] = auth_resp.id
        st.session_state.pop(SESSION_KEY_SESSION, None)  # no session


def logout_user():
    """Clear the Supabase session from st.session_state and sign out."""
    db: Client = get_db()

    # Try to sign out from Supabase server-side
    try:
        db.auth.sign_out()
    except Exception as e:
        st.warning(f"Error signing out of Supabase: {e}")

    # Clear local session state
    st.session_state.pop(SESSION_KEY_USER, None)
    st.session_state.pop(SESSION_KEY_SESSION, None)


def ensure_authenticated(db: Client | None = None, required: bool = True):
    """
    Ensures the current Supabase session is valid.
    Returns the user object if valid.
    If required=False, returns None instead of stopping execution.
    """
    db = db or get_db()

    try:
        user_resp = db.auth.get_user()
        if user_resp and getattr(user_resp, "user", None):
            st.session_state[SESSION_KEY_USER] = user_resp.user.id
            return user_resp.user

        # Try restoring session from st.session_state
        if SESSION_KEY_SESSION in st.session_state:
            session = st.session_state[SESSION_KEY_SESSION]
            refreshed = db.auth.set_session(
                session["access_token"],
                session["refresh_token"],
            )
            if refreshed and getattr(refreshed, "user", None):
                st.session_state[SESSION_KEY_USER] = refreshed.user.id
                return refreshed.user

        if required:
            st.error("Your session has expired or you are not logged in. Please log in again.")
            st.stop()

        return None

    except Exception as e:
        if required:
            st.error(f"Authentication error: {e}")
            st.stop()
        return None
