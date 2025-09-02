import streamlit as st
from data import crud
from data.db import get_db
import data.db_ipv4 as sp
from utils import auth, helpers
import uuid

MAX_IMAGE_SIZE_MB = 2
OFFER_BUCKET_NAME = "offer-images"

def main():
    st.title("📦 Offers")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    if not auth.is_authenticated():
        st.warning("You need to log in to view or create offers.")
        st.stop()

    db = next(get_db())
    profile_id = auth.get_current_profile_id()


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
            
            image_file_name = None
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
                    res = sp.supabase.storage.from_(OFFER_BUCKET_NAME).upload(
                        image_file_name, image_file.getvalue()
                    )
                    if res and isinstance(res, dict) and res.get("error"):
                        st.error("Error uploading image: " + str(res["error"]["message"]))
                        st.stop()
                except Exception as e:
                    st.error(f"Unexpected error while uploading image: {e}")
                    st.stop()
                    
            crud.create_offer(
                db=db,
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
    offers = db.query(crud.models.Offer).filter(crud.models.Offer.profile_id == profile_id).all()
    
    if offers:
        for o in offers:
            st.write(f"**{o.title}** - {o.category}")
            st.write(o.description)
            if o.get("image_file_name"):
                signed_url_resp = sp.supabase.storage.from_(OFFER_BUCKET_NAME).create_signed_url(
                    o["image_file_name"], 60*60*24
                )
                st.image(signed_url_resp.get("signedURL"), width=200)
            st.write(f"Active: {o.get('is_active', True)}")

            # Delete button
            delete_key = f"delete_offer_{o.id}"
            if st.button("Delete", key=delete_key):
                crud.delete_offer(db, o.id)
                st.success(f"Offer '{o.title}' has been deleted.")
                helpers.rerun()

            st.write("---")
    else:
        st.info("You have no offers yet.")

if __name__ == "__main__":
    main()
