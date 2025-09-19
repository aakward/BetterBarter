import streamlit as st
from data import crud, models
from data.db import get_db
import data.db_ipv4 as sp
from utils import auth

REQUEST_BUCKET_NAME = "request-images"  # same as requests.py
OFFER_BUCKET_NAME = "offer-images"      # adjust if your offers use a different bucket

def create_signed_url(db, bucket: str, file_name: str, expires_sec: int = 60 * 60 * 24) -> str | None:
    """Return a signed URL for a stored file name, or None on failure."""
    if not file_name:
        return None
    try:
        resp = sp.supabase.storage.from_(bucket).create_signed_url(file_name, expires_sec)
        # Supabase python client returns {"signedURL": "...", "signedUrl": "..."} – prefer "signedURL"
        return resp.get("signedURL") or resp.get("signedUrl")
    except Exception:
        return None
    
def main():
    st.title("📰 Feeds")

    user = auth.ensure_authenticated(db=db)
    profile_id = user.id

    db = next(get_db())

    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile.karma}**")

    # -------------------------
    # Requests Section
    # -------------------------
    st.header("📌 Requests")
    requests = crud.get_all_requests(db, exclude_profile_id=profile_id)
    if requests:
        for req in requests:
            col1, col2 = st.columns([3, 2], vertical_alignment="center")


            with col1:
                st.markdown(f"**{req.title}** *(by {req.profile.full_name}, {req.profile.postal_code})*")
                if req.description:
                    st.caption(req.description)

                # Show associated image (if any) using file name -> signed URL
                image_file_name = req.get("image_file_name")
                if image_file_name:
                    url = create_signed_url(db, REQUEST_BUCKET_NAME, image_file_name)
                    if url:
                        st.image(url, width=200)

            with col2:
                existing_match = crud.get_existing_match_request(
                    db, profile_id, request_id=req.id, offer_id=None
                )
                if existing_match:
                    st.success("✅ Match request sent")
                else:
                    msg_key = f"req_msg_{req['id']}"
                    btn_key = f"req_btn_{req['id']}"
                    custom_message = st.text_area(
                        "Custom message (optional)",
                        key=msg_key,
                        placeholder="Add a personal note..."
                    )
                    if st.button("📩 Request Match", key=btn_key):
                        if crud.can_send_match_request(db, profile_id):
                            try:
                                match_req = crud.create_match_request(
                                    db,
                                    requester_id=profile_id,
                                    request_id=req.id,
                                    offer_id=None,
                                    message=custom_message
                                )
                                if match_req:
                                    st.success("✅ Match request sent successfully!")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")
                        else:
                            st.error("⚠️ Daily limit reached")
    else:
        st.info("No requests available right now.")

    # -------------------------
    # Offers Section
    # -------------------------
    st.header("🎁 Offers")
    offers = crud.get_all_offers(db, exclude_profile_id=profile_id)
    if offers:
        for off in offers:
            col1, col2 = st.columns([3, 2], vertical_alignment="center")

            with col1:
                st.markdown(f"**{off.title}** *(by {off.profile.full_name}, {off.profile.postal_code})*")
                if off.description:
                    st.caption(off.description)
                
                # Show associated image (if any) using file name -> signed URL
                image_file_name = off.get("image_file_name")
                if image_file_name:
                    url = create_signed_url(db, OFFER_BUCKET_NAME, image_file_name)
                    if url:
                        st.image(url, width=200)

            with col2:
                existing_match = crud.get_existing_match_request(
                    db, profile_id, offer_id=off.id, request_id=None
                )
                if existing_match:
                    st.success("✅ Match request sent")
                else:
                    msg_key = f"off_msg_{off['id']}"
                    btn_key = f"off_btn_{off['id']}"
                    # Custom message field
                    custom_message = st.text_area(
                        "Custom message (optional)",
                        key=msg_key,
                        placeholder="Add a personal note..."
                    )
                    if st.button("📩 Request Match", key=btn_key):
                        if crud.can_send_match_request(db, profile_id):
                            try:
                                match_req = crud.create_match_request(
                                    db,
                                    requester_id=profile_id,
                                    offer_id=off.id,
                                    request_id=None,
                                    message=custom_message
                                )
                                if match_req:
                                    st.success("✅ Match request sent successfully!")
                            except Exception as e:
                                st.error(f"❌ {str(e)}")
                        else:
                            st.error("⚠️ Daily limit reached")
    else:
        st.info("No offers available right now.")
