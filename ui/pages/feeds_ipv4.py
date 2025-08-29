import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from utils import auth

def main():
    st.title("📰 Feeds")

    if not auth.is_authenticated():
        st.warning("You need to log in to see the feed.")
        st.stop()

    db = get_db()  # Supabase client
    profile_id = auth.get_current_profile_id()

    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")

    # -------------------------
    # Requests Section
    # -------------------------
    st.header("📌 Requests")
    requests = crud.get_all_requests(db, exclude_profile_id=profile_id)
    if requests:
        for req in requests:
            # Fetch request owner profile
            req_profile = crud.get_profile(db, req["profile_id"])

            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown(
                    f"**{req['title']}** *(by {req_profile['full_name']}, {req_profile['postal_code']})*"
                )
                if req.get("description"):
                    st.caption(req["description"])

            with col2:
                existing_match = crud.get_existing_match_request(
                    db, profile_id, request_id=req["id"], offer_id=None
                )
                if existing_match:
                    st.success("✅ Match request sent")
                else:
                    custom_message = st.text_area(
                        "Custom message (optional)",
                        key=f"req_msg_{req['id']}",
                        placeholder="Add a personal note..."
                    )
                    if st.button("📩 Request Match", key=f"req_btn_{req['id']}"):
                        if crud.can_send_match_request(db, profile_id):
                            try:
                                match_req = crud.create_match_request(
                                    db,
                                    requester_id=profile_id,
                                    request_id=req["id"],
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
            # Fetch offer owner profile
            off_profile = crud.get_profile(db, off["profile_id"])

            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown(
                    f"**{off['title']}** *(by {off_profile['full_name']}, {off_profile['postal_code']})*"
                )
                if off.get("description"):
                    st.caption(off["description"])

            with col2:
                existing_match = crud.get_existing_match_request(
                    db, profile_id, offer_id=off["id"], request_id=None
                )
                if existing_match:
                    st.success("✅ Match request sent")
                else:
                    custom_message = st.text_area(
                        "Custom message (optional)",
                        key=f"off_msg_{off['id']}",
                        placeholder="Add a personal note..."
                    )
                    if st.button("📩 Request Match", key=f"off_btn_{off['id']}"):
                        if crud.can_send_match_request(db, profile_id):
                            try:
                                match_req = crud.create_match_request(
                                    db,
                                    requester_id=profile_id,
                                    offer_id=off["id"],
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


if __name__ == "__main__":
    main()
