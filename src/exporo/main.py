"""
Main entry point for Exporo SME Export Assistant
Handles routing between login/auth and chat pages
"""

import streamlit as st
from .config import APP_TITLE, APP_ICON, SHARED_CSS
from .auth import (
    init_db,
    init_auth_session_state,
    show_navigation,
    show_login_page,
    show_signup_page,
    show_welcome_landing_page,
    get_user_count,
)


def main():
    """Main application entry point"""
    # Configure page
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Apply shared CSS
    st.markdown(SHARED_CSS, unsafe_allow_html=True)

    # Initialize database and session state
    init_db()
    init_auth_session_state()

    # Lazy import and initialize chat module only when needed
    if st.session_state.get("logged_in", False):
        from .chat import init_chat_session_state

        init_chat_session_state()

    # Show navigation
    show_navigation()

    # Route based on authentication status and page
    if not st.session_state.logged_in:
        # Show authentication pages
        if st.session_state.page == "login":
            st.session_state.last_page = "login"
            show_login_page()
        elif st.session_state.page == "signup":
            st.session_state.last_page = "signup"
            show_signup_page()
    else:
        # Show pages for logged-in users
        if st.session_state.page == "welcome":
            st.session_state.last_page = "welcome"
            show_welcome_landing_page()
        elif st.session_state.page == "chat":
            from .chat import show_full_chat_page

            show_full_chat_page()
        elif st.session_state.page == "profil-bisnis":
            st.session_state.last_page = "profil-bisnis"
            from .auth import show_business_profile_page

            show_business_profile_page()
        elif st.session_state.page == "langkah-ekspor":
            st.session_state.last_page = "langkah-ekspor"
            from .auth import show_coming_soon_page

            show_coming_soon_page("langkah-ekspor")
        elif st.session_state.page == "dokumen":
            st.session_state.last_page = "dokumen"
            from .auth import show_coming_soon_page

            show_coming_soon_page("dokumen")
        elif st.session_state.page == "kualitas":
            st.session_state.last_page = "kualitas"
            from .auth import show_coming_soon_page

            show_coming_soon_page("kualitas")
        elif st.session_state.page == "pasar-global":
            st.session_state.last_page = "pasar-global"
            from .auth import show_coming_soon_page

            show_coming_soon_page("pasar-global")
        elif st.session_state.page == "dashboard":
            st.session_state.last_page = "dashboard"
            from .dashboard import show_dashboard_page

            show_dashboard_page()
        else:
            # Default to welcome page for logged-in users
            st.session_state.page = "welcome"
            st.session_state.last_page = "welcome"
            show_welcome_landing_page()

    # Footer
    st.markdown("---")
    if st.session_state.logged_in:
        user_count = get_user_count()
        st.markdown(
            f"© 2025 Exporo - Platform UMKM untuk Ekspor Global | Total Users: {user_count}"
        )
    else:
        st.markdown("© 2025 Exporo - Platform UMKM untuk Ekspor Global")


if __name__ == "__main__":
    main()
