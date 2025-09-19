import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers

# -------------------------
# Main login/register page
# -------------------------
def main():
    st.title("🔑 Login / Register")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    db = get_db()

    # -------------------------
    # Already logged in
    # -------------------------
    user = auth.ensure_authenticated(db=db,required=False)
    if user:
        profile = crud.get_profile(db, user.id)
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
                    db = get_db()
                    try:
                        # Use Supabase sign_in_with_password for persistent session
                        auth_resp = db.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                    except Exception:
                        st.error("Invalid email or password.")
                        auth_resp = None

                    if auth_resp and getattr(auth_resp, "user", None):
                        auth.login_user(auth_resp)
                        profile = crud.get_profile(db, auth_resp.user.id)
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
                "Phone Number (No personal contact information would be shared with anyone unless you initiate or approve a match request. "
                "We will notify you via email when you have a match or match request.)",
                placeholder="+31101234567"
            )
            share_phone = st.checkbox(
                "Share the phone number **with matches** by default along with preferred mode of contact? "
                "(You can choose a preferred mode of contact while sending and accepting match requests.)", value=False
            )
            submitted = st.form_submit_button("Register")

            if submitted:
                if not full_name or not email or not pin_code or not password:
                    st.error("All fields are required.")
                elif password != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    db = get_db()
                    auth_resp = db.auth.sign_up({
                        "email": email,
                        "password": password,
                    })

                    if getattr(auth_resp, "user", None):
                        profile = crud.create_profile(
                            supabase_client=db,
                            supabase_id=auth_resp.user.id,
                            full_name=full_name,
                            postal_code=pin_code,
                            phone=phone,
                            email=email,
                            share_phone=share_phone
                        )
                        auth.login_user(auth_resp)
                        st.success(f"Account created! Welcome, {profile['full_name']}")
                        helpers.rerun()
                    else:
                        st.error("Failed to create account. Try again later.")


if __name__ == "__main__":
    main()
