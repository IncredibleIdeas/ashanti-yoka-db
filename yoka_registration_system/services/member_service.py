"""Member management services"""
import pandas as pd
from datetime import datetime
from database.connection import get_connection
from services.audit_service import log_audit
import streamlit as st

def get_table_columns():
    """Get actual column names from members table"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(members)")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    return columns

def save_member(data, profile_picture=None, created_by=None):
    """Save member with dynamic column matching"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get branch ID from branch name
    c.execute("SELECT id FROM branches WHERE branch_name = ?", (data['church_branch'],))
    branch_result = c.fetchone()
    branch_id = branch_result[0] if branch_result else 1
    
    # Get actual table columns
    table_columns = get_table_columns()
    
    # Prepare data dictionary with all possible fields
    full_data = {
        'official_name': data['official_name'],
        'date_of_birth': data['date_of_birth'],
        'age': data['age'],
        'residence': data['residence'],
        'active_phone': data['active_phone'],
        'email': data['email'],
        'profile_picture': profile_picture,
        'school_name': data['school_name'],
        'school_level': data['school_level'],
        'school_class': data['school_class'],
        'school_house': data['school_house'],
        'residence_status': data['residence_status'],
        'residence_name': data['residence_name'],
        'church_branch': data['church_branch'],
        'branch_id': branch_id,
        'yoka_hall': data['yoka_hall'],
        'youth_camps_attended': data['youth_camps_attended'],
        'has_church_position': int(data['has_church_position']),
        'church_position_status': data['church_position_status'],
        'church_position_type': data['church_position_type'],
        'church_position_name': data['church_position_name'],
        'church_position_duration': data['church_position_duration'],
        'work_status': data['work_status'],
        'work_type': data['work_type'],
        'work_name': data['work_name'],
        'work_position': data['work_position'],
        'work_location': data['work_location'],
        'work_experience_years': data['work_experience_years'],
        'is_diaspora': int(data['is_diaspora']),
        'diaspora_country': data['diaspora_country'],
        'diaspora_status': data['diaspora_status'],
        'diaspora_job': data['diaspora_job'],
        'diaspora_school': data['diaspora_school'],
        'diaspora_education_level': data['diaspora_education_level'],
        'mother_name': data['mother_name'],
        'mother_phone': data['mother_phone'],
        'mother_occupation': data['mother_occupation'],
        'father_name': data['father_name'],
        'father_phone': data['father_phone'],
        'father_occupation': data['father_occupation'],
        'guardian_name': data['guardian_name'],
        'guardian_phone': data['guardian_phone'],
        'guardian_relationship': data['guardian_relationship'],
        'guardian_occupation': data['guardian_occupation'],
        'submission_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'created_by': created_by,
        'last_modified_by': created_by,
        'last_modified_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'is_verified': 0,
        'verified_by': None,
        'verified_date': None,
        'gender': data.get('gender', ''),
        'emergency_contact_name': data.get('emergency_contact_name', ''),
        'emergency_contact_phone': data.get('emergency_contact_phone', ''),
        'medical_conditions': data.get('medical_conditions', ''),
        'talents': data.get('talents', ''),
        'interests': data.get('interests', '')
    }
    
    # Filter to only columns that exist in the table
    insert_columns = [col for col in full_data.keys() if col in table_columns]
    insert_values = [full_data[col] for col in insert_columns]
    
    # Build and execute INSERT statement
    placeholders = ', '.join(['?' for _ in insert_columns])
    columns_str = ', '.join(insert_columns)
    
    query = f"INSERT INTO members ({columns_str}) VALUES ({placeholders})"
    
    try:
        c.execute(query, insert_values)
        member_id = c.lastrowid
        conn.commit()
        log_audit(created_by, st.session_state.get('username', 'system'), 'CREATE_MEMBER', 'member', member_id, f"Created member: {data['official_name']}")
        conn.close()
        return member_id
    except Exception as e:
        conn.close()
        raise e

def get_members_by_role(user_role, user_branch_id=None, user_id=None):
    """Get members based on user role and permissions"""
    conn = get_connection()
    
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
    conn = get_connection()
    c = conn.cursor()
    
    if user_role == 'branch_executive':
        c.execute("SELECT * FROM members WHERE id = ? AND branch_id = ?", (member_id, user_branch_id))
    else:
        c.execute("SELECT * FROM members WHERE id = ?", (member_id,))
    
    member = c.fetchone()
    conn.close()
    return member

def update_member(member_id, data, updated_by):
    """Update member information dynamically"""
    conn = get_connection()
    c = conn.cursor()
    
    # Get branch ID from branch name
    c.execute("SELECT id FROM branches WHERE branch_name = ?", (data['church_branch'],))
    branch_result = c.fetchone()
    branch_id = branch_result[0] if branch_result else 1
    
    # Get actual table columns
    table_columns = get_table_columns()
    
    # Prepare update data
    update_data = {
        'official_name': data['official_name'],
        'date_of_birth': data['date_of_birth'],
        'age': data['age'],
        'residence': data['residence'],
        'active_phone': data['active_phone'],
        'email': data['email'],
        'school_name': data['school_name'],
        'school_level': data['school_level'],
        'school_class': data['school_class'],
        'school_house': data['school_house'],
        'residence_status': data['residence_status'],
        'residence_name': data['residence_name'],
        'church_branch': data['church_branch'],
        'branch_id': branch_id,
        'yoka_hall': data['yoka_hall'],
        'youth_camps_attended': data['youth_camps_attended'],
        'has_church_position': int(data['has_church_position']),
        'church_position_status': data['church_position_status'],
        'church_position_type': data['church_position_type'],
        'church_position_name': data['church_position_name'],
        'church_position_duration': data['church_position_duration'],
        'work_status': data['work_status'],
        'work_type': data['work_type'],
        'work_name': data['work_name'],
        'work_position': data['work_position'],
        'work_location': data['work_location'],
        'work_experience_years': data['work_experience_years'],
        'is_diaspora': int(data['is_diaspora']),
        'diaspora_country': data['diaspora_country'],
        'diaspora_status': data['diaspora_status'],
        'diaspora_job': data['diaspora_job'],
        'diaspora_school': data['diaspora_school'],
        'diaspora_education_level': data['diaspora_education_level'],
        'mother_name': data['mother_name'],
        'mother_phone': data['mother_phone'],
        'mother_occupation': data['mother_occupation'],
        'father_name': data['father_name'],
        'father_phone': data['father_phone'],
        'father_occupation': data['father_occupation'],
        'guardian_name': data['guardian_name'],
        'guardian_phone': data['guardian_phone'],
        'guardian_relationship': data['guardian_relationship'],
        'guardian_occupation': data['guardian_occupation'],
        'last_modified_by': updated_by,
        'last_modified_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'gender': data.get('gender', ''),
        'emergency_contact_name': data.get('emergency_contact_name', ''),
        'emergency_contact_phone': data.get('emergency_contact_phone', ''),
        'medical_conditions': data.get('medical_conditions', ''),
        'talents': data.get('talents', ''),
        'interests': data.get('interests', '')
    }
    
    # Filter to columns that exist and build SET clause
    set_clauses = []
    values = []
    for col, val in update_data.items():
        if col in table_columns and col != 'id':
            set_clauses.append(f"{col} = ?")
            values.append(val)
    
    values.append(member_id)
    query = f"UPDATE members SET {', '.join(set_clauses)} WHERE id = ?"
    
    c.execute(query, values)
    conn.commit()
    log_audit(updated_by, st.session_state.get('username', 'system'), 'UPDATE_MEMBER', 'member', member_id, f"Updated member ID: {member_id}")
    conn.close()
    return True

def delete_member(member_id, deleted_by, user_role, user_branch_id=None):
    """Delete member with permission check"""
    conn = get_connection()
    c = conn.cursor()
    
    if user_role == 'branch_executive':
        c.execute("SELECT branch_id FROM members WHERE id = ?", (member_id,))
        member = c.fetchone()
        if member and member[0] != user_branch_id:
            conn.close()
            return False, "Permission denied: Cannot delete members from other branches"
    
    c.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    log_audit(deleted_by, st.session_state.get('username', 'system'), 'DELETE_MEMBER', 'member', member_id, f"Deleted member ID: {member_id}")
    conn.close()
    return True, "Member deleted successfully"

def verify_member(member_id, verified_by):
    """Verify member data"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE members 
                 SET is_verified = 1, verified_by = ?, verified_date = ?
                 WHERE id = ?""",
              (verified_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), member_id))
    conn.commit()
    log_audit(verified_by, st.session_state.get('username', 'system'), 'VERIFY_MEMBER', 'member', member_id, f"Verified member ID: {member_id}")
    conn.close()
    return True