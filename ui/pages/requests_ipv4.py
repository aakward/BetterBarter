import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers

def main():
    st.title("📬 Requests")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    if not auth.is_authenticated():
        st.warning("You need to log in to view or create requests.")
        st.stop()

    db = get_db()  # Supabase client
    profile_id = auth.get_current_profile_id()

    # -------------------------
    # Create a new request
    # -------------------------
    st.subheader("Create a new request")
    with st.form("request_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        category = st.text_input("Category")
        submitted = st.form_submit_button("Add Request")

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                crud.create_request(
                    supabase_client=db,
                    profile_id=profile_id,
                    title=title,
                    description=description,
                    category=category
                )
                st.success(f"Request '{title}' created successfully!")
                helpers.rerun()

    # -------------------------
    # List user's requests
    # -------------------------
    st.subheader("My Requests")
    requests = crud.get_all_requests(db, exclude_profile_id=None)  # fetch all requests

    # Filter to only user's requests
    user_requests = [r for r in requests if r["profile_id"] == profile_id]

    if user_requests:
        for r in user_requests:
            st.write(f"**{r['title']}** - {r.get('category', '—')}")
            st.write(r.get("description", ""))
            st.write(f"Active: {r.get('is_active', True)}")

            # Delete button
            delete_key = f"delete_request_{r['id']}"
            if st.button("Delete", key=delete_key):
                crud.delete_request(db, r['id'])
                st.success(f"Request '{r['title']}' has been deleted.")
                helpers.rerun()

            st.write("---")
    else:
        st.info("You have no requests yet.")


if __name__ == "__main__":
    main()
