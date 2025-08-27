import streamlit as st
from data import crud
from data.db import get_db
from utils import auth, helpers

def main():
    st.title("📬 Requests")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False
        
    if not auth.is_authenticated():
        st.warning("You need to log in to view or create requests.")
        st.stop()

    db = next(get_db())
    profile_id = auth.get_current_user_id()

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
                    db,
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
    requests = db.query(crud.models.Request).filter(crud.models.Request.profile_id == profile_id).all()
    if requests:
        for r in requests:
            st.write(f"**{r.title}** - {r.category}")
            st.write(r.description)
            st.write(f"Active: {r.is_active}")
            st.write("---")
    else:
        st.info("You have no requests yet.")

if __name__ == "__main__":
    main()
