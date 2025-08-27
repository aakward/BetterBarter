import streamlit as st

SESSION_KEY = "supabase_user_id"


def is_authenticated() -> bool:
    """Check if user ID is in session."""
    return SESSION_KEY in st.session_state


def get_current_user_id():
    """Get the current user's Supabase user ID from session."""
    return st.session_state.get(SESSION_KEY)


def login_user(user_id: str):
    """Store the Supabase user ID in session."""
    st.session_state[SESSION_KEY] = user_id


def logout_user():
    """Clear the session."""
    if SESSION_KEY in st.session_state:
        del st.session_state[SESSION_KEY]



