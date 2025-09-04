import streamlit as st
from data import crud_ipv4 as crud
from data.db_ipv4 import get_db
from data.ui_models import UIMatch
from utils import auth
from datetime import datetime
from services.mappers import (
    build_ui_match_from_match,
    build_ui_match_from_match_request,
    build_ui_match_from_offer_request_pair
)
from supabase import Client

# Storage buckets
OFFER_BUCKET_NAME = "offer-images"
REQUEST_BUCKET_NAME = "request-images"

def main():
    st.set_page_config(page_title="Matches", layout="wide")
    st.title("🤝 Matches Dashboard")

    # -------------------------
    # Authentication
    # -------------------------
    db = get_db()
    user = auth.ensure_authenticated(db)
    profile_id = user.id

    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile['karma']}**")

    # -------------------------
    # Tabs for sections
    # -------------------------
    tabs = st.tabs([
        f"💡 Potential Matches",
        f"📤 Sent Requests",
        f"📥 Incoming Requests",
        f"🎯 Completed Matches"
    ])

    # -------------------------
    # Tab 1: Potential Matches
    # -------------------------
    with tabs[0]:
        potential_matches = crud.get_potential_matches(db, profile_id)
        matches_for_my_requests = [
            build_ui_match_from_offer_request_pair(o, r)
            for (o, r) in potential_matches
            if r["profile_id"] == profile_id
        ]
        matches_for_my_offers = [
            build_ui_match_from_offer_request_pair(o, r)
            for (o, r) in potential_matches
            if o["profile_id"] == profile_id
        ]

        st.subheader(f"✨ Matches for Your Requests ({len(matches_for_my_requests)})")
        if matches_for_my_requests:
            for idx, match in enumerate(matches_for_my_requests):
                display_match(db, match, section="potential", profile_id=profile_id, idx=idx)
        else:
            st.info("No offers found for your requests right now!")

        st.subheader(f"🎁 Matches for Your Offers ({len(matches_for_my_offers)})")
        if matches_for_my_offers:
            for idx, match in enumerate(matches_for_my_offers):
                display_match(db, match, section="potential", profile_id=profile_id, idx=idx + 1000)
        else:
            st.info("No requests found matching your offers right now!")

    # -------------------------
    # Tab 2: Sent Requests
    # -------------------------
    with tabs[1]:
        sent_requests = crud.get_match_requests_by_requester(db, profile_id)
        ui_sent_requests = [build_ui_match_from_match_request(mr) for mr in sent_requests]
        st.subheader(f"Sent Requests ({len(ui_sent_requests)})")
        if ui_sent_requests:
            for idx, match in enumerate(ui_sent_requests):
                display_match(db, match, section="sent", profile_id=profile_id, idx=idx)
        else:
            st.info("No match requests have been sent yet.")

    # -------------------------
    # Tab 3: Incoming Requests
    # -------------------------
    with tabs[2]:
        incoming_requests = crud.get_match_requests_for_offerer(db, profile_id, status="pending")
        ui_incoming_requests = [build_ui_match_from_match_request(mr) for mr in incoming_requests]
        st.subheader(f"Incoming Requests ({len(ui_incoming_requests)})")
        if ui_incoming_requests:
            for idx, match in enumerate(ui_incoming_requests):
                display_match(db, match, section="received", profile_id=profile_id, idx=idx)
        else:
            st.info("No incoming match requests for review.")

    # -------------------------
    # Tab 4: Completed Matches
    # -------------------------
    with tabs[3]:
        all_matches = db.table("match_requests").select("*").or_(
            f"requester_id.eq.{profile_id},offerer_id.eq.{profile_id}"
        ).execute().data
        matched_requests = [m for m in all_matches if m.get("status") in ("accepted", "completed")]
        st.subheader(f"Completed Matches ({len(matched_requests)})")
        if matched_requests:
            for idx, match in enumerate(matched_requests):
                ui_match = build_ui_match_from_match_request(match) if isinstance(match, dict) else match
                display_match(db, ui_match, section="matched", profile_id=profile_id, idx=idx)
        else:
            st.info("No matched requests yet!")




# -------------------------
# Redesigned display_match
# -------------------------
def display_match(db: Client, match: UIMatch, section: str, profile_id: str, idx: int = 0):
    """
    Display a single match in Streamlit with section-specific actions.
    Sections: potential, sent, received, matched
    """
    header_text = f"Match #{match.id}" if match.id else f"Potential Match #{idx+1}"

    # Use expander for collapsible display
    with st.expander(header_text, expanded=(section == "potential")):
        # Two-column layout: Offer | Request
        col_offer, col_request = st.columns(2)

        with col_offer:
            st.markdown("### Offer")
            if match.offer_title:
                st.write(match.offer_title)
            if match.offer_description:
                st.caption(match.offer_description)
            if match.offer_image:
                signed_url = db.storage.from_(OFFER_BUCKET_NAME).create_signed_url(
                    match.offer_image, 60*60*24
                )
                st.image(signed_url.get("signedURL"), width=150)
            if match.offer_user_name or match.offer_postal:
                st.write(f"Owner: **{match.offer_user_name or '-'}** ({match.offer_postal or '-'})")

        with col_request:
            st.markdown("### Request")
            if match.request_title:
                st.write(match.request_title)
            if match.request_description:
                st.caption(match.request_description)
            if match.request_image:
                signed_url = db.storage.from_(REQUEST_BUCKET_NAME).create_signed_url(
                    match.request_image, 60*60*24
                )
                st.image(signed_url.get("signedURL"), width=150)
            if match.request_user_name or match.request_postal:
                st.write(f"Owner: **{match.request_user_name or '-'}** ({match.request_postal or '-'})")

        st.markdown("---")
        st.write(f"**Status:** {match.status}")
        if match.created_at:
            st.caption(f"Created at: {match.created_at.strftime('%Y-%m-%d %H:%M')}")
        if match.message:
            st.info(f"💬 Message: {match.message}")

        # -------------------------
        # Section-specific actions
        # -------------------------
        if section == "potential":
            toggle_key = f"show_msg_box_{idx}"
            if st.button("Send Match Request", key=f"send-potential-{idx}"):
                st.session_state[toggle_key] = True
            if st.session_state.get(toggle_key, False):
                custom_message = st.text_area("Custom message (optional)", key=f"msg-potential-{idx}")
                if st.button("Submit Request", key=f"submit-{idx}"):
                    crud.create_match_request(db, profile_id, match.offer_id, match.request_id, custom_message)
                    st.success("Request sent!")
                    st.session_state[toggle_key] = False

        elif section == "sent":
            st.write(f"**To:** {match.offer_user_name or '-'} ({match.offer_postal or '-'})")
            if match.status.lower() == "pending" and st.button("Cancel Match Request", key=f"cancel-{idx}"):
                crud.cancel_match_request(db, match.id, profile_id)
                st.success("Match request cancelled!")

        elif section == "received":
            st.write(f"**From:** {match.request_user_name or '-'} ({match.request_postal or '-'})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Accept", key=f"accept-{idx}"):
                    crud.accept_match_request(db, match.id, profile_id)
                    st.success("Request accepted!")
            with col2:
                if st.button("Decline", key=f"decline-{idx}"):
                    crud.decline_match_request(db, match.id, profile_id)
                    st.warning("Request declined!")

        elif section == "matched":
            st.success("✅ Matched / Completed")
            st.write(f"Participants: {match.offer_user_name or '-'} ↔ {match.request_user_name or '-'}")

if __name__ == "__main__":
    main()
