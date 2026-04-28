"""Sidebar navigation component"""
import streamlit as st
from services.audit_service import log_audit

def render_sidebar(system_name):
    """Render sidebar navigation"""
    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role.replace('_', ' ').title()}")
    if st.session_state.branch_name:
        st.sidebar.write(f"**Branch:** {st.session_state.branch_name}")
    st.sidebar.divider()
    
    st.sidebar.subheader("Navigation")
    menu_items = ["Registration Form", "View Members", "Analytics Dashboard", "Export Data"]
    
    if st.session_state.user_role in ['super_admin', 'admin']:
        menu_items.extend(["Import Data", "Branch Management"])
    
    if st.session_state.user_role == 'super_admin':
        menu_items.extend(["User Management", "Email Settings", "Theme Customizer", "Audit Log"])
    
    selected_page = st.sidebar.radio("Go to", menu_items)
    
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        if st.session_state.user_id:
            log_audit(st.session_state.user_id, st.session_state.username, 'LOGOUT', 'user', 
                     st.session_state.user_id, "User logged out")
        for key in ['logged_in', 'user_id', 'username', 'user_role', 'user_branch_id', 'branch_name']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    return selected_page