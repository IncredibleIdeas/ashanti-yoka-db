"""Email settings UI"""
import streamlit as st
from services.email_service import get_email_settings, save_email_settings, send_email

def email_settings_ui():
    """Configure email settings (super admin only)"""
    if st.session_state.user_role != 'super_admin':
        st.error("Only Super Admin can configure email settings")
        return
    
    st.header("📧 Email Configuration")
    
    current_settings = get_email_settings()
    
    with st.form("email_config_form"):
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("SMTP Server", 
                                       value=current_settings['smtp_server'] if current_settings else "smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", 
                                       value=current_settings['smtp_port'] if current_settings else 587)
            sender_email = st.text_input("Sender Email",
                                        value=current_settings['sender_email'] if current_settings else "")
        
        with col2:
            sender_password = st.text_input("Sender Password", type="password",
                                           value=current_settings['sender_password'] if current_settings else "")
            use_tls = st.checkbox("Use TLS", value=current_settings['use_tls'] if current_settings else True)
        
        st.info("""
        **Email Configuration Tips:**
        - For Gmail: Use smtp.gmail.com, port 587, enable "Less secure app access" or use App Password
        - For Office 365: Use smtp.office365.com, port 587
        """)
        
        submitted = st.form_submit_button("Save Configuration", use_container_width=True)
        test_email_input = st.text_input("Test Email Address", key="test_email_field")
        test_submitted = st.form_submit_button("Send Test Email", use_container_width=True)
        
        if submitted:
            if sender_email and sender_password:
                save_email_settings(smtp_server, smtp_port, sender_email, sender_password, use_tls, 
                                  st.session_state.user_id)
                st.success("Email settings saved successfully!")
        
        if test_submitted and test_email_input:
            success, message = send_email(test_email_input, "YoKA System - Test Email",
                                         "<h3>Test Email</h3><p>Your email configuration is working correctly!</p>")
            if success:
                st.success("Test email sent successfully!")
            else:
                st.error(f"Failed to send test email: {message}")