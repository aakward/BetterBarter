import streamlit as st
from data import crud
from data.db import get_db
import data.db_ipv4 as sp
from utils import auth, helpers
import uuid

MAX_IMAGE_SIZE_MB = 2
REQUEST_BUCKET_NAME = "request-images"

def main():
    st.title("📬 Requests")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    if not auth.is_authenticated():
        st.warning("You need to log in to view or create requests.")
        st.stop()

    db = next(get_db())
    profile_id = auth.get_current_profile_id()

    # -------------------------
    # Create a new request
    # -------------------------
    st.subheader("Create a new request")
    with st.form("request_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        category = st.selectbox("Category", helpers.CATEGORIES)
        image_file = st.file_uploader(
            "Upload an image (optional, <2MB)", 
            type=["png", "jpg", "jpeg", "heic", "heif"]
        )
        submitted = st.form_submit_button("Add Request")

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
                    res = sp.supabase.storage.from_(REQUEST_BUCKET_NAME).upload(
                        image_file_name, image_file.getvalue()
                    )
                    if res and isinstance(res, dict) and res.get("error"):
                        st.error("Error uploading image: " + str(res["error"]["message"]))
                        st.stop()
                except Exception as e:
                    st.error(f"Unexpected error while uploading image: {e}")
                    st.stop()
                    
            crud.create_request(
                db=db,
                profile_id=profile_id,
                title=title,
                description=description,
                category=category,
                image_file_name=image_file_name
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
            if r.get("image_file_name"):
                signed_url_resp = sp.supabase.storage.from_(REQUEST_BUCKET_NAME).create_signed_url(
                    r["image_file_name"], 60*60*24
                )
                st.image(signed_url_resp.get("signedURL"), width=200)
            st.write(f"Active: {r.get('is_active', True)}")

            # Delete button
            delete_key = f"delete_request_{r.id}"
            if st.button("Delete", key=delete_key):
                crud.delete_request(db, r.id)
                st.success(f"Request '{r.title}' has been deleted.")
                helpers.rerun()

            st.write("---")
    else:
        st.info("You have no requests yet.")

if __name__ == "__main__":
    main()
