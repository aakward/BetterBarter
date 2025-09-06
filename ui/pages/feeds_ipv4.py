import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth

REQUEST_BUCKET_NAME = "request-images"
OFFER_BUCKET_NAME = "offer-images"


def create_signed_url(db, bucket: str, file_name: str, expires_sec: int = 60 * 60 * 24) -> str | None:
    """Return a signed URL for a stored file name, or None on failure."""
    if not file_name:
        return None
    try:
        resp = db.storage.from_(bucket).create_signed_url(file_name, expires_sec)
        return resp.get("signedURL") or resp.get("signedUrl")
    except Exception:
        return None


def display_feed_item(db, caller_id, item, item_type="request"):
    """
    Display a single request or offer inside an expander with card-like layout.
    item_type: "request" or "offer" (feed view)
    caller_id: the profile id of the current user
    """
    profile = crud.get_profile(db, item["profile_id"])
    icon = "🙏" if item_type == "request" else "🤗"
    expander_label = f"{icon} {item['title']}"

    with st.expander(expander_label, expanded=False):
        # ---- Top row: image + details ----
        col_img, col_info = st.columns([1, 3])
        with col_img:
            image_file_name = item.get("image_file_name")
            if image_file_name:
                bucket = REQUEST_BUCKET_NAME if item_type == "request" else OFFER_BUCKET_NAME
                url = create_signed_url(db, bucket, image_file_name)
                if url:
                    st.image(url, width=150)
        with col_info:
            st.markdown(f"### {item['title']}")
            st.markdown(
                f"<span style='color:gray; font-size:0.9em;'>by {profile['full_name']}, {profile['postal_code']}</span>",
                unsafe_allow_html=True
            )
            if item.get("description"):
                st.caption(item["description"])

        st.markdown("---")

        # ---- Bottom row: match request section ----
        existing_match = crud.get_existing_match_request(
            db,
            initiator_id=caller_id,
            request_id=item["id"] if item_type == "request" else None,
            offer_id=item["id"] if item_type == "offer" else None
        )

        if existing_match:
            st.success("✅ Match request sent")
        else:
            toggle_key = f"{item_type}_toggle_{item['id']}"
            if st.button("📩 Send Match Request", key=f"{item_type}_btn_{item['id']}"):
                st.session_state[toggle_key] = True

            if st.session_state.get(toggle_key, False):
                msg_key = f"{item_type}_msg_{item['id']}"
                contact_mode_key = f"{item_type}_contact_mode_{item['id']}"
                contact_value_key = f"{item_type}_contact_value_{item['id']}"

                custom_message = st.text_area(
                    "Custom message (optional)",
                    key=msg_key,
                    placeholder="Add a personal note..."
                )
                contact_mode = st.selectbox(
                    "Preferred contact mode",
                    options=["WhatsApp", "Phone", "Email"],
                    key=contact_mode_key
                )
                contact_value = st.text_input(
                    "Contact info",
                    key=contact_value_key,
                    placeholder="Enter your email or phone number"
                )

                if st.button("Submit Request", key=f"{item_type}_submit_{item['id']}"):
                    if not contact_mode or not contact_value:
                        st.error("Please provide both contact mode and contact info.")
                    else:
                        try:
                            # Correct initiator_type logic
                            initiator_type = "offer" if item_type == "request" else "request"

                            match_req = crud.create_match_request(
                                db,
                                caller_id=caller_id,
                                request_id=item["id"] if item_type == "request" else None,
                                offer_id=item["id"] if item_type == "offer" else None,
                                message=custom_message,
                                contact_mode=contact_mode,
                                contact_value=contact_value,
                                initiator_type=initiator_type
                            )
                            if match_req:
                                st.success("✅ Match request sent successfully!")
                                st.session_state[toggle_key] = False
                        except Exception as e:
                            st.error(f"❌ {str(e)}")



def main():
    st.title("📰 Feeds")

    db = get_db()
    user = auth.ensure_authenticated(db)
    profile_id = user.id

    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")

    # Tabs for separation
    tabs = st.tabs(["📌 Requests", "🎁 Offers"])

    # -------------------------
    # Requests Tab
    # -------------------------
    with tabs[0]:
        requests = crud.get_all_requests(db, exclude_profile_id=profile_id)
        if requests:
            for req in requests:
                display_feed_item(db, profile_id, req, item_type="request")
        else:
            st.info("No requests available right now.")

    # -------------------------
    # Offers Tab
    # -------------------------
    with tabs[1]:
        offers = crud.get_all_offers(db, exclude_profile_id=profile_id)
        if offers:
            for off in offers:
                display_feed_item(db, profile_id, off, item_type="offer")
        else:
            st.info("No offers available right now.")


if __name__ == "__main__":
    main()
