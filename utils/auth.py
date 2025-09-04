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


def logout_user(db=None):
    """Clear the session."""
    # Clear Streamlit session key
    if SESSION_KEY in st.session_state:
        del st.session_state[SESSION_KEY]

    # Clear Supabase session if a client is provided
    if db is not None:
        try:
            db.auth.sign_out()
        except Exception as e:
            st.warning(f"Error signing out of Supabase: {e}")



def ensure_authenticated(db: Client, required: bool = True):
    """
    Ensures the current Supabase session is valid.
    Returns the user object if valid.
    If required=False, returns None instead of stopping execution.
    """
    try:
        user_resp = db.auth.get_user()
        if user_resp and user_resp.user:
            st.session_state[SESSION_KEY] = user_resp.user.id
            return user_resp.user
        else:
            try:
                session = db.auth.refresh_session()
                if session and session.user:
                    st.session_state[SESSION_KEY] = session.user.id
                    return session.user
            except AuthSessionMissingError:
                pass

        if required:
            st.error("Your session has expired or you are not logged in. Please log in again.")
            st.stop()
        return None  # not required → just return None

    except Exception as e:
        if required:
            st.error(f"Error checking authentication: {e}")
            st.stop()
        return None





