"""Database connection management"""
import sqlite3
import os
from config.settings import DATABASE_PATH

def get_connection():
    """Get database connection"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema"""
    from database.models import init_rbac_database
    init_rbac_database()