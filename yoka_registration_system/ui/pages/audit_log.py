"""Audit log viewer UI"""
import streamlit as st
import pandas as pd
from datetime import datetime
from services.audit_service import get_audit_logs

def audit_log_ui():
    """View audit logs (super admin only)"""
    if st.session_state.user_role != 'super_admin':
        st.error("Only Super Admin can access audit logs")
        return
    
    st.title("📜 Audit Log")
    
    df = get_audit_logs(limit=1000)
    
    if not df.empty:
        st.dataframe(df[['timestamp', 'username', 'action', 'entity_type', 'entity_id', 'details']], 
                    use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button("Download Audit Log", csv, 
                         f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    else:
        st.info("No audit logs found")