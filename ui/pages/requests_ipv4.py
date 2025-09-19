import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth, helpers
import uuid

MAX_IMAGE_SIZE_MB = 2
REQUEST_BUCKET_NAME = "request-images"

def main():
    st.title("📬 Requests")

    if "rerun_flag" not in st.session_state:
        st.session_state["rerun_flag"] = False

    # -------------------------
    # Authentication
    # -------------------------
    db = get_db()
    user = auth.ensure_authenticated()
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
    # Tabs: Create / My Requests
    # -------------------------
    tab_create, tab_list = st.tabs(["Create Request", "My Requests"])

    # -------------------------
    # Create Request Tab
    # -------------------------
    with tab_create:
        st.subheader("Create a new request")

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

        # Form for creating a new request
        with st.form("request_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
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

                    ext = image_file.name.split(".")[-1].lower()
                    image_file_name = f"{profile_id}_{uuid.uuid4().hex}.{ext}"

                    try:
                        res = db.storage.from_(REQUEST_BUCKET_NAME).upload(
                            image_file_name, image_file.getvalue()
                        )
                        if res and isinstance(res, dict) and res.get("error"):
                            st.error("Error uploading image: " + str(res["error"]["message"]))
                            st.stop()
                    except Exception as e:
                        st.error(f"Unexpected error while uploading image: {e}")
                        st.stop()

                crud.create_request(
                    supabase_client=db,
                    profile_id=profile_id,
                    title=title,
                    description=description,
                    category=st.session_state.category,
                    subcategory=st.session_state.subcategory,
                    image_file_name=image_file_name
                )
                st.success(f"Request '{title}' created successfully!")
                helpers.rerun()

    # -------------------------
    # List Requests Tab
    # -------------------------
    with tab_list:
        st.subheader("My Requests")
        requests = crud.get_all_requests(db, exclude_profile_id=None, include_inactive=True)
        user_requests = [r for r in requests if r["profile_id"] == profile_id]

        if user_requests:
            for r in user_requests:
                st.write(f"**{r['title']}** - {r.get('category', '—')} : {r.get('subcategory', '—')}")
                st.write(r.get("description", ""))
                if r.get("image_file_name"):
                    signed_url_resp = db.storage.from_(REQUEST_BUCKET_NAME).create_signed_url(
                        r["image_file_name"], 60*60*24
                    )
                    st.image(signed_url_resp.get("signedURL"), width=200)

                st.write(f"Status: {'Active' if r.get('is_active', True) else 'Inactive'}")

                # Deactivate / Reactivate buttons
                if r.get("is_active", True):
                    deactivate_key = f"deactivate_request_{r['id']}"
                    if st.button("Deactivate", key=deactivate_key):
                        try:
                            crud.toggle_request_active(db, r['id'], False)
                            st.success(f"Request '{r['title']}' has been deactivated.")
                            helpers.rerun()
                        except Exception as e:
                            st.error(f"Failed to deactivate request: {e}")
                else:
                    reactivate_key = f"reactivate_request_{r['id']}"
                    if st.button("Reactivate", key=reactivate_key):
                        try:
                            crud.toggle_request_active(db, r['id'], True)
                            st.success(f"Request '{r['title']}' has been reactivated.")
                            helpers.rerun()
                        except Exception as e:
                            st.error(f"Failed to reactivate request: {e}")

                # Delete button
                delete_key = f"delete_request_{r['id']}"
                if st.button("Delete", key=delete_key):
                    try:
                        crud.delete_request(db, r['id'])
                        st.success(f"Request '{r['title']}' has been deleted.")
                        helpers.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete request: {e}")

                st.write("---")
        else:
            st.info("You have no requests yet.")


if __name__ == "__main__":
    main()
