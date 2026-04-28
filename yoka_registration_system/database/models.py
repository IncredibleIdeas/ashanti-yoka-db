"""Database schema and initialization"""
import sqlite3
from datetime import datetime
from database.connection import get_connection
from config.settings import DATABASE_PATH

def init_rbac_database():
    """Initialize database with complete RBAC schema"""
    conn = get_connection()
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
    
    # Create members table with enhanced fields
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
                  has_church_position BOOLEAN DEFAULT 0,
                  church_position_status TEXT,
                  church_position_type TEXT,
                  church_position_name TEXT,
                  church_position_duration TEXT,
                  work_status TEXT,
                  work_type TEXT,
                  work_name TEXT,
                  work_position TEXT,
                  work_location TEXT,
                  work_experience_years INTEGER,
                  is_diaspora BOOLEAN DEFAULT 0,
                  diaspora_country TEXT,
                  diaspora_status TEXT,
                  diaspora_job TEXT,
                  diaspora_school TEXT,
                  diaspora_education_level TEXT,
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
    
    # Create system_settings table
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
    
    # Insert default super admin
    from auth.authentication import hash_password
    c.execute("SELECT * FROM users WHERE username='super_admin'")
    if not c.fetchone():
        hashed_password = hash_password('SuperAdmin@123')
        c.execute("INSERT INTO users (username, password, full_name, email, phone, role, created_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ('super_admin', hashed_password, 'Super Administrator', 'superadmin@yoka.org', '0244000000', 'super_admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Insert default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_password = hash_password('Admin@123')
        c.execute("INSERT INTO users (username, password, full_name, email, phone, role, assigned_branch_id, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('admin', hashed_password, 'District Administrator', 'admin@yoka.org', '0244000006', 'admin', 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
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