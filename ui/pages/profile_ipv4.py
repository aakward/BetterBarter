import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers

def main():
    st.title("👤 Profile")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    db = get_db()  # Supabase client
    user = auth.ensure_authenticated(db)  # this will refresh/validate session
    profile_id = user.id


    # Get current profile
    profile = crud.get_profile(db, profile_id)
    if not profile:
        st.error("Profile not found.")
        return
    
    # Karma header
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")

    st.subheader("Profile Details")
    st.write(f"**Full Name:** {profile.get('full_name', '—')}")
    st.write(f"**Email Address:** {profile.get('email', '—')}")
    st.caption("Notifications regarding matches would be sent to this email address")
    st.write(f"**Postal Code:** {profile.get('postal_code', '—')}")
    st.write(f"**Member since:** {profile.get('created_at', '—')[:10]}")
    st.write(f"**Phone shared:** {'Yes' if profile.get('share_phone') else 'No'}")
    st.write(f"**Karma:** {profile.get('karma', 0)}")

    st.write("---")
    st.subheader("Update Profile")

    with st.form("update_profile_form"):
        new_name = st.text_input("Full Name", value=profile.get('full_name', ''))
        new_pin = st.text_input("Postal Code", value=profile.get('postal_code', ''))
        phone = st.text_input("Phone Number (optional)", value="")
        share_phone = st.checkbox("Share phone with matches?", value=profile.get('share_phone', False))
        submitted = st.form_submit_button("Save Changes")

        if submitted:
            update_data = {}
            if new_name != profile.get('full_name'):
                update_data["full_name"] = new_name
            if new_pin != profile.get('postal_code'):
                update_data["postal_code"] = new_pin
            if phone:
                update_data["phone_hash"] = helpers.hash_phone(phone)
            update_data["share_phone"] = share_phone

            if update_data:
                crud.update_profile(db, profile_id, **update_data)
                st.success("Profile updated successfully!")
                helpers.rerun()
            else:
                st.info("No changes detected.")

    st.write("---")
    if st.button("Log out"):
        auth.logout_user(db)
        st.success("Logged out successfully.")
        helpers.rerun()


if __name__ == "__main__":
    main()
