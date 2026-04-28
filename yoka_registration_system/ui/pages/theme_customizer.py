"""Theme customizer UI"""
import streamlit as st
from services.settings_service import get_system_settings, update_system_setting

def theme_customizer_ui():
    """Advanced theme customization with live preview"""
    if st.session_state.user_role != 'super_admin':
        st.error("Only Super Admin can customize themes")
        return
    
    st.title("🎨 Theme Customizer")
    
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()} if not settings_df.empty else {}
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎨 Color Scheme")
        primary_color = st.color_picker("Primary Color", settings.get('primary_color', '#1E3A8A'))
        secondary_color = st.color_picker("Secondary Color", settings.get('secondary_color', '#3B82F6'))
        accent_color = st.color_picker("Accent Color", settings.get('accent_color', '#F59E0B'))
        background_color = st.color_picker("Background Color", settings.get('background_color', '#FFFFFF'))
        sidebar_color = st.color_picker("Sidebar Color", settings.get('sidebar_color', '#1E3A8A'))
        
        st.subheader("📝 Typography")
        font_options = ["System Default", "Poppins", "Roboto", "Arial", "Helvetica"]
        current_font = settings.get('font_family', 'System Default')
        font_index = font_options.index(current_font) if current_font in font_options else 0
        font_family = st.selectbox("Font Family", font_options, index=font_index)
        
        font_size = st.select_slider("Base Font Size", 
                                     options=["12px", "14px", "16px", "18px", "20px"],
                                     value=settings.get('font_size', '16px'))
        
        st.subheader("📐 Layout")
        try:
            current_radius = int(settings.get('card_border_radius', '10'))
        except:
            current_radius = 10
        card_border_radius = st.slider("Card Border Radius", 0, 20, current_radius)
        
        st.subheader("🏷️ Branding")
        system_name = st.text_input("System Name", settings.get('system_name', 'Kumasi District YoKA Registration System'))
        favicon = st.text_input("Favicon Emoji", settings.get('favicon', '⛪'))
        footer_text = st.text_input("Footer Text", settings.get('footer_text', '© 2024 Kumasi District YoKA. All Rights Reserved.'))
        
        if st.button("💾 Save Theme Settings", type="primary", use_container_width=True):
            update_system_setting('primary_color', primary_color, st.session_state.user_id)
            update_system_setting('secondary_color', secondary_color, st.session_state.user_id)
            update_system_setting('accent_color', accent_color, st.session_state.user_id)
            update_system_setting('background_color', background_color, st.session_state.user_id)
            update_system_setting('sidebar_color', sidebar_color, st.session_state.user_id)
            update_system_setting('font_family', font_family, st.session_state.user_id)
            update_system_setting('font_size', font_size, st.session_state.user_id)
            update_system_setting('card_border_radius', str(card_border_radius), st.session_state.user_id)
            update_system_setting('system_name', system_name, st.session_state.user_id)
            update_system_setting('favicon', favicon, st.session_state.user_id)
            update_system_setting('footer_text', footer_text, st.session_state.user_id)
            st.success("Theme saved successfully! Refreshing...")
            st.rerun()
    
    with col2:
        st.subheader("🔍 Live Preview")
        st.markdown(f"""
        <div style="background-color: {background_color}; padding: 20px; border-radius: {card_border_radius}px;">
            <h1 style="color: {primary_color};">{system_name}</h1>
            <div style="background-color: {sidebar_color}; padding: 15px; border-radius: {card_border_radius}px; margin: 10px 0;">
                <p style="color: white;">Sidebar navigation preview</p>
            </div>
            <button style="background-color: {primary_color}; color: white; padding: 10px 20px; border: none; border-radius: 5px;">
                Button Preview
            </button>
            <div style="background-color: {secondary_color}; color: white; padding: 10px; margin-top: 10px; border-radius: {card_border_radius}px;">
                <p>Secondary color preview</p>
            </div>
        </div>
        """, unsafe_allow_html=True)