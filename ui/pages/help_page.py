import streamlit as st

def main():
    st.title("Welcome to betterBarter!")

    st.markdown("""
    Welcome to **betterBarter**!  
    We’re building a community where people help each other by **sharing, exchanging, lending, or gifting**.  
    Here’s everything you need to know to get started.
    """)

    # How it Works
    st.header("👋 How it Works")
    st.markdown("""
    1. **Post an offer** – something you’d like to give, lend, or share.  
    2. **Post a request** – something you need.  
    3. **Browse the feed** – see offers and requests from others.  
    4. **Send a match request** – or accept matches sent out by other community members.  
    5. **Agree on the exchange** – it can be a gift, a swap, a loan, or even involve payment if both sides agree.  
    """)

    st. write("---")
    # FAQ inside expander
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **1. What can I post as an offer or request?**  
        Items, services, skills, or even your time. You can also lend or borrow things.  

        **2. Do I need both an offer *and* a request?**  
        No. You can post only offers, only requests, or both. You can also browse and respond directly to others without posting anything yourself.  

        **3. Can I ask for money?**  
        Yes, but it’s optional. You can mention a payment or lending arrangement in your post description, but it’s not the core of the platform.  

        **4. Who can see my contact details?**  
        Your contact info is **only shared when both sides confirm a match**.  

        **5. How do matches work?**  
        - The system suggests matches between offers and requests.  
        - You can also send a match request directly from the feed.  
        - If the other person accepts, contact details are exchanged.  

        **6. Can I edit or delete my posts?**  
        Yes, at any time. Deleted posts disappear immediately.  

        **7. What if I don’t find a match?**  
        New posts are added all the time. Keep your posts active, update them, or browse the feed again later.  

        **8. Is this like a marketplace?**  
        Not exactly. betterBarter is about **community support first**. Payment is allowed, but not required.  

        **9. How do I know I can trust other users?**  
        We encourage clear descriptions, fair exchanges, and respectful communication. If something seems off, report it.  

        **10. What is the karma system?**  
        Karma points are awarded for positive community interactions — giving, helping, or completing exchanges. Karma helps others see you as a trusted member.  

        **11. Can I just browse without posting?**  
        Absolutely. You can explore offers and requests in the feed and even initiate a match without posting your own.  

        **12. Who do I contact for help?**  
        Reach us at betterbartercontact@gmail.com  
        *(Yes, I know it’s a Gmail — still bootstrapping, not a corporate HQ… but we read every email! 📨)*  
        """)

    # Community Guidelines inside expander
    with st.expander("🌱 Community Guidelines"):
        st.markdown("""
        1. **Be honest and clear** – describe your offers/requests accurately.  
        2. **Respect others’ choices** – it’s fine to say no.  
        3. **Keep it safe & legal** – no dangerous or prohibited items.  
        4. **Protect privacy** – contact info is shared only after a confirmed match.  
        5. **Be reliable** – follow through or communicate if plans change.  
        6. **Support generosity** – giving and lending are encouraged!  
        7. **Report issues** – help keep betterBarter safe and fair.  
        8. **Earn karma points** – positive participation builds trust and reputation within the community.  
        """)

    # Closing note
    st.markdown("""
    ---
    Thanks for being part of the community 💙  
    Together, we make exchanges easier, fairer, and friendlier.
    """)

# If running this page standalone
if __name__ == "__main__":
    main()
