import streamlit as st
from ui.pages import login_ipv4, profile_ipv4, offers_ipv4, requests_ipv4, matches_ipv4, feeds_ipv4
from streamlit_option_menu import option_menu



# -----------------------------
# App Navigation
# -----------------------------
PAGES = {
    "Login / Register": login_ipv4,
    "Profile": profile_ipv4,
    "My Offers": offers_ipv4,
    "My Requests": requests_ipv4,
    "Matches": matches_ipv4,
    "Community Feed": feeds_ipv4
}

def set_sidebar():
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=list(PAGES.keys()),
            icons=["box-arrow-in-right", "person-circle", "magic", "subtract","emoji-laughing-fill", "person-hearts"],
            menu_icon="menu-button-wide",
            default_index=0
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='text-align: center; font-size: 16px;'>
            Created with <span style='color:red;'>❤️</span> by <b>Aakash Banik</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")

    st.sidebar.markdown(f"**App Version:** 1.0.2")

    return selected

def main():
    st.set_page_config(page_title="Barter", layout="wide")
    selected=set_sidebar()
    page = PAGES[selected]

    # Render selected page
    page.main()


if __name__ == "__main__":
    main()
