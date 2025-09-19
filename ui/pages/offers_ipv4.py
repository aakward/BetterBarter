import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers
import uuid

MAX_IMAGE_SIZE_MB = 2
OFFER_BUCKET_NAME = "offer-images"

def main():
    st.title("📦 Offers")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    # -------------------------
    # Authentication
    # -------------------------
    db = get_db()
    user = auth.ensure_authenticated(db=db)
    profile_id = user.id

    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")

    # -------------------------
    # Initialize session state for category/subcategory
    # -------------------------
    if "category" not in st.session_state:
        st.session_state.category = list(helpers.CATEGORIES.keys())[0]
    if "subcategory" not in st.session_state:
        st.session_state.subcategory = helpers.CATEGORIES[st.session_state.category][0]

    # -------------------------
    # Tabs: Create / My Offers
    # -------------------------
    tab_create, tab_list = st.tabs(["Create Offer", "My Offers"])

    # -------------------------
    # Create Offer Tab
    # -------------------------
    with tab_create:
        st.subheader("Create a new offer")

        # Category/Subcategory container (outside form but visually coherent)
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "Category",
                    list(helpers.CATEGORIES.keys()),
                    key="category",
                    on_change=lambda: st.session_state.update({
                        "subcategory": helpers.CATEGORIES[st.session_state.category][0]
                    })
                )
            with col2:
                st.selectbox(
                    "Subcategory",
                    helpers.CATEGORIES[st.session_state.category],
                    key="subcategory"
                )

        # Form for creating a new offer
        with st.form("offer_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            image_file = st.file_uploader(
                "Upload an image (optional, <2MB)",
                type=["png", "jpg", "jpeg", "heic", "heif"]
            )
            submitted = st.form_submit_button("Add Offer")

            if submitted:
                if not title:
                    st.error("Title is required.")
                    st.stop()

                image_file_name = None
                if image_file:
                    size_mb = len(image_file.getvalue()) / (1024 * 1024)
                    if size_mb > MAX_IMAGE_SIZE_MB:
                        st.error("Image exceeds 2MB size limit.")
                        st.stop()

                    ext = image_file.name.split(".")[-1].lower()
                    image_file_name = f"{profile_id}_{uuid.uuid4().hex}.{ext}"

                    try:
                        res = db.storage.from_(OFFER_BUCKET_NAME).upload(
                            image_file_name, image_file.getvalue()
                        )
                        if res and isinstance(res, dict) and res.get("error"):
                            st.error("Error uploading image: " + str(res["error"]["message"]))
                            st.stop()
                    except Exception as e:
                        st.error(f"Unexpected error while uploading image: {e}")
                        st.stop()

                crud.create_offer(
                    supabase_client=db,
                    profile_id=profile_id,
                    title=title,
                    description=description,
                    category=st.session_state.category,
                    subcategory=st.session_state.subcategory,
                    image_file_name=image_file_name
                )
                st.success(f"Offer '{title}' created successfully!")
                helpers.rerun()

    # -------------------------
    # List Offers Tab
    # -------------------------
    with tab_list:
        st.subheader("My Offers")
        offers = crud.get_all_offers(db, exclude_profile_id=None, include_inactive=True)
        user_offers = [o for o in offers if o["profile_id"] == profile_id]

        if user_offers:
            for o in user_offers:
                st.write(f"**{o['title']}** - {o.get('category', '—')} : {o.get('subcategory', '—')}")
                st.write(o.get("description", ""))
                if o.get("image_file_name"):
                    signed_url_resp = db.storage.from_(OFFER_BUCKET_NAME).create_signed_url(
                        o["image_file_name"], 60*60*24
                    )
                    st.image(signed_url_resp.get("signedURL"), width=200)

                st.write(f"Status: {'Active' if o.get('is_active', True) else 'Inactive'}")

                # Deactivate / Reactivate buttons
                if o.get("is_active", True):
                    deactivate_key = f"deactivate_offer_{o['id']}"
                    if st.button("Deactivate", key=deactivate_key):
                        try:
                            crud.toggle_offer_active(db, o['id'], False)
                            st.success(f"Offer '{o['title']}' has been deactivated.")
                            helpers.rerun()
                        except Exception as e:
                            st.error(f"Failed to deactivate offer: {e}")
                else:
                    reactivate_key = f"reactivate_offer_{o['id']}"
                    if st.button("Reactivate", key=reactivate_key):
                        try:
                            crud.toggle_offer_active(db, o['id'], True)
                            st.success(f"Offer '{o['title']}' has been reactivated.")
                            helpers.rerun()
                        except Exception as e:
                            st.error(f"Failed to reactivate offer: {e}")

                # Delete button
                delete_key = f"delete_offer_{o['id']}"
                if st.button("Delete", key=delete_key):
                    try:
                        crud.delete_offer(db, o['id'])
                        st.success(f"Offer '{o['title']}' has been deleted.")
                        helpers.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete offer: {e}")

                st.write("---")
        else:
            st.info("You have no offers yet.")


if __name__ == "__main__":
    main()
