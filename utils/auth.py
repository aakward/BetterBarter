import streamlit as st
from supabase import AuthSessionMissingError, Client

SESSION_KEY = "supabase_user_id"


def is_authenticated() -> bool:
    """Check if user ID is in session."""
    return SESSION_KEY in st.session_state


def get_current_profile_id():
    """Get the current user's Supabase user ID from session."""
    return st.session_state.get(SESSION_KEY)


def login_user(user_id: str):
    """Store the Supabase user ID in session."""
    st.session_state[SESSION_KEY] = user_id


def logout_user():
    """Clear the session."""
    if SESSION_KEY in st.session_state:
        del st.session_state[SESSION_KEY]


def ensure_authenticated(db: Client):
    """
    Ensures the current Supabase session is valid.
    Returns the user object if valid.
    Stops execution if no valid session.
    """
    try:
        user_resp = db.auth.get_user()
        if user_resp and user_resp.user:
            st.session_state[SESSION_KEY] = user_resp.user.id
            return user_resp.user
        else:
            # Try to refresh session
            try:
                session = db.auth.refresh_session()
                if session and session.user:
                    st.session_state[SESSION_KEY] = session.user.id
                    return session.user
            except AuthSessionMissingError:
                pass

        # No valid session
        st.error("Your session has expired or you are not logged in. Please log in again.")
        st.stop()

    except Exception as e:
        st.error(f"Error checking authentication: {e}")
        st.stop()




