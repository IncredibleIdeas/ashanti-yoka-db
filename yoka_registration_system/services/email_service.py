"""Email services for notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st
from database.connection import get_connection

def get_email_settings():
    """Get email configuration settings"""
    conn = get_connection()
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
            'use_tls': bool(settings[5]) if settings[5] is not None else True
        }
    return None

def save_email_settings(smtp_server, smtp_port, sender_email, sender_password, use_tls, updated_by):
    """Save email configuration"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM email_settings")
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
        conn = get_connection()
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
    <head><style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ padding: 20px; background-color: #f4f4f4; }}
        .header {{ background-color: #1E3A8A; color: white; padding: 10px; text-align: center; }}
        .content {{ background-color: white; padding: 20px; margin: 20px 0; }}
        .credentials {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; }}
    </style></head>
    <body>
        <div class="container">
            <div class="header"><h2>Kumasi District YoKA Registration System</h2></div>
            <div class="content">
                <h3>Dear {full_name},</h3>
                <p>Your account has been created with the following credentials:</p>
                <div class="credentials">
                    <p><strong>Username:</strong> {username}</p>
                    <p><strong>Password:</strong> {password}</p>
                    <p><strong>Role:</strong> {role.replace('_', ' ').title()}</p>
                </div>
                <p><strong>Important:</strong> Please change your password after your first login.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, body)

def send_password_reset_email(email, full_name, username, new_password):
    """Send password reset notification"""
    subject = "YoKA System - Password Reset Notification"
    body = f"""
    <html>
    <body>
        <h3>Password Reset</h3>
        <p>Dear {full_name},</p>
        <p>Your password has been reset. Your new login credentials are:</p>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>New Password:</strong> {new_password}</p>
        <p>Please change your password after logging in.</p>
    </body>
    </html>
    """
    return send_email(email, subject, body)