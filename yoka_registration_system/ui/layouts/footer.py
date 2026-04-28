"""Footer component"""
import streamlit as st
from services.settings_service import get_system_settings

def render_footer():
    """Render footer in sidebar"""
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()} if not settings_df.empty else {}
    footer_text = settings.get('footer_text', '© 2024 Kumasi District YoKA. All Rights Reserved.')
    
    st.sidebar.divider()
    st.sidebar.caption(footer_text)