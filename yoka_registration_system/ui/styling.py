"""Custom styling and theming"""
import streamlit as st
from services.settings_service import get_system_settings

def apply_custom_styling():
    """Apply custom styling from system settings"""
    try:
        settings_df = get_system_settings()
        if not settings_df.empty:
            settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()}
        else:
            settings = {}
        
        font_family = settings.get('font_family', 'System Default')
        font_size = settings.get('font_size', '16px')
        primary_color = settings.get('primary_color', '#1E3A8A')
        secondary_color = settings.get('secondary_color', '#3B82F6')
        background_color = settings.get('background_color', '#FFFFFF')
        sidebar_color = settings.get('sidebar_color', '#1E3A8A')
        card_border_radius = settings.get('card_border_radius', '10')
        
        font_family_css = ""
        if font_family != "System Default":
            font_family_css = f"font-family: '{font_family}', sans-serif;"
        
        st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap');
            
            .stApp {{ background-color: {background_color}; }}
            
            body, .stApp, .stMarkdown, .stTextInput, .stSelectbox, .stTextArea {{
                {font_family_css}
                font-size: {font_size};
            }}
            
            .stButton > button {{
                background-color: {primary_color};
                color: white;
                border-radius: 8px;
                border: none;
                padding: 0.5rem 1rem;
                font-weight: 500;
                transition: all 0.3s ease;
            }}
            
            .stButton > button:hover {{
                background-color: {secondary_color};
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            
            h1, h2, h3, h4, h5, h6 {{ color: {primary_color}; font-weight: 600; }}
            
            .css-1d391kg, .css-12oz5g7 {{ background-color: {sidebar_color}; }}
            
            .stSidebar .stMarkdown, .stSidebar .stTextInput, .stSidebar label {{ color: white; }}
            
            .stDataFrame {{ border-radius: {card_border_radius}px; overflow: hidden; }}
            
            .success-box {{
                background-color: #d4edda;
                padding: 20px;
                border-radius: {card_border_radius}px;
                border-left: 5px solid #28a745;
                margin: 10px 0;
            }}
            
            .info-box {{
                background-color: #d1ecf1;
                padding: 15px;
                border-radius: {card_border_radius}px;
                border-left: 5px solid #17a2b8;
                margin: 10px 0;
            }}
            
            .warning-box {{
                background-color: #fff3cd;
                padding: 15px;
                border-radius: {card_border_radius}px;
                border-left: 5px solid #ffc107;
                margin: 10px 0;
            }}
            
            .metric-card {{
                background-color: white;
                padding: 15px;
                border-radius: {card_border_radius}px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
                color: {primary_color};
            }}
            
            .metric-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        </style>
        """, unsafe_allow_html=True)
    except:
        pass