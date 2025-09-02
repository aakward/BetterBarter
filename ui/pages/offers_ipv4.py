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
    db = get_db()  # Supabase client
    user = auth.ensure_authenticated(db)
    profile_id = user.id

    # Karma header
    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")
        
    # -------------------------
    # Create a new offer
    # -------------------------
    st.subheader("Create a new offer")
    with st.form("offer_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        category = st.selectbox("Category", helpers.CATEGORIES)
        image_file = st.file_uploader(
            "Upload an image (optional, <2MB)", 
            type=["png", "jpg", "jpeg", "heic", "heif"]
        )
        submitted = st.form_submit_button("Add Offer")

        if submitted:
            if not title:
                st.error("Title is required.")
                st.stop()

            image_file_name = None  # store file name in DB, not signed URL
            if image_file:
                size_mb = len(image_file.getvalue()) / (1024 * 1024)
                if size_mb > MAX_IMAGE_SIZE_MB:
                    st.error("Image exceeds 2MB size limit.")
                    st.stop()

                # Generate unique file name
                ext = image_file.name.split(".")[-1].lower()
                image_file_name = f"{profile_id}_{uuid.uuid4().hex}.{ext}"

                # Upload file
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
                category=category,
                image_file_name=image_file_name
            )
            st.success(f"Offer '{title}' created successfully!")
            helpers.rerun()

    # -------------------------
    # List user's offers
    # -------------------------
    st.subheader("My Offers")
    offers = crud.get_all_offers(db, exclude_profile_id=None)
    user_offers = [o for o in offers if o["profile_id"] == profile_id]
    
    if user_offers:
        for o in user_offers:
            st.write(f"**{o['title']}** - {o.get('category', '—')}")
            st.write(o.get("description", ""))
            if o.get("image_file_name"):
                signed_url_resp = db.storage.from_(OFFER_BUCKET_NAME).create_signed_url(
                    o["image_file_name"], 60*60*24
                )
                st.image(signed_url_resp.get("signedURL"), width=200)
            st.write(f"Active: {o.get('is_active', True)}")

            # Delete button
            delete_key = f"delete_offer_{o['id']}"
            if st.button("Delete", key=delete_key):
                crud.delete_offer(db, o['id'])
                st.success(f"Offer '{o['title']}' has been deleted.")
                helpers.rerun()

            st.write("---")
    else:
        st.info("You have no offers yet.")


if __name__ == "__main__":
    main()
