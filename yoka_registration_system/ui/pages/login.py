"""Login page UI"""
import streamlit as st
from auth.authentication import check_login
from services.audit_service import log_audit

def login_page(system_name):
    """Render login page"""
    st.title(f"⛪ {system_name}")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome")
        st.markdown("Please login to access the system")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                user_info = check_login(username, password)
                if user_info:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_info['id']
                    st.session_state.username = user_info['username']
                    st.session_state.user_role = user_info['role']
                    st.session_state.user_branch_id = user_info.get('assigned_branch_id')
                    st.session_state.branch_name = user_info.get('branch_name')
                    
                    st.success(f"Welcome {user_info['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.info("Contact system administrator for credentials")