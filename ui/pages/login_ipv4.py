import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_ANON_KEY = st.secrets["SUPABASE_ANON_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def main():
    st.title("🔑 Login / Register")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    db = get_db()  # Supabase client

    # -------------------------
    # Already logged in
    # -------------------------
    if auth.is_authenticated():
        profile_id = auth.get_current_profile_id()
        profile = crud.get_profile(db, profile_id)
        if profile:
            st.success(f"Welcome back, **{profile['full_name']}**!")
        if st.button("Log out"):
            auth.logout_user()
            helpers.rerun()
        st.stop()

    # -------------------------
    # Tabs: Login / Register
    # -------------------------
    tab1, tab2 = st.tabs(["Login", "Register"])

    # -------------------------
    # Existing User Login
    # -------------------------
    with tab1:
        st.subheader("Existing User Login")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

            if submitted:
                if not email or not password:
                    st.error("Email and password are required.")
                else:
                    user = crud.authenticate_user(db, email=email, password=password)
                    if user:
                        auth.login_user(user.id)
                        profile = crud.get_profile(db, user.id)
                        if profile:
                            st.success(f"Logged in as {profile['full_name']}")
                        helpers.rerun()
                    else:
                        st.error("Invalid email or password.")

    # -------------------------
    # New User Registration
    # -------------------------
    with tab2:
        st.subheader("New User Registration")
        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Jane Doe")
            email = st.text_input("Email", placeholder="your@email.com")
            pin_code = st.text_input("Postal Code", placeholder="1012AB")
            password = st.text_input("Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            phone = st.text_input(
                "WhatsApp Number (Phone Numbers would only be shared with matches once you approve a match request. "
                "We will notify you via email when you have a match.)",
                placeholder="+31101234567"
            )
            share_phone = st.checkbox(
                "Share phone with matches without waiting for approval?", value=False
            )
            submitted = st.form_submit_button("Register")

            if submitted:
                if not full_name or not email or not pin_code or not password:
                    st.error("All fields are required.")
                elif password != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    # Create user in Supabase Auth
                    supabase_user = supabase.auth.sign_up({
                        "email": email,
                        "password": password,
                    })

                    if supabase_user.user:
                        # Create profile in Supabase table
                        profile = crud.create_profile(
                            supabase_client=db,
                            supabase_id=supabase_user.user.id,
                            full_name=full_name,
                            postal_code=pin_code,
                            phone=phone,
                            share_phone=share_phone
                        )
                        auth.login_user(profile["id"])
                        st.success(f"Account created! Welcome, {profile['full_name']}")
                        helpers.rerun()
                    else:
                        st.error("Failed to create account. Try again later.")


if __name__ == "__main__":
    main()
