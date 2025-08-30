import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers

def main():
    st.title("📦 Offers")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    if not auth.is_authenticated():
        st.warning("You need to log in to view or create offers.")
        st.stop()

    supabase = get_db()  # Supabase client
    profile_id = auth.get_current_profile_id()

    # -------------------------
    # Create a new offer
    # -------------------------
    st.subheader("Create a new offer")
    with st.form("offer_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        category = st.selectbox("Category", helpers.CATEGORIES)
        submitted = st.form_submit_button("Add Offer")

        if submitted:
            if not title:
                st.error("Title is required.")
            else:
                crud.create_offer(
                    supabase,
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
    res = supabase.table("offers").select("*").eq("profile_id", profile_id).execute()
    offers = res.data if res.data else []

    if offers:
        for o in offers:
            st.write(f"**{o.get('title', '—')}** - {o.get('category', '—')}")
            st.write(o.get('description', ''))
            st.write(f"Active: {o.get('is_active', True)}")

            # Delete button
            delete_key = f"delete_offer_{o.get('id')}"
            if st.button("Delete", key=delete_key):
                crud.delete_offer(supabase, o.get('id'))
                st.success(f"Offer '{o.get('title', '—')}' has been deleted.")
                helpers.rerun()

            st.write("---")
    else:
        st.info("You have no offers yet.")


if __name__ == "__main__":
    main()
