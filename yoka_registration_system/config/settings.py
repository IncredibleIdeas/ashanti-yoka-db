"""Configuration settings for the application"""
import os
from datetime import datetime

# Database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kumasi_yoka_registration.db')

# Date formats
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_ONLY_FORMAT = "%Y-%m-%d"

# Roles
ROLES = {
    'SUPER_ADMIN': 'super_admin',
    'ADMIN': 'admin',
    'BRANCH_EXECUTIVE': 'branch_executive'
}

# School levels
SCHOOL_LEVELS = ['SHS', 'Tertiary', 'Graduate', 'Other']

# Residence status
RESIDENCE_STATUS = ['Day Student', 'Boarder']

# YoKA Halls
YOKA_HALLS = ['Hall A', 'Hall B', 'Hall C', 'Hall D', 'Hall E', 'Other']

# Work status
WORK_STATUS = ['None', 'Apprenticeship', 'Internship', 'Permanent Staff', 'Part-time']

# Gender options
GENDER_OPTIONS = ['Male', 'Female', 'Other']

# Diaspora status
DIASPORA_STATUS = ['Working', 'Studying', 'Both']