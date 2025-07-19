"""
Main entry point for Exporo SME Export Assistant
Handles routing between login/auth and chat pages
"""

import streamlit as st
from .config import APP_TITLE, APP_ICON, SHARED_CSS
from .auth import (
    init_db, init_auth_session_state, show_navigation, 
    show_login_page, show_signup_page, show_welcome_landing_page, get_user_count
)
from .chat import init_chat_session_state, show_full_chat_page

def main():
    """Main application entry point"""
    # Configure page
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Apply shared CSS
    st.markdown(SHARED_CSS, unsafe_allow_html=True)
    
    # Initialize database and session state
    init_db()
    init_auth_session_state()
    init_chat_session_state()
    
    # Show navigation
    show_navigation()
    
    # Route based on authentication status and page
    if not st.session_state.logged_in:
        # Show authentication pages
        if st.session_state.page == 'login':
            show_login_page()
        elif st.session_state.page == 'signup':
            show_signup_page()
    else:
        # Show pages for logged-in users
        if st.session_state.page == 'welcome':
            show_welcome_landing_page()
        elif st.session_state.page == 'chat':
            show_full_chat_page()
        else:
            # Default to welcome page for logged-in users
            st.session_state.page = 'welcome'
            show_welcome_landing_page()
    
    # Footer
    st.markdown("---")
    if st.session_state.logged_in:
        user_count = get_user_count()
        st.markdown(f"© 2024 Exporo - Platform UMKM untuk Ekspor Global | Total Users: {user_count}")
    else:
        st.markdown("© 2024 Exporo - Platform UMKM untuk Ekspor Global")

if __name__ == "__main__":
    main()