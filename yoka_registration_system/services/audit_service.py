"""Audit logging service"""
from datetime import datetime
from database.connection import get_connection

def log_audit(user_id, username, action, entity_type, entity_id, details=""):
    """Log user actions for audit trail"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, username, action, entity_type, entity_id, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_audit_logs(limit=1000):
    """Get audit logs"""
    conn = get_connection()
    import pandas as pd
    df = pd.read_sql_query(f"SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df