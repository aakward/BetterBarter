import streamlit as st
from data import crud
from data.db import get_db
from utils import auth, helpers

def main():
    st.title("📦 Offers")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False
        
    if not auth.is_authenticated():
        st.warning("You need to log in to view or create offers.")
        st.stop()

    db = next(get_db())
    profile_id = auth.get_current_user_id()

    # -------------------------
    # Create a new offer
    # -------------------------
    st.subheader("Create a new offer")
    with st.form("offer_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        category = st.text_input("Category")
        submitted = st.form_submit_button("Add Offer")

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                crud.create_offer(
                    db,
                    profile_id=profile_id,
                    title=title,
                    description=description,
                    category=category
                )
                st.success(f"Offer '{title}' created successfully!")
                helpers.rerun()

    # -------------------------
    # List user's offers
    # -------------------------
    st.subheader("My Offers")
    offers = db.query(crud.models.Offer).filter(crud.models.Offer.profile_id == profile_id).all()
    if offers:
        for o in offers:
            st.write(f"**{o.title}** - {o.category}")
            st.write(o.description)
            st.write(f"Active: {o.is_active}")
            st.write("---")
    else:
        st.info("You have no offers yet.")

if __name__ == "__main__":
    main()
