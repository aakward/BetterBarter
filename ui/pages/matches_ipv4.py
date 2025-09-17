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
        "💡 Potential Matches",
        "📤 Sent Requests",
        "📥 Received Requests",
        "🎯 Completed Matches"
    ])

    # -------------------------
    # Tab 1: Potential Matches
    # -------------------------
    with tabs[0]:
        potential_matches = crud.get_potential_matches(db, profile_id)

        matches_for_my_requests = [
            build_ui_match_from_offer_request_pair(o, r, score=score)
            for (o, r, score) in potential_matches
            if r["profile_id"] == profile_id
        ]

        matches_for_my_offers = [
            build_ui_match_from_offer_request_pair(o, r, score=score)
            for (o, r, score) in potential_matches
            if o["profile_id"] == profile_id
        ]

        st.subheader(f"✨ Potential Matches for Your Requests ({len(matches_for_my_requests)})")
        if matches_for_my_requests:
            for idx, match in enumerate(matches_for_my_requests):
                display_match(db, match, section="potential", profile_id=profile_id, idx=idx)
        else:
            st.info("No offers found for your requests right now!")

        st.subheader(f"🎁 Potential Matches for Your Offers ({len(matches_for_my_offers)})")
        if matches_for_my_offers:
            for idx, match in enumerate(matches_for_my_offers):
                display_match(db, match, section="potential", profile_id=profile_id, idx=idx + 1000)
        else:
            st.info("No requests found matching your offers right now!")

    # -------------------------
    # Tab 2: Sent Requests
    # -------------------------
    with tabs[1]:
        sent_requests = crud.get_sent_match_requests(db, profile_id, status="pending")
        ui_sent_requests = [build_ui_match_from_match_request(mr, db) for mr in sent_requests]

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
        incoming_requests = crud.get_incoming_match_requests(db, profile_id, status="pending")
        ui_incoming_requests = [build_ui_match_from_match_request(mr, db) for mr in incoming_requests]

        st.subheader(f"Received Requests ({len(ui_incoming_requests)})")
        if ui_incoming_requests:
            for idx, match in enumerate(ui_incoming_requests):
                display_match(db, match, section="received", profile_id=profile_id, idx=idx)
        else:
            st.info("No incoming match requests for review.")

    # -------------------------
    # Tab 4: Completed Matches
    # -------------------------
    with tabs[3]:
        all_matches = db.table("match_requests").select("""
            *,
            offers:offer_id (
                id, title, description, image_file_name, category, subcategory,
                profiles:profile_id (id, full_name, postal_code, karma)
            ),
            requests:request_id (
                id, title, description, image_file_name, category, subcategory,
                profiles:profile_id (id, full_name, postal_code, karma)
            )
        """).or_(
            f"requester_id.eq.{profile_id},offerer_id.eq.{profile_id}"
        ).execute().data

        matched_requests = [m for m in all_matches if m.get("status") in ("accepted", "completed")]
        rejected_requests = [m for m in all_matches if m.get("status") == "rejected"]

        st.subheader(f"🙌 Successful Matches ({len(matched_requests)})")
        if matched_requests:
            for idx, match_req in enumerate(matched_requests):
                ui_match = build_ui_match_from_match_request(match_req, db) if isinstance(match_req, dict) else match_req
                display_match(db, ui_match, section="matched", profile_id=profile_id, idx=idx)
        else:
            st.info("No matched requests yet!")

        st.write("---")
        st.subheader(f"❌ Declined Requests ({len(rejected_requests)})")
        for idx, match_req in enumerate(rejected_requests):
            ui_match = build_ui_match_from_match_request(match_req, db) if isinstance(match_req, dict) else match_req
            display_match(db, ui_match, section="matched", profile_id=profile_id, idx=idx + 10000)


# -------------------------
# Redesigned display_match
# -------------------------
def display_match(db: Client, match: UIMatch, section: str, profile_id: str, idx: int = 0):
    """
    Display a single match with richer info (karma, postal, category, subcategory, image).
    Sections: potential, sent, received, matched
    """
    header_text = f"Match #{match.id}" if match.id else f"Potential Match #{idx+1}"

    with st.expander(header_text, expanded=(section == "potential")):
        col_offer, col_request = st.columns(2)

        # ---- Offer side ----
        with col_offer:
            st.markdown("### 🤗 Offer")
            if match.offer_image:
                signed_url = db.storage.from_(OFFER_BUCKET_NAME).create_signed_url(match.offer_image, 60*60*24)
                st.image(signed_url.get("signedURL"), width=160)

            st.markdown(f"**{match.offer_title or 'No Title'}**")
            st.caption(match.offer_description or "No Description")
            st.markdown(f" 👤 {match.offer_user_name or '-'} (Karma: {match.offer_user_karma or 0})")
            st.markdown(f" 📍 {match.offer_postal or '—'}")
            st.markdown(f" 📂 {match.offer_category or '—'} → {match.offer_subcategory or '—'}")

        # ---- Request side ----
        with col_request:
            st.markdown("### 🙏 Request")
            if match.request_image:
                signed_url = db.storage.from_(REQUEST_BUCKET_NAME).create_signed_url(match.request_image, 60*60*24)
                st.image(signed_url.get("signedURL"), width=160)

            st.markdown(f"**{match.request_title or 'No Title'}**")
            st.caption(match.request_description or "No Description")
            st.markdown(f" 👤 {match.request_user_name or '-'} (Karma: {match.request_user_karma or 0})")
            st.markdown(f" 📍 {match.request_postal or '—'}")
            st.markdown(f" 📂 {match.request_category or '—'} → {match.request_subcategory or '—'}")

        st.markdown("---")
        st.write(f"**Status:** {match.status.capitalize() if match.status else '—'}")
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
                contact_mode = st.selectbox(
                    "Preferred contact method",
                    options=["WhatsApp", "Phone", "Email"],
                    key=f"contact-mode-{idx}"
                )
                contact_value = st.text_input(
                    "Your contact details",
                    key=f"contact-value-{idx}"
                )

                if st.button("Submit Request", key=f"submit-{idx}"):
                    if not contact_value:
                        st.error("Please provide your contact details.")
                    else:
                        initiator_type = "request" if profile_id == match.requester_id else "offer"
                        crud.create_match_request(
                            db,
                            caller_id=profile_id,
                            offer_id=match.offer_id,
                            request_id=match.request_id,
                            message=custom_message,
                            contact_mode=contact_mode,
                            contact_value=contact_value,
                            initiator_type=initiator_type
                        )
                        st.success("✅ Match request sent successfully!")
                        st.session_state[toggle_key] = False

        elif section == "sent":
            # Determine the other party
            if profile_id == match.requester_id:
                # I sent the request, so "To" is the offerer
                other_name = match.offer_user_name
                other_postal = match.offer_postal
            elif profile_id == match.offerer_id:
                # I sent the request, so "To" is the requester
                other_name = match.request_user_name
                other_postal = match.request_postal
            else:
                other_name = "-"
                other_postal = "-"
            st.write(f"**To:** {other_name or '-'} ({other_postal or '-'})")
            if match.status.lower() == "pending" and st.button("Cancel Match Request", key=f"cancel-{idx}"):
                crud.cancel_match_request(db, match.id, profile_id)
                st.success("Match request cancelled!")

        elif section == "received":
            is_offerer = profile_id == match.offerer_id
            is_requester = profile_id == match.requester_id

            sender_name = match.request_user_name if is_offerer else match.offer_user_name
            sender_postal = match.request_postal if is_offerer else match.offer_postal

            st.write(f"**From:** {sender_name or '-'} ({sender_postal or '-'})")

            col1, col2 = st.columns(2)
            accept_key = f"accept_clicked_{idx}"  # track if user clicked Accept

            with col1:
                if not st.session_state.get(accept_key, False):
                    if st.button("Accept", key=f"accept-{idx}"):
                        st.session_state[accept_key] = True
                else:
                    contact_mode_key = f"accept-contact-mode-{idx}"
                    contact_value_key = f"accept-contact-value-{idx}"

                    existing_contact_mode = match.requester_contact_mode if is_requester else match.offerer_contact_mode
                    existing_contact_value = match.requester_contact_value if is_requester else match.offerer_contact_value

                    contact_mode = st.selectbox(
                        "Preferred contact method for this match",
                        options=["WhatsApp", "Phone", "Email"],
                        key=contact_mode_key,
                        index=["WhatsApp", "Phone", "Email"].index(existing_contact_mode)
                            if existing_contact_mode in ["WhatsApp", "Phone", "Email"] else 0
                    )
                    contact_value = st.text_input(
                        "Provide contact details to share",
                        key=contact_value_key,
                        value=existing_contact_value or ""
                    )

                    if st.button("Confirm Accept", key=f"confirm-accept-{idx}"):
                        if not contact_value:
                            st.error("Please provide contact details to accept the match.")
                        else:
                            crud.accept_match_request(
                                db,
                                match_request_id=match.id,
                                profile_id=profile_id,
                                contact_mode=contact_mode,
                                contact_value=contact_value
                            )
                            st.success("Request accepted!")
                            st.session_state[accept_key] = False

            with col2:
                if st.button("Decline", key=f"decline-{idx}"):
                    crud.decline_match_request(db, match.id, profile_id)
                    st.warning("Request declined!")

        elif section == "matched":
            if match.status == "rejected":
                st.warning("❌ Match Request Declined")
                st.caption("This match request was declined. No further action is possible.")
            else:
                st.success("✅ Matched / Completed")
                if profile_id == match.requester_id:
                    other_name = match.offer_user_name
                    other_contact_mode = match.offerer_contact_mode
                    other_contact_value = match.offerer_contact_value
                elif profile_id == match.offerer_id:
                    other_name = match.request_user_name
                    other_contact_mode = match.requester_contact_mode
                    other_contact_value = match.requester_contact_value
                else:
                    other_name = "-"
                    other_contact_mode = "-"
                    other_contact_value = "-"

                st.markdown(f"📞 **Contact {other_name or '-'}**: {other_contact_value or '-'} ({other_contact_mode or '-'})")


if __name__ == "__main__":
    main()
