import streamlit as st
from ui.pages import login, profile, offers, requests, matches, feeds
from streamlit_option_menu import option_menu
from supabase import create_client, Client


# -----------------------------
# App Navigation
# -----------------------------
PAGES = {
    "Login / Register": login,
    "Profile": profile,
    "My Offers": offers,
    "My Requests": requests,
    "Matches": matches,
    "Community Feed": feeds
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

    st.sidebar.markdown(f"**App Version:** 1.0.1")

    return selected

def main():
    st.set_page_config(page_title="Barter", layout="wide")
    selected=set_sidebar()
    page = PAGES[selected]

    # Render selected page
    page.main()

    supabase: Client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

    response = supabase.table("profiles").select("*").limit(1).execute()
        
    if response.data is not None:
        st.write("✅ Connection successful! Sample row:")
        st.write(response.data)
    else:
        st.write("⚠️ Connected, but no data returned from table 'profiles'.")


if __name__ == "__main__":
    main()
