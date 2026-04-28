"""Authentication and user management"""
import hashlib
import streamlit as st
from datetime import datetime
from database.connection import get_connection
from services.audit_service import log_audit

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_info(username):
    """Get complete user information"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT u.id, u.username, u.full_name, u.email, u.phone, u.role, u.assigned_branch_id, u.is_active,
                        b.branch_name, b.branch_code
                 FROM users u
                 LEFT JOIN branches b ON u.assigned_branch_id = b.id
                 WHERE u.username = ?""", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'full_name': user[2],
            'email': user[3],
            'phone': user[4],
            'role': user[5],
            'assigned_branch_id': user[6],
            'is_active': user[7],
            'branch_name': user[8],
            'branch_code': user[9]
        }
    return None

def check_login(username, password):
    """Authenticate user and return user info"""
    conn = get_connection()
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND is_active=1", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    
    if user:
        user_info = get_user_info(username)
        if user_info:
            # Update last login
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_info['id']))
            conn.commit()
            conn.close()
            log_audit(user_info['id'], username, 'LOGIN', 'user', user_info['id'], f"User logged in")
            return user_info
    return None