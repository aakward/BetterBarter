import streamlit as st
from data import crud, models
from data.db import get_db
from utils import auth, helpers


def main():
    st.title("👤 Profile")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    db = next(get_db())

    if not auth.is_authenticated():
        st.warning("You need to log in first.")
        return

    # Get current profile
    profile_id = auth.get_current_profile_id()
    profile = db.query(models.Profile).filter(models.Profile.id == profile_id).first()
    if not profile:
        st.error("Profile not found.")
        return

    st.subheader("Profile Details")
    st.write(f"**Full Name:** {profile.full_name}")
    st.write(f"**Postal Code:** {profile.postal_code}")
    st.write(f"**Member since:** {profile.created_at.strftime('%Y-%m-%d')}")
    st.write(f"**Phone shared:** {'Yes' if profile.share_phone else 'No'}")

    st.write("---")
    st.subheader("Update Profile")

    with st.form("update_profile_form"):
        new_name = st.text_input("Full Name", value=profile.full_name)
        new_pin = st.text_input("Postal Code", value=profile.postal_code)
        phone = st.text_input("Phone Number (optional)", value="")
        share_phone = st.checkbox("Share phone with matches?", value=profile.share_phone)
        submitted = st.form_submit_button("Save Changes")

        if submitted:
            update_data = {}
            if new_name != profile.full_name:
                update_data["full_name"] = new_name
            if new_pin != profile.postal_code:
                update_data["postal_code"] = new_pin
            if phone:
                update_data["phone_hash"] = helpers.hash_phone(phone)
            update_data["share_phone"] = share_phone

            if update_data:
                crud.update_profile(db, profile_id=profile.id, **update_data)
                st.success("Profile updated successfully!")
                helpers.rerun()
            else:
                st.info("No changes detected.")

    st.write("---")
    if st.button("Log out"):
        auth.logout_user()
        st.success("Logged out successfully.")
        helpers.rerun()


if __name__ == "__main__":
    main()
