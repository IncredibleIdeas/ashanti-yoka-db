"""System settings management"""
import pandas as pd
from database.connection import get_connection
from services.audit_service import log_audit
import streamlit as st

def get_system_settings():
    """Get all system settings"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM system_settings", conn)
    conn.close()
    return df

def update_system_setting(setting_key, setting_value, updated_by):
    """Update system setting"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE system_settings SET setting_value = ? WHERE setting_key = ?", (setting_value, setting_key))
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'UPDATE_SETTING', 'system', None, f"Updated setting: {setting_key} = {setting_value}")
    conn.close()
    return True