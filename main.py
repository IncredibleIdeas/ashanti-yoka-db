import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os
from PIL import Image
import io
import json
import plotly.express as px
import plotly.graph_objects as go
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import qrcode
from io import BytesIO
import re

# Page configuration MUST be the first Streamlit command
st.set_page_config(page_title="Kumasi District YoKA Registration System", page_icon="⛪", layout="wide")

# ==================== DATABASE SETUP WITH RBAC ====================

def init_rbac_database():
    """Initialize database with complete RBAC schema"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    # Create branches table
    c.execute('''CREATE TABLE IF NOT EXISTS branches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  branch_name TEXT UNIQUE NOT NULL,
                  branch_code TEXT UNIQUE NOT NULL,
                  location TEXT,
                  contact_person TEXT,
                  contact_phone TEXT,
                  created_date TEXT NOT NULL,
                  is_active BOOLEAN DEFAULT 1)''')
    
    # Create users table with role and branch assignment
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  full_name TEXT NOT NULL,
                  email TEXT,
                  phone TEXT,
                  role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'branch_executive')),
                  assigned_branch_id INTEGER,
                  is_active BOOLEAN DEFAULT 1,
                  created_by INTEGER,
                  created_date TEXT NOT NULL,
                  last_login TEXT,
                  FOREIGN KEY (assigned_branch_id) REFERENCES branches(id),
                  FOREIGN KEY (created_by) REFERENCES users(id))''')
    
    # Create members table with branch assignment and all new fields
    c.execute('''CREATE TABLE IF NOT EXISTS members
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  official_name TEXT NOT NULL,
                  date_of_birth TEXT,
                  age INTEGER NOT NULL,
                  residence TEXT NOT NULL,
                  active_phone TEXT NOT NULL,
                  email TEXT,
                  profile_picture BLOB,
                  school_name TEXT NOT NULL,
                  school_level TEXT NOT NULL,
                  school_class TEXT NOT NULL,
                  school_house TEXT,
                  residence_status TEXT NOT NULL,
                  residence_name TEXT,
                  church_branch TEXT NOT NULL,
                  branch_id INTEGER NOT NULL,
                  yoka_hall TEXT NOT NULL,
                  youth_camps_attended INTEGER NOT NULL,
                  -- Church Position Fields
                  has_church_position BOOLEAN DEFAULT 0,
                  church_position_type TEXT,
                  church_position_name TEXT,
                  church_position_duration TEXT,
                  -- Work Info Fields
                  work_status TEXT,
                  work_type TEXT,
                  work_name TEXT,
                  work_position TEXT,
                  work_location TEXT,
                  work_experience_years INTEGER,
                  -- Diaspora Fields
                  is_diaspora BOOLEAN DEFAULT 0,
                  diaspora_country TEXT,
                  diaspora_status TEXT,
                  diaspora_job TEXT,
                  diaspora_school TEXT,
                  diaspora_education_level TEXT,
                  -- Parent/Guardian Fields
                  mother_name TEXT,
                  mother_phone TEXT,
                  mother_occupation TEXT,
                  father_name TEXT,
                  father_phone TEXT,
                  father_occupation TEXT,
                  guardian_name TEXT,
                  guardian_phone TEXT,
                  guardian_relationship TEXT,
                  guardian_occupation TEXT,
                  submission_date TEXT NOT NULL,
                  created_by INTEGER,
                  last_modified_by INTEGER,
                  last_modified_date TEXT,
                  is_verified BOOLEAN DEFAULT 0,
                  verified_by INTEGER,
                  verified_date TEXT,
                  gender TEXT,
                  emergency_contact_name TEXT,
                  emergency_contact_phone TEXT,
                  medical_conditions TEXT,
                  talents TEXT,
                  interests TEXT,
                  FOREIGN KEY (branch_id) REFERENCES branches(id),
                  FOREIGN KEY (created_by) REFERENCES users(id))''')
    
    # Create audit_log table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  action TEXT NOT NULL,
                  entity_type TEXT NOT NULL,
                  entity_id INTEGER,
                  details TEXT,
                  ip_address TEXT,
                  timestamp TEXT NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    # Create system_settings table for branding
    c.execute('''CREATE TABLE IF NOT EXISTS system_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  setting_key TEXT UNIQUE NOT NULL,
                  setting_value TEXT,
                  setting_type TEXT DEFAULT 'text',
                  description TEXT)''')
    
    # Create email_settings table
    c.execute('''CREATE TABLE IF NOT EXISTS email_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  smtp_server TEXT,
                  smtp_port INTEGER,
                  sender_email TEXT,
                  sender_password TEXT,
                  use_tls BOOLEAN DEFAULT 1,
                  updated_by INTEGER,
                  updated_date TEXT)''')
    
    # Create email_logs table
    c.execute('''CREATE TABLE IF NOT EXISTS email_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  recipient_email TEXT,
                  subject TEXT,
                  message TEXT,
                  status TEXT,
                  sent_date TEXT,
                  sent_by INTEGER)''')
    
    # Insert default branches
    default_branches = [
        ('Kumasi Central', 'KMC', 'Kumasi Central Business District', 'Rev. John Doe', '0244000001'),
        ('Asokwa', 'ASK', 'Asokwa District', 'Rev. Jane Smith', '0244000002'),
        ('Tafo', 'TAF', 'Tafo Community', 'Rev. Michael Brown', '0244000003'),
        ('Suame', 'SUA', 'Suame Magazine Area', 'Rev. Sarah Johnson', '0244000004'),
        ('Bantama', 'BAN', 'Bantama Community', 'Rev. David Wilson', '0244000005')
    ]
    
    for branch in default_branches:
        c.execute("INSERT OR IGNORE INTO branches (branch_name, branch_code, location, contact_person, contact_phone, created_date) VALUES (?, ?, ?, ?, ?, ?)",
                  (branch[0], branch[1], branch[2], branch[3], branch[4], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Insert default super admin if not exists
    c.execute("SELECT * FROM users WHERE username='super_admin'")
    if not c.fetchone():
        hashed_password = hashlib.sha256('SuperAdmin@123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, full_name, email, phone, role, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ('super_admin', hashed_password, 'Super Administrator', 'superadmin@yoka.org', '0244000000', 'super_admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Insert default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_password = hashlib.sha256('Admin@123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, full_name, email, phone, role, assigned_branch_id, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('admin', hashed_password, 'District Administrator', 'admin@yoka.org', '0244000006', 'admin', 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Insert default branch executive for each branch
    branch_execs = [
        ('exec_central', 'Central@123', 'Central Branch Executive', 'central@yoka.org', '0244000010', 1),
        ('exec_asokwa', 'Asokwa@123', 'Asokwa Branch Executive', 'asokwa@yoka.org', '0244000011', 2),
        ('exec_tafo', 'Tafo@123', 'Tafo Branch Executive', 'tafo@yoka.org', '0244000012', 3)
    ]
    
    for exec_data in branch_execs:
        c.execute("SELECT * FROM users WHERE username=?", (exec_data[0],))
        if not c.fetchone():
            hashed_password = hashlib.sha256(exec_data[1].encode()).hexdigest()
            c.execute("INSERT INTO users (username, password, full_name, email, phone, role, assigned_branch_id, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (exec_data[0], hashed_password, exec_data[2], exec_data[3], exec_data[4], 'branch_executive', exec_data[5], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Insert default system settings
    default_settings = [
        ('system_name', 'Kumasi District YoKA Registration System', 'text', 'System display name'),
        ('primary_color', '#1E3A8A', 'color', 'Primary theme color'),
        ('secondary_color', '#3B82F6', 'color', 'Secondary theme color'),
        ('accent_color', '#F59E0B', 'color', 'Accent theme color'),
        ('background_color', '#FFFFFF', 'color', 'Background color'),
        ('sidebar_color', '#1E3A8A', 'color', 'Sidebar color'),
        ('font_family', 'System Default', 'text', 'Font family'),
        ('font_size', '16px', 'text', 'Base font size'),
        ('card_border_radius', '10', 'text', 'Card border radius'),
        ('logo_url', '', 'text', 'URL to system logo'),
        ('favicon', '⛪', 'text', 'Favicon emoji or URL'),
        ('footer_text', '© 2024 Kumasi District YoKA. All Rights Reserved.', 'text', 'Footer text'),
        ('registration_open', 'true', 'boolean', 'Whether registration is open')
    ]
    
    for setting in default_settings:
        c.execute("INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES (?, ?, ?, ?)",
                  (setting[0], setting[1], setting[2], setting[3]))
    
    conn.commit()
    conn.close()

# ==================== EMAIL FUNCTIONS ====================

def get_email_settings():
    """Get email configuration settings"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("SELECT * FROM email_settings ORDER BY id DESC LIMIT 1")
    settings = c.fetchone()
    conn.close()
    
    if settings:
        return {
            'smtp_server': settings[1],
            'smtp_port': settings[2],
            'sender_email': settings[3],
            'sender_password': settings[4],
            'use_tls': settings[5]
        }
    return None

def save_email_settings(smtp_server, smtp_port, sender_email, sender_password, use_tls, updated_by):
    """Save email configuration"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("DELETE FROM email_settings")  # Keep only latest settings
    c.execute("""INSERT INTO email_settings 
                 (smtp_server, smtp_port, sender_email, sender_password, use_tls, updated_by, updated_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (smtp_server, smtp_port, sender_email, sender_password, use_tls, updated_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def send_email(recipient_email, subject, body):
    """Send email using configured settings"""
    settings = get_email_settings()
    if not settings:
        return False, "Email settings not configured"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = settings['sender_email']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(settings['smtp_server'], settings['smtp_port'])
        if settings['use_tls']:
            server.starttls()
        server.login(settings['sender_email'], settings['sender_password'])
        server.send_message(msg)
        server.quit()
        
        # Log email
        conn = sqlite3.connect('kumasi_yoka_registration.db')
        c = conn.cursor()
        c.execute("""INSERT INTO email_logs (recipient_email, subject, message, status, sent_date, sent_by)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (recipient_email, subject, body, 'sent', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   st.session_state.get('user_id', 1)))
        conn.commit()
        conn.close()
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

def send_user_credentials_email(email, username, password, full_name, role):
    """Send login credentials to user via email"""
    subject = "Welcome to YoKA Registration System - Your Login Credentials"
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .container {{ padding: 20px; background-color: #f4f4f4; }}
            .header {{ background-color: #1E3A8A; color: white; padding: 10px; text-align: center; }}
            .content {{ background-color: white; padding: 20px; margin: 20px 0; }}
            .credentials {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; }}
            .footer {{ text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Kumasi District YoKA Registration System</h2>
            </div>
            <div class="content">
                <h3>Dear {full_name},</h3>
                <p>Your account has been created in the YoKA Registration System with the following credentials:</p>
                
                <div class="credentials">
                    <p><strong>Username:</strong> {username}</p>
                    <p><strong>Password:</strong> {password}</p>
                    <p><strong>Role:</strong> {role.replace('_', ' ').title()}</p>
                </div>
                
                <p><strong>Important:</strong> Please change your password after your first login.</p>
                <p>You can access the system using the login page.</p>
                
                <h4>Security Tips:</h4>
                <ul>
                    <li>Never share your password with anyone</li>
                    <li>Use a strong password</li>
                    <li>Log out after each session</li>
                </ul>
            </div>
            <div class="footer">
                <p>This is an automated message, please do not reply.</p>
                <p>© 2024 Kumasi District YoKA. All Rights Reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, body)

# ==================== HELPER FUNCTIONS ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_audit(user_id, username, action, entity_type, entity_id, details=""):
    """Log user actions for audit trail"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (user_id, username, action, entity_type, entity_id, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_user_info(username):
    """Get complete user information"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
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
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND is_active=1", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    
    if user:
        user_info = get_user_info(username)
        # Update last login
        conn = sqlite3.connect('kumasi_yoka_registration.db')
        c = conn.cursor()
        c.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_info['id']))
        conn.commit()
        conn.close()
        log_audit(user_info['id'], username, 'LOGIN', 'user', user_info['id'], f"User logged in")
        return user_info
    return None

# ==================== CRUD OPERATIONS FOR BRANCHES ====================

def create_branch(branch_name, branch_code, location, contact_person, contact_phone, created_by):
    """Create a new branch"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO branches (branch_name, branch_code, location, contact_person, contact_phone, created_date)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (branch_name, branch_code, location, contact_person, contact_phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        branch_id = c.lastrowid
        conn.commit()
        log_audit(created_by, st.session_state.username, 'CREATE_BRANCH', 'branch', branch_id, f"Created branch: {branch_name}")
        return True, branch_id
    except sqlite3.IntegrityError:
        return False, "Branch name or code already exists"
    finally:
        conn.close()

def get_all_branches(include_inactive=False):
    """Get all branches"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    if include_inactive:
        df = pd.read_sql_query("SELECT * FROM branches ORDER BY branch_name", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM branches WHERE is_active = 1 ORDER BY branch_name", conn)
    conn.close()
    return df

def get_branch_by_id(branch_id):
    """Get branch by ID"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("SELECT * FROM branches WHERE id = ?", (branch_id,))
    branch = c.fetchone()
    conn.close()
    return branch

def update_branch(branch_id, branch_name, branch_code, location, contact_person, contact_phone, updated_by):
    """Update branch information"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
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
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("UPDATE branches SET is_active = 0 WHERE id = ?", (branch_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.username, 'DELETE_BRANCH', 'branch', branch_id, f"Deactivated branch ID: {branch_id}")
    conn.close()
    return True

# ==================== CRUD OPERATIONS FOR USERS ====================

def create_user(username, password, full_name, email, phone, role, assigned_branch_id, created_by):
    """Create a new user"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
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
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def reset_user_password(user_id, new_password, updated_by):
    """Reset user password and notify via email"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    hashed_password = hash_password(new_password)
    
    # Get user email
    c.execute("SELECT email, full_name, username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    
    c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
    conn.commit()
    
    if user:
        # Send password reset email
        subject = "YoKA System - Password Reset Notification"
        body = f"""
        <html>
        <body>
            <h3>Password Reset</h3>
            <p>Dear {user[1]},</p>
            <p>Your password has been reset. Your new login credentials are:</p>
            <p><strong>Username:</strong> {user[2]}</p>
            <p><strong>New Password:</strong> {new_password}</p>
            <p>Please change your password after logging in.</p>
        </body>
        </html>
        """
        send_email(user[0], subject, body)
    
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'RESET_PASSWORD', 'user', user_id, f"Reset password for user ID: {user_id}")
    conn.close()
    return True

def get_all_users():
    """Get all users with branch information"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
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
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(user_id, full_name, email, phone, role, assigned_branch_id, is_active, updated_by):
    """Update user information"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
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
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.username, 'DELETE_USER', 'user', user_id, f"Deactivated user ID: {user_id}")
    conn.close()
    return True

# ==================== CRUD OPERATIONS FOR MEMBERS ====================

def save_member(data, profile_picture=None, created_by=None):
    """Save member with all new fields"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    # Get branch ID from branch name
    c.execute("SELECT id FROM branches WHERE branch_name = ?", (data['church_branch'],))
    branch_result = c.fetchone()
    branch_id = branch_result[0] if branch_result else 1
    
    c.execute('''INSERT INTO members 
                 (official_name, date_of_birth, age, residence, active_phone, email, profile_picture,
                  school_name, school_level, school_class, school_house, residence_status, residence_name,
                  church_branch, branch_id, yoka_hall, youth_camps_attended,
                  has_church_position, church_position_type, church_position_name, church_position_duration,
                  work_status, work_type, work_name, work_position, work_location, work_experience_years,
                  is_diaspora, diaspora_country, diaspora_status, diaspora_job, diaspora_school, diaspora_education_level,
                  mother_name, mother_phone, mother_occupation,
                  father_name, father_phone, father_occupation,
                  guardian_name, guardian_phone, guardian_relationship, guardian_occupation,
                  submission_date, created_by, last_modified_date, gender, emergency_contact_name,
                  emergency_contact_phone, medical_conditions, talents, interests)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['official_name'], data['date_of_birth'], data['age'], data['residence'], 
               data['active_phone'], data['email'], profile_picture,
               data['school_name'], data['school_level'], data['school_class'], 
               data['school_house'], data['residence_status'], data['residence_name'],
               data['church_branch'], branch_id, data['yoka_hall'], data['youth_camps_attended'],
               data['has_church_position'], data['church_position_type'], data['church_position_name'], data['church_position_duration'],
               data['work_status'], data['work_type'], data['work_name'], data['work_position'], data['work_location'], data['work_experience_years'],
               data['is_diaspora'], data['diaspora_country'], data['diaspora_status'], data['diaspora_job'], 
               data['diaspora_school'], data['diaspora_education_level'],
               data['mother_name'], data['mother_phone'], data['mother_occupation'],
               data['father_name'], data['father_phone'], data['father_occupation'],
               data['guardian_name'], data['guardian_phone'], data['guardian_relationship'], data['guardian_occupation'],
               datetime.now().strftime("%Y-%m-%d %H:%M:%S"), created_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               data.get('gender', ''), data.get('emergency_contact_name', ''),
               data.get('emergency_contact_phone', ''), data.get('medical_conditions', ''),
               data.get('talents', ''), data.get('interests', '')))
    
    member_id = c.lastrowid
    conn.commit()
    log_audit(created_by, st.session_state.username, 'CREATE_MEMBER', 'member', member_id, f"Created member: {data['official_name']}")
    conn.close()
    return member_id

def get_members_by_role(user_role, user_branch_id=None, user_id=None):
    """Get members based on user role and permissions"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    
    if user_role == 'super_admin':
        df = pd.read_sql_query("SELECT * FROM members ORDER BY submission_date DESC", conn)
    elif user_role == 'admin':
        df = pd.read_sql_query("SELECT * FROM members ORDER BY submission_date DESC", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM members WHERE branch_id = ? ORDER BY submission_date DESC", conn, params=(user_branch_id,))
    
    conn.close()
    return df

def get_member_by_id(member_id, user_role, user_branch_id=None):
    """Get member by ID with permission check"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    if user_role == 'branch_executive':
        c.execute("SELECT * FROM members WHERE id = ? AND branch_id = ?", (member_id, user_branch_id))
    else:
        c.execute("SELECT * FROM members WHERE id = ?", (member_id,))
    
    member = c.fetchone()
    conn.close()
    return member

def update_member(member_id, data, updated_by):
    """Update member information with all new fields"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    c.execute("SELECT id FROM branches WHERE branch_name = ?", (data['church_branch'],))
    branch_result = c.fetchone()
    branch_id = branch_result[0] if branch_result else 1
    
    c.execute('''UPDATE members SET
                 official_name = ?, date_of_birth = ?, age = ?, residence = ?, active_phone = ?, email = ?,
                 school_name = ?, school_level = ?, school_class = ?, school_house = ?,
                 residence_status = ?, residence_name = ?, church_branch = ?, branch_id = ?,
                 yoka_hall = ?, youth_camps_attended = ?,
                 has_church_position = ?, church_position_type = ?, church_position_name = ?, church_position_duration = ?,
                 work_status = ?, work_type = ?, work_name = ?, work_position = ?, work_location = ?, work_experience_years = ?,
                 is_diaspora = ?, diaspora_country = ?, diaspora_status = ?, diaspora_job = ?,
                 diaspora_school = ?, diaspora_education_level = ?,
                 mother_name = ?, mother_phone = ?, mother_occupation = ?,
                 father_name = ?, father_phone = ?, father_occupation = ?,
                 guardian_name = ?, guardian_phone = ?, guardian_relationship = ?, guardian_occupation = ?,
                 last_modified_by = ?, last_modified_date = ?, gender = ?, emergency_contact_name = ?,
                 emergency_contact_phone = ?, medical_conditions = ?, talents = ?, interests = ?
                 WHERE id = ?''',
              (data['official_name'], data['date_of_birth'], data['age'], data['residence'], data['active_phone'], data['email'],
               data['school_name'], data['school_level'], data['school_class'], data['school_house'],
               data['residence_status'], data['residence_name'], data['church_branch'], branch_id,
               data['yoka_hall'], data['youth_camps_attended'],
               data['has_church_position'], data['church_position_type'], data['church_position_name'], data['church_position_duration'],
               data['work_status'], data['work_type'], data['work_name'], data['work_position'], data['work_location'], data['work_experience_years'],
               data['is_diaspora'], data['diaspora_country'], data['diaspora_status'], data['diaspora_job'],
               data['diaspora_school'], data['diaspora_education_level'],
               data['mother_name'], data['mother_phone'], data['mother_occupation'],
               data['father_name'], data['father_phone'], data['father_occupation'],
               data['guardian_name'], data['guardian_phone'], data['guardian_relationship'], data['guardian_occupation'],
               updated_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               data.get('gender', ''), data.get('emergency_contact_name', ''),
               data.get('emergency_contact_phone', ''), data.get('medical_conditions', ''),
               data.get('talents', ''), data.get('interests', ''), member_id))
    
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'UPDATE_MEMBER', 'member', member_id, f"Updated member ID: {member_id}")
    conn.close()
    return True

def delete_member(member_id, deleted_by, user_role, user_branch_id=None):
    """Delete member with permission check"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    if user_role == 'branch_executive':
        c.execute("SELECT branch_id FROM members WHERE id = ?", (member_id,))
        member = c.fetchone()
        if member and member[0] != user_branch_id:
            conn.close()
            return False, "Permission denied: Cannot delete members from other branches"
    
    c.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.username, 'DELETE_MEMBER', 'member', member_id, f"Deleted member ID: {member_id}")
    conn.close()
    return True, "Member deleted successfully"

def verify_member(member_id, verified_by):
    """Verify member data"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("""UPDATE members 
                 SET is_verified = 1, verified_by = ?, verified_date = ?
                 WHERE id = ?""",
              (verified_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), member_id))
    conn.commit()
    log_audit(verified_by, st.session_state.username, 'VERIFY_MEMBER', 'member', member_id, f"Verified member ID: {member_id}")
    conn.close()
    return True

# ==================== IMPORT/EXPORT FUNCTIONS ====================

def export_to_excel(df, include_photos=False):
    """Export DataFrame to Excel with formatting"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Members', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Members']
        
        # Add formatting
        from openpyxl.styles import Font, PatternFill, Alignment
        
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return output.getvalue()

def import_from_csv(file, target_branch, created_by):
    """Import members from CSV file"""
    df = pd.read_csv(file)
    success_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            data = {
                'official_name': row.get('official_name', ''),
                'date_of_birth': str(row.get('date_of_birth', '')) if pd.notna(row.get('date_of_birth')) else '',
                'age': row.get('age', 18),
                'residence': row.get('residence', ''),
                'active_phone': row.get('active_phone', ''),
                'email': row.get('email', ''),
                'school_name': row.get('school_name', ''),
                'school_level': row.get('school_level', 'SHS'),
                'school_class': row.get('school_class', ''),
                'school_house': row.get('school_house', ''),
                'residence_status': row.get('residence_status', 'Day Student'),
                'residence_name': row.get('residence_name', ''),
                'church_branch': target_branch,
                'yoka_hall': row.get('yoka_hall', 'Hall A'),
                'youth_camps_attended': row.get('youth_camps_attended', 0),
                'has_church_position': row.get('has_church_position', False),
                'church_position_type': row.get('church_position_type', ''),
                'church_position_name': row.get('church_position_name', ''),
                'church_position_duration': row.get('church_position_duration', ''),
                'work_status': row.get('work_status', ''),
                'work_type': row.get('work_type', ''),
                'work_name': row.get('work_name', ''),
                'work_position': row.get('work_position', ''),
                'work_location': row.get('work_location', ''),
                'work_experience_years': row.get('work_experience_years', 0),
                'is_diaspora': row.get('is_diaspora', False),
                'diaspora_country': row.get('diaspora_country', ''),
                'diaspora_status': row.get('diaspora_status', ''),
                'diaspora_job': row.get('diaspora_job', ''),
                'diaspora_school': row.get('diaspora_school', ''),
                'diaspora_education_level': row.get('diaspora_education_level', ''),
                'mother_name': row.get('mother_name', ''),
                'mother_phone': row.get('mother_phone', ''),
                'mother_occupation': row.get('mother_occupation', ''),
                'father_name': row.get('father_name', ''),
                'father_phone': row.get('father_phone', ''),
                'father_occupation': row.get('father_occupation', ''),
                'guardian_name': row.get('guardian_name', ''),
                'guardian_phone': row.get('guardian_phone', ''),
                'guardian_relationship': row.get('guardian_relationship', ''),
                'guardian_occupation': row.get('guardian_occupation', ''),
                'gender': row.get('gender', ''),
                'emergency_contact_name': row.get('emergency_contact_name', ''),
                'emergency_contact_phone': row.get('emergency_contact_phone', ''),
                'medical_conditions': row.get('medical_conditions', ''),
                'talents': row.get('talents', ''),
                'interests': row.get('interests', '')
            }
            save_member(data, created_by=created_by)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {idx+2}: {str(e)}")
    
    return success_count, errors

def import_from_excel(file, target_branch, created_by):
    """Import members from Excel file"""
    df = pd.read_excel(file)
    success_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            data = {
                'official_name': row.get('official_name', ''),
                'date_of_birth': str(row.get('date_of_birth', '')) if pd.notna(row.get('date_of_birth')) else '',
                'age': row.get('age', 18),
                'residence': row.get('residence', ''),
                'active_phone': row.get('active_phone', ''),
                'email': row.get('email', ''),
                'school_name': row.get('school_name', ''),
                'school_level': row.get('school_level', 'SHS'),
                'school_class': row.get('school_class', ''),
                'school_house': row.get('school_house', ''),
                'residence_status': row.get('residence_status', 'Day Student'),
                'residence_name': row.get('residence_name', ''),
                'church_branch': target_branch,
                'yoka_hall': row.get('yoka_hall', 'Hall A'),
                'youth_camps_attended': row.get('youth_camps_attended', 0),
                'has_church_position': row.get('has_church_position', False),
                'church_position_type': row.get('church_position_type', ''),
                'church_position_name': row.get('church_position_name', ''),
                'church_position_duration': row.get('church_position_duration', ''),
                'work_status': row.get('work_status', ''),
                'work_type': row.get('work_type', ''),
                'work_name': row.get('work_name', ''),
                'work_position': row.get('work_position', ''),
                'work_location': row.get('work_location', ''),
                'work_experience_years': row.get('work_experience_years', 0),
                'is_diaspora': row.get('is_diaspora', False),
                'diaspora_country': row.get('diaspora_country', ''),
                'diaspora_status': row.get('diaspora_status', ''),
                'diaspora_job': row.get('diaspora_job', ''),
                'diaspora_school': row.get('diaspora_school', ''),
                'diaspora_education_level': row.get('diaspora_education_level', ''),
                'mother_name': row.get('mother_name', ''),
                'mother_phone': row.get('mother_phone', ''),
                'mother_occupation': row.get('mother_occupation', ''),
                'father_name': row.get('father_name', ''),
                'father_phone': row.get('father_phone', ''),
                'father_occupation': row.get('father_occupation', ''),
                'guardian_name': row.get('guardian_name', ''),
                'guardian_phone': row.get('guardian_phone', ''),
                'guardian_relationship': row.get('guardian_relationship', ''),
                'guardian_occupation': row.get('guardian_occupation', ''),
                'gender': row.get('gender', ''),
                'emergency_contact_name': row.get('emergency_contact_name', ''),
                'emergency_contact_phone': row.get('emergency_contact_phone', ''),
                'medical_conditions': row.get('medical_conditions', ''),
                'talents': row.get('talents', ''),
                'interests': row.get('interests', '')
            }
            save_member(data, created_by=created_by)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {idx+2}: {str(e)}")
    
    return success_count, errors

# ==================== SYSTEM SETTINGS FUNCTIONS ====================

def get_system_settings():
    """Get all system settings"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    df = pd.read_sql_query("SELECT * FROM system_settings", conn)
    conn.close()
    return df

def update_system_setting(setting_key, setting_value, updated_by):
    """Update system setting"""
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    c.execute("UPDATE system_settings SET setting_value = ? WHERE setting_key = ?", (setting_value, setting_key))
    conn.commit()
    log_audit(updated_by, st.session_state.username, 'UPDATE_SETTING', 'system', None, f"Updated setting: {setting_key} = {setting_value}")
    conn.close()
    return True

def apply_custom_styling():
    """Apply custom styling from system settings"""
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()}
    
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
        
        .stApp {{
            background-color: {background_color};
        }}
        
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
        
        h1, h2, h3, h4, h5, h6 {{
            color: {primary_color};
            font-weight: 600;
        }}
        
        .css-1d391kg, .css-12oz5g7 {{
            background-color: {sidebar_color};
        }}
        
        .stSidebar .stMarkdown, .stSidebar .stTextInput, .stSidebar label {{
            color: white;
        }}
        
        .stDataFrame {{
            border-radius: {card_border_radius}px;
            overflow: hidden;
        }}
        
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
        
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==================== DASHBOARD & ANALYTICS ====================

def analytics_dashboard_ui():
    """Comprehensive analytics dashboard with charts"""
    st.title("📊 YoKA Analytics Dashboard")
    
    # Get data based on role
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"📈 Analytics for {st.session_state.branch_name} Branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
        selected_branch = st.selectbox("Filter by Branch", branch_options)
        if selected_branch != "All Branches":
            members_df = members_df[members_df['church_branch'] == selected_branch]
            st.info(f"📈 Analytics for {selected_branch} Branch")
        else:
            st.info("📈 Analytics for ALL Branches")
    
    if not members_df.empty:
        members_df['submission_date'] = pd.to_datetime(members_df['submission_date'])
        
        # Key Metrics
        st.subheader("📈 Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_members = len(members_df)
            new_this_month = len(members_df[members_df['submission_date'] > datetime.now() - pd.Timedelta(days=30)])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_members}</div>
                <div class="metric-label">Total Members</div>
                <small style="color: #28a745;">+{new_this_month} this month</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_age = round(members_df['age'].mean(), 1)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_age}</div>
                <div class="metric-label">Average Age</div>
                <small>years old</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            verification_rate = (members_df['is_verified'].sum() / len(members_df)) * 100
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{verification_rate:.1f}%</div>
                <div class="metric-label">Verification Rate</div>
                <small>{members_df['is_verified'].sum()} verified</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            unique_schools = members_df['school_name'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{unique_schools}</div>
                <div class="metric-label">Schools</div>
                <small>represented</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            avg_camps = round(members_df['youth_camps_attended'].mean(), 1)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_camps}</div>
                <div class="metric-label">Avg Camps</div>
                <small>per member</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Growth Trends
        st.subheader("📅 Registration Trends")
        col1, col2 = st.columns(2)
        
        with col1:
            daily_regs = members_df.set_index('submission_date').resample('D').size()
            fig_daily = px.line(x=daily_regs.index, y=daily_regs.values, 
                                title="Daily Registration Trend",
                                labels={'x': 'Date', 'y': 'Registrations'})
            fig_daily.update_layout(showlegend=False, hovermode='x unified')
            st.plotly_chart(fig_daily, use_container_width=True)
        
        with col2:
            monthly_regs = members_df.set_index('submission_date').resample('M').size()
            fig_monthly = px.bar(x=monthly_regs.index, y=monthly_regs.values,
                                 title="Monthly Registration Trend",
                                 labels={'x': 'Month', 'y': 'Registrations'})
            fig_monthly.update_layout(showlegend=False)
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Demographics
        st.subheader("👥 Demographics Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age_bins = [13, 16, 19, 22, 25, 30]
            age_labels = ['13-15', '16-18', '19-21', '22-24', '25-30']
            members_df['age_group'] = pd.cut(members_df['age'], bins=age_bins, labels=age_labels, right=False)
            age_dist = members_df['age_group'].value_counts().sort_index()
            
            fig_age = px.pie(values=age_dist.values, names=age_dist.index, title="Age Distribution")
            fig_age.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            school_level_dist = members_df['school_level'].value_counts()
            fig_school = px.bar(x=school_level_dist.index, y=school_level_dist.values,
                               title="Education Levels",
                               labels={'x': 'Level', 'y': 'Count'})
            fig_school.update_layout(showlegend=False)
            st.plotly_chart(fig_school, use_container_width=True)
        
        with col3:
            hall_dist = members_df['yoka_hall'].value_counts().head(10)
            fig_hall = px.bar(x=hall_dist.index, y=hall_dist.values,
                             title="YoKA Hall Distribution",
                             labels={'x': 'Hall', 'y': 'Members'})
            fig_hall.update_layout(showlegend=False)
            st.plotly_chart(fig_hall, use_container_width=True)
        
        # Church Positions Analysis
        if 'has_church_position' in members_df.columns:
            st.subheader("⛪ Church Leadership & Service")
            col1, col2 = st.columns(2)
            with col1:
                pos_holders = members_df[members_df['has_church_position'] == 1]
                st.metric("Members with Church Positions", len(pos_holders))
                if not pos_holders.empty:
                    pos_types = pos_holders['church_position_type'].value_counts()
                    fig_pos = px.pie(values=pos_types.values, names=pos_types.index, title="Position Types")
                    st.plotly_chart(fig_pos, use_container_width=True)
            with col2:
                if 'work_status' in members_df.columns:
                    work_status_dist = members_df['work_status'].value_counts()
                    fig_work = px.bar(x=work_status_dist.index, y=work_status_dist.values, title="Work Status Distribution")
                    st.plotly_chart(fig_work, use_container_width=True)
        
        # Export dashboard report
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Export Dashboard Report (Excel)", use_container_width=True):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    members_df.to_excel(writer, sheet_name='Raw Data', index=False)
                    
                    # Summary statistics
                    summary_data = {
                        'Metric': ['Total Members', 'Average Age', 'Verification Rate', 'Unique Schools', 'Average Camps'],
                        'Value': [len(members_df), round(members_df['age'].mean(), 1), 
                                 f"{(members_df['is_verified'].sum() / len(members_df) * 100):.1f}%",
                                 members_df['school_name'].nunique(), 
                                 round(members_df['youth_camps_attended'].mean(), 1)]
                    }
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                    
                    age_dist.to_frame().to_excel(writer, sheet_name='Age Distribution')
                    school_level_dist.to_frame().to_excel(writer, sheet_name='Education Levels')
                    hall_dist.to_frame().to_excel(writer, sheet_name='Hall Distribution')
                
                st.download_button("📥 Download Report", output.getvalue(),
                                 file_name=f"yoka_dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                 use_container_width=True)
        
        with col2:
            if st.button("📈 Generate PDF Report", use_container_width=True):
                st.info("PDF report generation would be implemented here")
        
    else:
        st.info("No data available for analytics. Start registering members to see insights!")

# ==================== IMPORT/EXPORT UI ====================

def advanced_export_ui():
    """Export data with multiple format options"""
    st.title("📥 Advanced Data Export")
    
    # Get data based on role
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"Exporting data from {st.session_state.branch_name} branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
        selected_branch = st.selectbox("Select Branch to Export", branch_options)
        if selected_branch != "All Branches":
            members_df = members_df[members_df['church_branch'] == selected_branch]
            st.info(f"Exporting data from {selected_branch} branch")
        else:
            st.info("Exporting data from ALL branches")
    
    if not members_df.empty:
        st.subheader("Export Options")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Format", ["Excel (.xlsx)", "CSV", "JSON"])
        
        with col2:
            date_range = st.date_input("Date Range", [])
            if len(date_range) == 2:
                members_df = members_df[(pd.to_datetime(members_df['submission_date']) >= pd.to_datetime(date_range[0])) &
                                       (pd.to_datetime(members_df['submission_date']) <= pd.to_datetime(date_range[1]))]
        
        # Select columns to export
        st.subheader("Select Columns to Export")
        exclude_columns = ['profile_picture', 'branch_id', 'created_by', 'last_modified_by']
        available_columns = [col for col in members_df.columns if col not in exclude_columns]
        
        selected_columns = st.multiselect("Columns", available_columns, default=available_columns[:15])
        
        if selected_columns:
            export_df = members_df[selected_columns]
            
            # Preview
            st.subheader("Preview")
            st.dataframe(export_df.head(10), use_container_width=True)
            
            st.info(f"📊 Total records to export: {len(export_df)}")
            
            # Export button
            if st.button("📥 Export Data", type="primary", use_container_width=True):
                if export_format == "Excel (.xlsx)":
                    excel_data = export_to_excel(export_df, include_photos=False)
                    st.download_button("Download Excel File", excel_data, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                elif export_format == "CSV":
                    csv = export_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                elif export_format == "JSON":
                    json_str = export_df.to_json(orient='records', indent=2)
                    st.download_button("Download JSON", json_str, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
                log_audit(st.session_state.user_id, st.session_state.username, 'EXPORT_DATA', 
                         'members', len(export_df), f"Exported {len(export_df)} records in {export_format}")
    else:
        st.info("No data to export")

def import_data_ui():
    """Import data with role-based access"""
    st.title("📤 Import Data")
    
    # Check permissions for import
    if st.session_state.user_role not in ['super_admin', 'admin']:
        st.error("You don't have permission to import data. Only Super Admin and Admin can import data.")
        return
    
    branches_df = get_all_branches()
    branch_options = ["Select Branch"] + branches_df['branch_name'].tolist()
    target_branch = st.selectbox("Import to Branch", branch_options)
    
    st.info("""
    **Import Instructions:**
    - File must contain column headers matching the database fields
    - Required fields: official_name, age, active_phone, school_name, at least one parent/guardian
    - Download the template below for correct format
    """)
    
    # Download template
    template_df = pd.DataFrame({
        'official_name': ['John Doe', 'Jane Smith'],
        'age': [18, 19],
        'active_phone': ['024XXXXXXX', '020XXXXXXX'],
        'school_name': ['Kumasi High School', 'Opoku Ware School'],
        'mother_name': ['Mrs. Jane Doe', 'Mrs. Mary Smith'],
        'mother_phone': ['024YYYYYYY', '020YYYYYYY'],
        'father_name': ['Mr. John Doe Sr.', 'Mr. James Smith'],
        'father_phone': ['024ZZZZZZZ', '020ZZZZZZZ'],
        'church_position_type': ['YoKA Executive', 'Sevent Member'],
        'work_status': ['Apprenticeship', 'Permanent Staff'],
        'diaspora_status': ['Working', 'Studying'],
        'email': ['john@example.com', 'jane@example.com'],
        'residence': ['Kumasi', 'Asokwa'],
        'school_level': ['SHS', 'Tertiary'],
        'yoka_hall': ['Hall A', 'Hall B'],
        'gender': ['Male', 'Female']
    })
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download CSV Template", template_df.to_csv(index=False),
                         file_name="import_template.csv", mime="text/csv")
    with col2:
        st.download_button("📥 Download Excel Template", 
                         export_to_excel(template_df, include_photos=False),
                         file_name="import_template.xlsx")
    
    uploaded_file = st.file_uploader("Choose file to import", type=['csv', 'xlsx'])
    
    if uploaded_file and target_branch != "Select Branch":
        st.subheader("Preview of data to import")
        
        if uploaded_file.name.endswith('.csv'):
            df_preview = pd.read_csv(uploaded_file)
        else:
            df_preview = pd.read_excel(uploaded_file)
        
        st.dataframe(df_preview.head(10), use_container_width=True)
        st.write(f"Total records in file: {len(df_preview)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Import", type="primary", use_container_width=True):
                with st.spinner("Importing data..."):
                    if uploaded_file.name.endswith('.csv'):
                        success_count, errors = import_from_csv(uploaded_file, target_branch, st.session_state.user_id)
                    else:
                        success_count, errors = import_from_excel(uploaded_file, target_branch, st.session_state.user_id)
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully imported {success_count} records to {target_branch} branch!")
                        log_audit(st.session_state.user_id, st.session_state.username, 'IMPORT_DATA', 
                                 'members', success_count, f"Imported {success_count} members to {target_branch}")
                    
                    if errors:
                        st.warning(f"⚠️ {len(errors)} errors occurred:")
                        for error in errors[:10]:  # Show first 10 errors
                            st.write(f"- {error}")
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.rerun()
    
    elif uploaded_file and target_branch == "Select Branch":
        st.error("Please select a branch to import data into")
    else:
        if uploaded_file:
            st.warning("Please select a branch to import to")

# ==================== EMAIL SETTINGS UI ====================

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
        - For custom domains: Check with your hosting provider for SMTP settings
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save Configuration", use_container_width=True):
                if sender_email and sender_password:
                    save_email_settings(smtp_server, smtp_port, sender_email, sender_password, use_tls, 
                                      st.session_state.user_id)
                    st.success("Email settings saved successfully!")
                else:
                    st.error("Please provide sender email and password")
        
        with col2:
            test_email_input = st.text_input("Test Email Address", key="test_email_input")
            if st.form_submit_button("Send Test Email", use_container_width=True) and test_email_input:
                success, message = send_email(test_email_input, "YoKA System - Test Email",
                                             "<h3>Test Email</h3><p>Your email configuration is working correctly!</p>")
                if success:
                    st.success("Test email sent successfully!")
                else:
                    st.error(f"Failed to send test email: {message}")

# ==================== THEME CUSTOMIZER UI ====================

def theme_customizer_ui():
    """Advanced theme customization with live preview"""
    if st.session_state.user_role != 'super_admin':
        st.error("Only Super Admin can customize themes")
        return
    
    st.title("🎨 Theme Customizer")
    
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()}
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎨 Color Scheme")
        primary_color = st.color_picker("Primary Color", settings.get('primary_color', '#1E3A8A'))
        secondary_color = st.color_picker("Secondary Color", settings.get('secondary_color', '#3B82F6'))
        accent_color = st.color_picker("Accent Color", settings.get('accent_color', '#F59E0B'))
        background_color = st.color_picker("Background Color", settings.get('background_color', '#FFFFFF'))
        sidebar_color = st.color_picker("Sidebar Color", settings.get('sidebar_color', '#1E3A8A'))
        
        st.subheader("📝 Typography")
        font_family = st.selectbox("Font Family", 
                                   ["System Default", "Poppins", "Roboto", "Arial", "Helvetica"],
                                   index=["System Default", "Poppins", "Roboto", "Arial", "Helvetica"].index(settings.get('font_family', 'System Default')))
        font_size = st.select_slider("Base Font Size", 
                                     options=["12px", "14px", "16px", "18px", "20px"],
                                     value=settings.get('font_size', '16px'))
        
        st.subheader("📐 Layout")
        card_border_radius = st.slider("Card Border Radius", 0, 20, int(settings.get('card_border_radius', 10)))
        
        st.subheader("🏷️ Branding")
        system_name = st.text_input("System Name", settings.get('system_name', 'Kumasi District YoKA Registration System'))
        logo_url = st.text_input("Logo URL (optional)", settings.get('logo_url', ''))
        favicon = st.text_input("Favicon Emoji", settings.get('favicon', '⛪'))
        footer_text = st.text_input("Footer Text", settings.get('footer_text', '© 2024 Kumasi District YoKA. All Rights Reserved.'))
        
        registration_open = st.checkbox("Registration Open", settings.get('registration_open', 'true') == 'true')
        
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
            update_system_setting('logo_url', logo_url, st.session_state.user_id)
            update_system_setting('favicon', favicon, st.session_state.user_id)
            update_system_setting('footer_text', footer_text, st.session_state.user_id)
            update_system_setting('registration_open', str(registration_open).lower(), st.session_state.user_id)
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
            <div style="margin-top: 10px; font-family: '{font_family}', sans-serif; font-size: {font_size};">
                <p>Font preview: The quick brown fox jumps over the lazy dog.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📊 Component Previews")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="success-box" style="border-left-color: {primary_color};">
                <strong>Success Message Preview</strong><br>
                This is how success messages will appear
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div class="info-box" style="border-left-color: {secondary_color};">
                <strong>Info Message Preview</strong><br>
                This is how info messages will appear
            </div>
            """, unsafe_allow_html=True)

# ==================== REGISTRATION FORM UI ====================

def registration_form_ui():
    """Registration form for branch executives to add members"""
    st.title("⛪ YoKA Registration Form")
    
    with st.form("registration_form"):
        # Personal Information
        st.header("📋 Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            official_name = st.text_input("Full Name *")
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
            date_of_birth = st.date_input("Date of Birth", min_value=datetime(1950,1,1), max_value=datetime.now())
            residence = st.text_input("Residential Address *")
            email = st.text_input("Email Address")
        
        with col2:
            age = st.number_input("Age *", min_value=13, max_value=30, value=18)
            active_phone = st.text_input("Active Phone Number(s) *")
            emergency_contact_name = st.text_input("Emergency Contact Name")
            emergency_contact_phone = st.text_input("Emergency Contact Phone")
            medical_conditions = st.text_area("Medical Conditions/Allergies (if any)")
        
        # School Information
        st.header("🎓 School Information")
        col3, col4 = st.columns(2)
        with col3:
            school_level = st.selectbox("Education Level *", ["SHS", "Tertiary", "Graduate", "Other"])
            school_name = st.text_input("School Name *")
            school_class = st.text_input("Current Class/Level *")
        
        with col4:
            school_house = st.text_input("House (if applicable)")
            residence_status = st.selectbox("Residence Status *", ["Day Student", "Boarder"])
            residence_name = st.text_input("Residence/Hostel Name (if boarder)")
        
        # Talents and Interests
        st.header("🎭 Talents & Interests")
        col5, col6 = st.columns(2)
        with col5:
            talents = st.multiselect("Talents/Skills", 
                                    ["Singing", "Dancing", "Drama", "Instrumental", "Public Speaking", 
                                     "Sports", "Teaching", "Technical", "Writing", "Graphic Design", "Other"])
        with col6:
            interests = st.multiselect("Areas of Interest", 
                                      ["Evangelism", "Teaching", "Technical Support", "Event Planning",
                                       "Counseling", "Media", "Worship Team", "Ushering", "Protocol", "Other"])
        
        # Church Information
        st.header("⛪ Church Information")
        
        if st.session_state.user_role == 'branch_executive':
            church_branch = st.text_input("Church Branch", value=st.session_state.branch_name, disabled=True)
        else:
            branches_df = get_all_branches()
            branch_options = branches_df['branch_name'].tolist()
            church_branch = st.selectbox("Church Branch *", branch_options)
        
        yoka_hall = st.selectbox("YoKA Hall *", ["Hall A", "Hall B", "Hall C", "Hall D", "Hall E", "Other"])
        if yoka_hall == "Other":
            yoka_hall = st.text_input("Specify Hall")
        
        youth_camps = st.slider("Number of YoKA Youth Camps Attended *", min_value=0, max_value=20, value=0)
        
        # Church Position/Service Information
        st.subheader("🙏 Church Leadership & Service")
        has_church_position = st.checkbox("Currently hold or formerly held a church position?")
        
        if has_church_position:
            col_pos1, col_pos2 = st.columns(2)
            with col_pos1:
                church_position_type = st.selectbox("Position Type", ["Sevent Member", "YoKA Executive", "Other"])
                if church_position_type == "Other":
                    church_position_name = st.text_input("Please specify position name")
                else:
                    church_position_name = church_position_type
            with col_pos2:
                church_position_duration = st.text_input("How long have you been/had been in this position? (e.g., 2 years, 6 months)", placeholder="e.g., 2 years")
        else:
            church_position_type = ""
            church_position_name = ""
            church_position_duration = ""
        
        # Work Information
        st.header("💼 Work Information")
        col_work1, col_work2 = st.columns(2)
        with col_work1:
            work_status = st.selectbox("Work Status", ["None", "Apprenticeship", "Internship", "Permanent Staff", "Part-time"])
        with col_work2:
            if work_status != "None":
                work_type = st.selectbox("Type of Work", ["Formal Employment", "Self-Employed", "Freelance", "Volunteer", "Other"])
            else:
                work_type = ""
        
        if work_status != "None":
            col_work3, col_work4 = st.columns(2)
            with col_work3:
                work_name = st.text_input("Name of Workplace/Organization")
                work_position = st.text_input("Your Position/Title")
            with col_work4:
                work_location = st.text_input("Work Location (City/Country)")
                work_experience_years = st.number_input("Number of Years of Experience", min_value=0, max_value=30, value=0)
        else:
            work_name = work_position = work_location = ""
            work_experience_years = 0
        
        # Diaspora Information - Enhanced
        st.header("🌍 Diaspora Information")
        is_diaspora = st.checkbox("Are you currently in the diaspora (outside Ghana)?")
        
        if is_diaspora:
            col_dias1, col_dias2 = st.columns(2)
            with col_dias1:
                diaspora_country = st.text_input("Which country are you in? *")
                diaspora_status = st.selectbox("Status in Diaspora", ["Working", "Studying", "Both"])
            
            with col_dias2:
                if diaspora_status in ["Working", "Both"]:
                    diaspora_job = st.text_input("Current Job/Profession")
                else:
                    diaspora_job = ""
                
                if diaspora_status in ["Studying", "Both"]:
                    diaspora_school = st.text_input("School/Institution")
                    diaspora_education_level = st.selectbox("Level of Education", 
                                                           ["Undergraduate", "Graduate", "Masters", "PhD", "Other"])
                else:
                    diaspora_school = ""
                    diaspora_education_level = ""
        else:
            diaspora_country = diaspora_status = diaspora_job = diaspora_school = diaspora_education_level = ""
        
        # Parent/Guardian Information - SEPARATED SECTIONS
        st.header("👨‍👩‍👧 Parent/Guardian Information")
        st.info("Please provide information for at least one parent or guardian")
        
        # Mother's Information Section
        st.subheader("👩 Mother's Information")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mother_name = st.text_input("Mother's Full Name")
            mother_phone = st.text_input("Mother's Phone Number")
        with col_m2:
            mother_occupation = st.text_input("Mother's Occupation")
        
        st.divider()
        
        # Father's Information Section
        st.subheader("👨 Father's Information")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            father_name = st.text_input("Father's Full Name")
            father_phone = st.text_input("Father's Phone Number")
        with col_f2:
            father_occupation = st.text_input("Father's Occupation")
        
        st.divider()
        
        # Guardian's Information Section (Optional, shown if parents not fully provided)
        st.subheader("👤 Guardian Information (if applicable)")
        st.caption("Provide guardian information if the member is not living with parents or if parents are unavailable")
        
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            guardian_name = st.text_input("Guardian's Full Name")
        with col_g2:
            guardian_phone = st.text_input("Guardian's Phone Number")
        with col_g3:
            guardian_relationship = st.text_input("Relationship to Member")
        guardian_occupation = st.text_input("Guardian's Occupation")
        
        submitted = st.form_submit_button("Register Member", use_container_width=True)
        
        if submitted:
            # Check required fields
            required_fields = [official_name, residence, active_phone, age, school_name, school_class, 
                             residence_status, church_branch, yoka_hall, gender]
            
            # Check if at least one parent or guardian is provided
            has_parent_guardian = (mother_name and mother_phone) or (father_name and father_phone) or (guardian_name and guardian_phone)
            
            if all(required_fields) and school_level and has_parent_guardian:
                data = {
                    'official_name': official_name,
                    'date_of_birth': date_of_birth.strftime("%Y-%m-%d") if date_of_birth else "",
                    'age': age,
                    'residence': residence,
                    'active_phone': active_phone,
                    'email': email,
                    'school_name': school_name,
                    'school_level': school_level,
                    'school_class': school_class,
                    'school_house': school_house,
                    'residence_status': residence_status,
                    'residence_name': residence_name if residence_status == "Boarder" else "",
                    'church_branch': church_branch,
                    'yoka_hall': yoka_hall,
                    'youth_camps_attended': youth_camps,
                    'has_church_position': has_church_position,
                    'church_position_type': church_position_type,
                    'church_position_name': church_position_name,
                    'church_position_duration': church_position_duration,
                    'work_status': work_status if work_status != "None" else "",
                    'work_type': work_type,
                    'work_name': work_name,
                    'work_position': work_position,
                    'work_location': work_location,
                    'work_experience_years': work_experience_years,
                    'is_diaspora': is_diaspora,
                    'diaspora_country': diaspora_country,
                    'diaspora_status': diaspora_status,
                    'diaspora_job': diaspora_job,
                    'diaspora_school': diaspora_school,
                    'diaspora_education_level': diaspora_education_level,
                    'mother_name': mother_name,
                    'mother_phone': mother_phone,
                    'mother_occupation': mother_occupation,
                    'father_name': father_name,
                    'father_phone': father_phone,
                    'father_occupation': father_occupation,
                    'guardian_name': guardian_name,
                    'guardian_phone': guardian_phone,
                    'guardian_relationship': guardian_relationship,
                    'guardian_occupation': guardian_occupation,
                    'gender': gender,
                    'emergency_contact_name': emergency_contact_name,
                    'emergency_contact_phone': emergency_contact_phone,
                    'medical_conditions': medical_conditions,
                    'talents': ', '.join(talents) if talents else '',
                    'interests': ', '.join(interests) if interests else ''
                }
                
                save_member(data, created_by=st.session_state.user_id)
                st.success("Member registered successfully!")
                st.balloons()
                st.rerun()
            else:
                missing_fields = []
                if not official_name: missing_fields.append("Full Name")
                if not residence: missing_fields.append("Residential Address")
                if not active_phone: missing_fields.append("Phone Number")
                if not school_name: missing_fields.append("School Name")
                if not school_class: missing_fields.append("Class/Level")
                if not church_branch: missing_fields.append("Church Branch")
                if not yoka_hall: missing_fields.append("YoKA Hall")
                if not gender: missing_fields.append("Gender")
                if not has_parent_guardian: missing_fields.append("At least one Parent/Guardian (Mother, Father, or Guardian)")
                
                if missing_fields:
                    st.error(f"Please fill in the following required fields: {', '.join(missing_fields)}")
                else:
                    st.error("Please fill in all required fields (*) and provide at least one parent/guardian contact")

# ==================== VIEW MEMBERS UI ====================

def view_members_ui():
    """View members with role-based access"""
    st.title("📋 Registered Members")
    
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"Showing members from {st.session_state.branch_name} branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
        selected_branch = st.selectbox("Filter by Branch", branch_options)
        if selected_branch != "All Branches":
            members_df = members_df[members_df['church_branch'] == selected_branch]
    
    if not members_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Members", len(members_df))
        with col2:
            st.metric("Average Age", round(members_df['age'].mean(), 1))
        with col3:
            st.metric("Youth Camps (Avg)", round(members_df['youth_camps_attended'].mean(), 1))
        with col4:
            st.metric("Verified", members_df['is_verified'].sum())
        
        search_term = st.text_input("🔍 Search by name or phone")
        if search_term:
            members_df = members_df[members_df['official_name'].str.contains(search_term, case=False, na=False) | 
                                   members_df['active_phone'].str.contains(search_term, case=False, na=False)]
        
        display_cols = ['id', 'official_name', 'age', 'gender', 'active_phone', 'church_branch', 'yoka_hall', 'submission_date', 'is_verified']
        available_cols = [col for col in display_cols if col in members_df.columns]
        st.dataframe(members_df[available_cols], use_container_width=True)
        
        if len(members_df) > 0:
            selected_id = st.selectbox("Select Member to View Details", members_df['id'].tolist())
            if selected_id:
                member = get_member_by_id(selected_id, st.session_state.user_role, st.session_state.user_branch_id)
                if member:
                    with st.expander("Member Details", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Name:** {member[1]}")
                            st.write(f"**Gender:** {member[36] if len(member) > 36 else 'N/A'}")
                            st.write(f"**Age:** {member[3]}")
                            st.write(f"**Phone:** {member[5]}")
                            st.write(f"**Email:** {member[6]}")
                            st.write(f"**Residence:** {member[4]}")
                        with col2:
                            st.write(f"**Branch:** {member[16]}")
                            st.write(f"**Hall:** {member[18]}")
                            st.write(f"**School:** {member[12]}")
                            st.write(f"**Class:** {member[14]}")
                            st.write(f"**Registered:** {member[29]}")
                        
                        # Church Position Section
                        if len(member) > 20 and member[20]:  # has_church_position
                            st.subheader("⛪ Church Position")
                            st.write(f"**Position Type:** {member[21] if len(member) > 21 else 'N/A'}")
                            st.write(f"**Position Name:** {member[22] if len(member) > 22 else 'N/A'}")
                            st.write(f"**Duration:** {member[23] if len(member) > 23 else 'N/A'}")
                        
                        # Work Information Section
                        if len(member) > 24 and member[24] and member[24] != "":  # work_status
                            st.subheader("💼 Work Information")
                            st.write(f"**Status:** {member[24]}")
                            st.write(f"**Type:** {member[25] if len(member) > 25 else 'N/A'}")
                            st.write(f"**Workplace:** {member[26] if len(member) > 26 else 'N/A'}")
                            st.write(f"**Position:** {member[27] if len(member) > 27 else 'N/A'}")
                            st.write(f"**Location:** {member[28] if len(member) > 28 else 'N/A'}")
                            st.write(f"**Years of Experience:** {member[29] if len(member) > 29 else 'N/A'}")
                        
                        # Diaspora Information
                        if len(member) > 31 and member[31]:  # is_diaspora
                            st.subheader("🌍 Diaspora Information")
                            st.write(f"**Country:** {member[32] if len(member) > 32 else 'N/A'}")
                            st.write(f"**Status:** {member[33] if len(member) > 33 else 'N/A'}")
                            if member[33] in ["Working", "Both"]:
                                st.write(f"**Job:** {member[34] if len(member) > 34 else 'N/A'}")
                            if member[33] in ["Studying", "Both"]:
                                st.write(f"**School:** {member[35] if len(member) > 35 else 'N/A'}")
                                st.write(f"**Education Level:** {member[36] if len(member) > 36 else 'N/A'}")
                        
                        # Parent/Guardian Information - Adjust indices based on new fields
                        st.subheader("👩‍👨‍👧 Parent/Guardian Information")
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            st.write("**Mother:**")
                            st.write(f"Name: {member[37] if len(member) > 37 else 'N/A'}")
                            st.write(f"Phone: {member[38] if len(member) > 38 else 'N/A'}")
                            st.write(f"Occupation: {member[39] if len(member) > 39 else 'N/A'}")
                        with col_p2:
                            st.write("**Father:**")
                            st.write(f"Name: {member[40] if len(member) > 40 else 'N/A'}")
                            st.write(f"Phone: {member[41] if len(member) > 41 else 'N/A'}")
                            st.write(f"Occupation: {member[42] if len(member) > 42 else 'N/A'}")
                        with col_p3:
                            st.write("**Guardian:**")
                            st.write(f"Name: {member[43] if len(member) > 43 else 'N/A'}")
                            st.write(f"Phone: {member[44] if len(member) > 44 else 'N/A'}")
                            st.write(f"Relationship: {member[45] if len(member) > 45 else 'N/A'}")
                            st.write(f"Occupation: {member[46] if len(member) > 46 else 'N/A'}")
                        
                        # Emergency and Medical
                        st.subheader("🚨 Emergency & Medical")
                        st.write(f"**Emergency Contact:** {member[48] if len(member) > 48 else 'N/A'} - {member[49] if len(member) > 49 else 'N/A'}")
                        st.write(f"**Medical Conditions:** {member[50] if len(member) > 50 else 'None'}")
                        
                        # Talents and Interests
                        st.subheader("🎭 Talents & Interests")
                        st.write(f"**Talents:** {member[51] if len(member) > 51 else 'None'}")
                        st.write(f"**Interests:** {member[52] if len(member) > 52 else 'None'}")
                        
                        if len(member) > 53 and member[53]:  # is_verified index may vary
                            st.success("✅ Verified Member")
                        else:
                            st.warning("⏳ Pending Verification")
                        
                        if st.session_state.user_role in ['super_admin', 'admin'] and (len(member) > 53 and not member[53]):
                            if st.button("Verify Member"):
                                verify_member(selected_id, st.session_state.user_id)
                                st.success("Member verified!")
                                st.rerun()
                        
                        if st.session_state.user_role == 'super_admin':
                            if st.button("Delete Member", type="secondary"):
                                success, message = delete_member(selected_id, st.session_state.user_id, 
                                                                st.session_state.user_role, st.session_state.user_branch_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
    else:
        st.info("No members registered yet")

# ==================== BRANCH MANAGEMENT UI ====================

def branch_management_ui():
    """UI for super admin and admin to manage branches"""
    st.header("🏢 Branch Management")
    
    tab1, tab2 = st.tabs(["All Branches", "Create New Branch"])
    
    with tab1:
        branches_df = get_all_branches(include_inactive=True)
        if not branches_df.empty:
            st.dataframe(branches_df[['id', 'branch_name', 'branch_code', 'location', 'contact_person', 'contact_phone', 'is_active']], 
                        use_container_width=True)
            
            selected_branch = st.selectbox("Select Branch to Edit", branches_df['id'].tolist(), 
                                          format_func=lambda x: branches_df[branches_df['id']==x]['branch_name'].iloc[0])
            if selected_branch:
                with st.expander("Edit Branch"):
                    branch_data = get_branch_by_id(selected_branch)
                    if branch_data:
                        new_branch_name = st.text_input("Branch Name", branch_data[1])
                        new_branch_code = st.text_input("Branch Code", branch_data[2])
                        new_location = st.text_input("Location", branch_data[3])
                        new_contact_person = st.text_input("Contact Person", branch_data[4])
                        new_contact_phone = st.text_input("Contact Phone", branch_data[5])
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update Branch"):
                                update_branch(selected_branch, new_branch_name, new_branch_code, new_location, 
                                            new_contact_person, new_contact_phone, st.session_state.user_id)
                                st.success("Branch updated successfully!")
                                st.rerun()
                        with col2:
                            if st.button("Deactivate Branch", type="secondary"):
                                delete_branch(selected_branch, st.session_state.user_id)
                                st.warning("Branch deactivated!")
                                st.rerun()
        else:
            st.info("No branches found")
    
    with tab2:
        if st.session_state.user_role in ['super_admin', 'admin']:
            with st.form("create_branch_form"):
                col1, col2 = st.columns(2)
                with col1:
                    branch_name = st.text_input("Branch Name *")
                    branch_code = st.text_input("Branch Code *")
                    location = st.text_input("Location *")
                with col2:
                    contact_person = st.text_input("Contact Person *")
                    contact_phone = st.text_input("Contact Phone *")
                
                if st.form_submit_button("Create Branch"):
                    if all([branch_name, branch_code, location, contact_person, contact_phone]):
                        success, result = create_branch(branch_name, branch_code, location , contact_person, 
                                                       contact_phone, st.session_state.user_id)
                        if success:
                            st.success(f"Branch {branch_name} created successfully!")
                            st.rerun()
                        else:
                            st.error(result)
                    else:
                        st.error("Please fill all required fields")
        else:
            st.error("You don't have permission to create branches")

# ==================== USER MANAGEMENT UI ====================

def user_management_ui():
    """UI for super admin to manage users"""
    st.header("👥 User Management")
    
    tab1, tab2 = st.tabs(["All Users", "Create New User"])
    
    with tab1:
        users_df = get_all_users()
        if not users_df.empty:
            st.dataframe(users_df[['id', 'username', 'full_name', 'email', 'role', 'assigned_branch', 'is_active']], 
                        use_container_width=True)
            
            selected_user = st.selectbox("Select User to Edit", users_df['id'].tolist(),
                                        format_func=lambda x: f"{x} - {users_df[users_df['id']==x]['full_name'].iloc[0]}")
            if selected_user:
                with st.expander("Edit User"):
                    user_data = get_user_by_id(selected_user)
                    if user_data:
                        new_full_name = st.text_input("Full Name", user_data[3])
                        new_email = st.text_input("Email", user_data[4])
                        new_phone = st.text_input("Phone", user_data[5])
                        new_role = st.selectbox("Role", ['super_admin', 'admin', 'branch_executive'], 
                                               index=['super_admin', 'admin', 'branch_executive'].index(user_data[6]))
                        
                        branches_df = get_all_branches()
                        branch_options = {row['id']: row['branch_name'] for _, row in branches_df.iterrows()}
                        new_branch = st.selectbox("Assigned Branch", list(branch_options.keys()),
                                                 format_func=lambda x: branch_options.get(x, 'None'),
                                                 index=list(branch_options.keys()).index(user_data[7]) if user_data[7] in branch_options.keys() else 0)
                        
                        is_active = st.checkbox("Active", user_data[8] == 1)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update User"):
                                update_user(selected_user, new_full_name, new_email, new_phone, new_role, 
                                          new_branch, is_active, st.session_state.user_id)
                                st.success("User updated successfully!")
                                st.rerun()
                        with col2:
                            new_password = st.text_input("New Password (leave blank to keep current)", type="password")
                            if st.button("Reset Password") and new_password:
                                reset_user_password(selected_user, new_password, st.session_state.user_id)
                                st.success("Password reset and email sent successfully!")
        else:
            st.info("No users found")
    
    with tab2:
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username *")
                full_name = st.text_input("Full Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone *")
            with col2:
                password = st.text_input("Password *", type="password")
                role = st.selectbox("Role *", ['branch_executive', 'admin'])
                
                branches_df = get_all_branches()
                branch_options = {row['id']: row['branch_name'] for _, row in branches_df.iterrows()}
                assigned_branch = st.selectbox("Assigned Branch *", list(branch_options.keys()), 
                                              format_func=lambda x: branch_options[x])
            
            if st.form_submit_button("Create User"):
                if all([username, full_name, email, phone, password, assigned_branch]):
                    success, result = create_user(username, password, full_name, email, phone, role, 
                                                 assigned_branch, st.session_state.user_id)
                    if success:
                        st.success(f"User {username} created successfully! Credentials sent to their email.")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Please fill all required fields")

# ==================== AUDIT LOG UI ====================

def audit_log_ui():
    """View audit logs (super admin only)"""
    if st.session_state.user_role != 'super_admin':
        st.error("Only Super Admin can access audit logs")
        return
    
    st.title("📜 Audit Log")
    
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 1000", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df[['timestamp', 'username', 'action', 'entity_type', 'entity_id', 'details']], 
                    use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button("Download Audit Log", csv, 
                         f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    else:
        st.info("No audit logs found")

# ==================== MAIN APPLICATION ====================

def main():
    # Initialize database
    init_rbac_database()
    
    # Apply custom styling
    apply_custom_styling()
    
    # Session state initialization
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_branch_id' not in st.session_state:
        st.session_state.user_branch_id = None
    if 'branch_name' not in st.session_state:
        st.session_state.branch_name = None
    
    # Get system settings
    settings_df = get_system_settings()
    settings = {row['setting_key']: row['setting_value'] for _, row in settings_df.iterrows()}
    system_name = settings.get('system_name', 'Kumasi District YoKA Registration System')
    favicon = settings.get('favicon', '⛪')
    
    # Login Page
    if not st.session_state.logged_in:
        st.title(f"{favicon} {system_name}")
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("### Welcome")
            st.markdown("Please login to access the system")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    user_info = check_login(username, password)
                    if user_info:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_info['id']
                        st.session_state.username = user_info['username']
                        st.session_state.user_role = user_info['role']
                        st.session_state.user_branch_id = user_info.get('assigned_branch_id')
                        st.session_state.branch_name = user_info.get('branch_name')
                        
                        st.success(f"Welcome {user_info['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.info("Contact system administrator for credentials")
    
    # Main Application after login
    else:
        st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
        st.sidebar.write(f"**Role:** {st.session_state.user_role.replace('_', ' ').title()}")
        if st.session_state.branch_name:
            st.sidebar.write(f"**Branch:** {st.session_state.branch_name}")
        st.sidebar.divider()
        
        st.sidebar.subheader("Navigation")
        menu_items = ["Registration Form", "View Members", "Analytics Dashboard", "Export Data"]
        
        if st.session_state.user_role in ['super_admin', 'admin']:
            menu_items.extend(["Import Data", "Branch Management"])
        
        if st.session_state.user_role == 'super_admin':
            menu_items.extend(["User Management", "Email Settings", "Theme Customizer", "Audit Log"])
        
        selected_page = st.sidebar.radio("Go to", menu_items)
        
        st.sidebar.divider()
        if st.sidebar.button("Logout", use_container_width=True):
            log_audit(st.session_state.user_id, st.session_state.username, 'LOGOUT', 'user', 
                     st.session_state.user_id, "User logged out")
            for key in ['logged_in', 'user_id', 'username', 'user_role', 'user_branch_id', 'branch_name']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # Page content
        if selected_page == "Registration Form":
            registration_form_ui()
        elif selected_page == "View Members":
            view_members_ui()
        elif selected_page == "Analytics Dashboard":
            analytics_dashboard_ui()
        elif selected_page == "Export Data":
            advanced_export_ui()
        elif selected_page == "Import Data":
            import_data_ui()
        elif selected_page == "Branch Management":
            branch_management_ui()
        elif selected_page == "User Management":
            user_management_ui()
        elif selected_page == "Email Settings":
            email_settings_ui()
        elif selected_page == "Theme Customizer":
            theme_customizer_ui()
        elif selected_page == "Audit Log":
            audit_log_ui()
        
        # Footer
        footer_text = settings.get('footer_text', '© 2024 Kumasi District YoKA. All Rights Reserved.')
        st.sidebar.divider()
        st.sidebar.caption(footer_text)

if __name__ == "__main__":
    main()