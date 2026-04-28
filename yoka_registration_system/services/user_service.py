"""User management services"""
import pandas as pd
from datetime import datetime
from database.connection import get_connection
from services.audit_service import log_audit
from services.email_service import send_user_credentials_email
from auth.authentication import hash_password
import streamlit as st

def create_user(username, password, full_name, email, phone, role, assigned_branch_id, created_by):
    """Create a new user"""
    conn = get_connection()
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        c.execute("""INSERT INTO users (username, password, full_name, email, phone, role, assigned_branch_id, created_by, created_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (username, hashed_password, full_name, email, phone, role, assigned_branch_id, created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        user_id = c.lastrowid
        conn.commit()
        log_audit(created_by, st.session_state.username, 'CREATE_USER', 'user', user_id, f"Created user: {username} with role: {role}")
        
        # Send email notification
        send_user_credentials_email(email, username, password, full_name, role)
        
        return True, user_id
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def reset_user_password(user_id, new_password, updated_by):
    """Reset user password and notify via email"""
    conn = get_connection()
    c = conn.cursor()
    hashed_password = hash_password(new_password)
    
    # Get user email
    c.execute("SELECT email, full_name, username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    conn.commit()
    
    if user:
        from services.email_service import send_password_reset_email
        send_password_reset_email(user[0], user[1], user[2], new_password)
    
    log_audit(updated_by, st.session_state.username, 'RESET_PASSWORD', 'user', user_id, f"Reset password for user ID: {user_id}")
    conn.close()
    return True

def get_all_users():
    """Get all users with branch information"""
    conn = get_connection()
    query = """SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role, 
                      b.branch_name as assigned_branch, u.is_active, u.created_date, u.last_login
               FROM users u
               LEFT JOIN branches b ON u.assigned_branch_id = b.id
               ORDER BY u.created_date DESC"""
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(user_id, full_name, email, phone, role, assigned_branch_id, is_active, updated_by):
    """Update user information"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE users 
                 SET full_name = ?, email = ?, phone = ?, role = ?, assigned_branch_id = ?, is_active = ?
                 WHERE id = ?""",
              (full_name, email, phone, role, assigned_branch_id, is_active, user_id))
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'UPDATE_USER', 'user', user_id, f"Updated user ID: {user_id}")
    conn.close()
    return True

def delete_user(user_id, deleted_by):
    """Soft delete a user (deactivate)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.username, 'DELETE_USER', 'user', user_id, f"Deactivated user ID: {user_id}")
    conn.close()
    return True