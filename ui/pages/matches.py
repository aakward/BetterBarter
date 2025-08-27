import streamlit as st
from data import crud, models
from data.db import get_db
from utils import auth 
from services import matching

def main():
    st.title("🤝 Matches")

    if not auth.is_authenticated():
        st.warning("You need to log in to see your matches.")
        st.stop()

    db = next(get_db())
    user_id = auth.get_current_user_id()

    # Fetch matches (from a matching service)
    matches = matching.find_matches_for_user(db, user_id=user_id)

    if not matches:
        st.info("No matches found at the moment. Check back later!")
        return

    st.subheader("Potential Matches")
    for m in matches:
        st.markdown(f"**Offer:** {m['offer_title']} (User: {m['offer_user_name']}, Postal Code: {m['offer_postal']})")
        st.markdown(f"**Request:** {m['request_title']} (User: {m['request_user_name']}, Postal Code: {m['request_postal']})")
        st.markdown(f"**Match Score:** {m['score']:.2f}")
        st.write("---")

if __name__ == "__main__":
    main()
