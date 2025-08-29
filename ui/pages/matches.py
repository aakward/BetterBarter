import streamlit as st
from data import crud
from data.db import get_db
from utils import auth
from services import matching

def main():
    st.title("🤝 Matches")

    if not auth.is_authenticated():
        st.warning("You need to log in to see your matches.")
        st.stop()

    db = next(get_db())
    profile_id = auth.get_current_profile_id()

    # Show current karma
    profile = crud.get_profile(db, profile_id)
    if profile:
        st.info(f"🌟 Your Karma: **{profile.karma}**")

    st.header("🔎 Potential Matches")
    matches = matching.find_matches_for_user(db, profile_id=profile_id)

    if matches:
        for idx, m in enumerate(matches):
            with st.expander(f"Match {idx+1}: {m['offer_title']} ↔ {m['request_title']}"):
                st.markdown(f"**Offer:** {m['offer_title']} (User: {m['offer_user_name']}, Postal Code: {m['offer_postal']})")
                st.markdown(f"**Request:** {m['request_title']} (User: {m['request_user_name']}, Postal Code: {m['request_postal']})")
                st.markdown(f"**Match Score:** {m['score']:.2f}")

                # Optional message input
                custom_message = st.text_area(f"Custom message for offer owner (optional)", key=f"msg_{idx}")

                if st.button("📩 Send Match Request", key=f"send_{idx}"):
                    if crud.can_send_match_request(db, profile_id):
                        try:
                            crud.create_match_request(
                                db,
                                requester_id=profile_id,
                                offer_id=m["offer_id"],
                                request_id=m["request_id"],
                                message=custom_message
                            )
                            st.success("✅ Match request sent successfully!")
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
                    else:
                        st.error("⚠️ Daily match request limit reached.")
    else:
        st.info("No matches found right now. Check back later!")

    st.header("📤 Your Sent Match Requests")
    sent_requests = crud.get_match_requests_by_requester(db, profile_id)
    if sent_requests:
        for r in sent_requests:
            offer_title = r.offer.title if r.offer else "—"
            request_title = r.request.title if r.request else "—"
            st.markdown(f"- Offer: **{offer_title}** → Request: **{request_title}** | Status: **{r.status.value}**")
            if r.message:
                st.caption(f"Message: {r.message}")
    else:
        st.info("You haven’t sent any match requests yet.")

    st.header("📥 Incoming Match Requests")
    # Incoming requests for offers posted by the user
    user_offers = crud.get_offers(db)
    incoming_requests = []
    for offer in user_offers:
        if offer.profile_id == profile_id:
            incoming_requests.extend(crud.get_match_requests_for_offer(db, offer.id))

    if incoming_requests:
        for r in incoming_requests:
            with st.expander(f"From {r.requester.full_name} for your offer '{r.offer.title}'"):
                st.markdown(f"**Request:** {r.request.title} (Postal: {r.request.profile.postal_code})")
                if r.message:
                    st.caption(f"Message: {r.message}")

                col1, col2 = st.columns(2)
                if col1.button("✅ Approve", key=f"approve_{r.id}"):
                    crud.update_match_request_status(db, r.id, "approved")
                    st.success("Match approved! Both parties gained karma.")
                if col2.button("❌ Reject", key=f"reject_{r.id}"):
                    crud.update_match_request_status(db, r.id, "rejected")
                    st.warning("Match request rejected.")
    else:
        st.info("No incoming match requests yet.")


if __name__ == "__main__":
    main()
