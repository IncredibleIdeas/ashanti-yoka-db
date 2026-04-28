"""Branch management services"""
import pandas as pd
from datetime import datetime
from database.connection import get_connection
from services.audit_service import log_audit
import streamlit as st

def create_branch(branch_name, branch_code, location, contact_person, contact_phone, created_by):
    """Create a new branch"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO branches (branch_name, branch_code, location, contact_person, contact_phone, created_date)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (branch_name, branch_code, location, contact_person, contact_phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        branch_id = c.lastrowid
        conn.commit()
        log_audit(created_by, st.session_state.username, 'CREATE_BRANCH', 'branch', branch_id, f"Created branch: {branch_name}")
        return True, branch_id
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_all_branches(include_inactive=False):
    """Get all branches"""
    conn = get_connection()
    if include_inactive:
        df = pd.read_sql_query("SELECT * FROM branches ORDER BY branch_name", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM branches WHERE is_active = 1 ORDER BY branch_name", conn)
    conn.close()
    return df

def get_branch_by_id(branch_id):
    """Get branch by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM branches WHERE id = ?", (branch_id,))
    branch = c.fetchone()
    conn.close()
    return branch

def update_branch(branch_id, branch_name, branch_code, location, contact_person, contact_phone, updated_by):
    """Update branch information"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE branches 
                 SET branch_name = ?, branch_code = ?, location = ?, contact_person = ?, contact_phone = ?
                 WHERE id = ?""",
              (branch_name, branch_code, location, contact_person, contact_phone, branch_id))
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'UPDATE_BRANCH', 'branch', branch_id, f"Updated branch: {branch_name}")
    conn.close()
    return True

def delete_branch(branch_id, deleted_by):
    """Soft delete a branch (deactivate)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE branches SET is_active = 0 WHERE id = ?", (branch_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.username, 'DELETE_BRANCH', 'branch', branch_id, f"Deactivated branch ID: {branch_id}")
    conn.close()
    return True