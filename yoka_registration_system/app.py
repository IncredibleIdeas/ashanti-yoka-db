"""Main entry point for YoKA Registration System"""
import streamlit as st
from datetime import datetime

# Page configuration MUST be the first Streamlit command
st.set_page_config(page_title="Kumasi District YoKA Registration System", page_icon="⛪", layout="wide")

# Import modules
from database.connection import init_database
from ui.styling import apply_custom_styling
from ui.pages.login import login_page
from ui.layouts.sidebar import render_sidebar
from ui.layouts.footer import render_footer
from services.settings_service import get_system_settings

def main():
    # Initialize database
    init_database()
    
    # Apply custom styling
    apply_custom_styling()
    
    # Get system settings
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()} if not settings_df.empty else {}
    system_name = settings.get('system_name', 'Kumasi District YoKA Registration System')
    
    # Session state initialization
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_branch_id' not in st.session_state:
        st.session_state.user_branch_id = None
    if 'branch_name' not in st.session_state:
        st.session_state.branch_name = None
    
    # Login Page
    if not st.session_state.logged_in:
        login_page(system_name)
    else:
        # Render sidebar and get selected page
        selected_page = render_sidebar(system_name)
        
        # Page routing
        if selected_page == "Registration Form":
            from ui.pages.registration import registration_form_ui
            registration_form_ui()
        elif selected_page == "View Members":
            from ui.pages.view_members import view_members_ui
            view_members_ui()
        elif selected_page == "Analytics Dashboard":
            from ui.pages.analytics import analytics_dashboard_ui
            analytics_dashboard_ui()
        elif selected_page == "Export Data":
            from ui.pages.export import advanced_export_ui
            advanced_export_ui()
        elif selected_page == "Import Data":
            from ui.pages.import_page import import_data_ui
            import_data_ui()
        elif selected_page == "Branch Management":
            from ui.pages.branch_management import branch_management_ui
            branch_management_ui()
        elif selected_page == "User Management":
            from ui.pages.user_management import user_management_ui
            user_management_ui()
        elif selected_page == "Email Settings":
            from ui.pages.email_settings import email_settings_ui
            email_settings_ui()
        elif selected_page == "Theme Customizer":
            from ui.pages.theme_customizer import theme_customizer_ui
            theme_customizer_ui()
        elif selected_page == "Audit Log":
            from ui.pages.audit_log import audit_log_ui
            audit_log_ui()
        
        # Render footer
        render_footer()

if __name__ == "__main__":
    main()