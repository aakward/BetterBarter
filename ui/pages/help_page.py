import streamlit as st

def main():
    st.set_page_config(page_title="BetterBarter", layout="wide", initial_sidebar_state="expanded")

    # Unified CSS
    st.markdown("""
    <style>
        body {
            background-color: #f9f9f9;
            color: #333333;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .title {
            text-align: center;
            color: #2C3E50;
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 0;
        }
        .subtitle {
            text-align: center;
            color: #555555;
            font-size: 24px;
            margin-top: 0;
        }
        .section-header {
            color: #2E86C1;
        }
        /* Info box */
        div.info-box {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        [data-theme="light"] div.info-box {
            background-color: #EAF2F8;
            color: #2C3E50;
        }
        [data-theme="dark"] div.info-box {
            background-color: #2C3E3E;  /* darker for dark mode */
            color: #F0F0F0;
        }
        .closing-note {
            text-align: center;
            font-size: 18px;
            color: #2C3E50;
            margin-top: 30px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Title and subtitle
    st.markdown("<div class='title'> BetterBarter </div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Share • Exchange • Lend • Request</div>", unsafe_allow_html=True)

    # Intro info box
    st.markdown("""
    <div class='info-box'>
    We’re glad you’re here! BetterBarter is a community space where people can 
    <b>share, exchange, lend, or request</b> things to help each other out.<br>
    Whether it’s giving away a spare item, asking for a hand, lending tools, or setting up 
    whatever arrangement works for both sides - it’s all about connecting and making life easier.<br>
    Here’s everything you need to know to get started.
    </div>
    """, unsafe_allow_html=True)

    # How it Works
    st.markdown("<h2 class='section-header'>How it Works</h2>", unsafe_allow_html=True)
    st.markdown("""
    1. 🎁 **Post an offer** – something you’d like to give, lend, or share.  
    2. 🙋 **Post a request** – something you need.  
    3. 👀 **Browse the feed** – see offers and requests from others.  
    4. 🔗 **Send a match request** – or accept matches sent by community members.  
    5. 🤝 **Agree on the arrangement** – it could be a gift, a swap, a loan, or involve payment if agreed.  
    """)

    st.divider()

    # FAQ
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **1. What can I post as an offer or request?**  
        Items, services, skills, or your time.  

        **2. Do I need both an offer *and* a request?**  
        No, you can post only offers, only requests, or both.  

        **3. Who can see my contact details?**  
        Only shared after a confirmed match.  

        **4. How do matches work?**  
        - System suggests matches.  
        - You can send match requests.  
        - Contact details are exchanged once accepted.  

        **5. What is the karma system?**  
        Karma points are awarded for positive community interactions — giving, helping, completing exchanges.
        """)

    # Community Guidelines
    with st.expander("🌱 Community Guidelines"):
        st.markdown("""
        1. **Be honest and clear** – describe your offers/requests accurately.  
        2. **Respect others** – it’s fine to say no.  
        3. **Keep it safe & legal** – no dangerous or prohibited items.  
        4. **Protect privacy** – contact info shared only after match.  
        5. **Be reliable** – follow through or communicate if plans change.  
        6. **Support generosity** – giving and lending are encouraged!  
        7. **Report issues** – help keep BetterBarter safe and fair.  
        8. **Earn karma points** – positive participation builds trust.
        """)

    # Closing note
    st.markdown("<div class='closing-note'>💙 Thanks for being part of the community! Together, we make exchanges easier, fairer, and friendlier.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
