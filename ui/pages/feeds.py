import streamlit as st
from data import crud
from data.db import get_db

def main():
    st.title("📢 Community Feed")
    st.write("Browse anonymized community requests and offers.")

    # Database session
    db = next(get_db())

    # Fetch requests and offers (most recent first)
    requests = sorted(crud.get_requests(db), key=lambda x: x.created_at, reverse=True)
    offers = sorted(crud.get_offers(db), key=lambda x: x.created_at, reverse=True)

    # Tabs for navigation
    tab1, tab2 = st.tabs(["🆘 Requests", "🎁 Offers"])

    with tab1:
        st.subheader("Community Requests")
        if not requests:
            st.info("No requests yet.")
        else:
            for r in requests:
                st.markdown(
                    f"**{r.title}**\n\n{r.description or 'No description'}\n\n📍 Location: {r.profile.postal_code or 'N/A'}"
                )
                st.divider()

    with tab2:
        st.subheader("Community Offers")
        if not offers:
            st.info("No offers yet.")
        else:
            for o in offers:
                st.markdown(
                    f"**{o.title}**\n\n{o.description or 'No description'}\n\n📍 Location: {o.profile.postal_code or 'N/A'}"
                )
                st.divider()

if __name__ == "__main__":
    main()
