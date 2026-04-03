import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os
from PIL import Image
import io

# Page configuration MUST be the first Streamlit command
st.set_page_config(page_title="Kumasi District YoKA Registration", page_icon="⛪", layout="wide")

# Database setup with comprehensive migration
def init_database():
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    # Check if members table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='members'")
    table_exists = c.fetchone()
    
    if table_exists:
        # Get existing columns
        c.execute("PRAGMA table_info(members)")
        existing_columns = [column[1] for column in c.fetchall()]
        
        # Define all new columns that should be added
        new_columns = {
            'profile_picture': 'BLOB',
            'school_name': 'TEXT NOT NULL DEFAULT ""',
            'school_level': 'TEXT NOT NULL DEFAULT ""',
            'school_class': 'TEXT NOT NULL DEFAULT ""',
            'school_house': 'TEXT',
            'residence_status': 'TEXT NOT NULL DEFAULT ""',
            'residence_name': 'TEXT',
            'youth_camps_attended': 'INTEGER DEFAULT 0',
            'is_diaspora': 'BOOLEAN DEFAULT 0',
            'diaspora_country': 'TEXT',
            'diaspora_job': 'TEXT',
            'diaspora_school': 'TEXT',
            'diaspora_education_level': 'TEXT',
            'parent_name': 'TEXT NOT NULL DEFAULT ""',
            'parent_phone': 'TEXT NOT NULL DEFAULT ""',
            'parent_relationship': 'TEXT NOT NULL DEFAULT ""',
            'parent_occupation': 'TEXT NOT NULL DEFAULT ""'
        }
        
        # Add missing columns
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    c.execute(f"ALTER TABLE members ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    pass
        
        # Check if old columns need to be renamed or data migrated
        if 'father_name' in existing_columns:
            try:
                c.execute("UPDATE members SET parent_name = father_name WHERE parent_name = '' OR parent_name IS NULL")
                c.execute("UPDATE members SET parent_phone = father_phone WHERE parent_phone = '' OR parent_phone IS NULL")
                c.execute("UPDATE members SET parent_relationship = 'Father' WHERE parent_relationship = '' OR parent_relationship IS NULL")
                c.execute("UPDATE members SET parent_occupation = father_occupation WHERE parent_occupation = '' OR parent_occupation IS NULL")
            except Exception as e:
                pass
        
        conn.commit()
    else:
        # Create members table with all columns (new database)
        c.execute('''CREATE TABLE members
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
                      yoka_hall TEXT NOT NULL,
                      youth_camps_attended INTEGER NOT NULL,
                      is_diaspora BOOLEAN DEFAULT 0,
                      diaspora_country TEXT,
                      diaspora_job TEXT,
                      diaspora_school TEXT,
                      diaspora_education_level TEXT,
                      parent_name TEXT NOT NULL,
                      parent_phone TEXT NOT NULL,
                      parent_relationship TEXT NOT NULL,
                      parent_occupation TEXT NOT NULL,
                      submission_date TEXT NOT NULL)''')
    
    # Create users table for login
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  is_admin BOOLEAN DEFAULT 0)''')
    
    # Insert default admin user if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                  ('admin', hashed_password, 1))
    
    conn.commit()
    conn.close()

# Password hashing function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Login function
def check_login(username, password):
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

# Function to save member data
def save_member(data, profile_picture=None):
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO members 
                 (official_name, date_of_birth, age, residence, active_phone, email, profile_picture,
                  school_name, school_level, school_class, school_house, residence_status, residence_name,
                  church_branch, yoka_hall, youth_camps_attended,
                  is_diaspora, diaspora_country, diaspora_job, diaspora_school, diaspora_education_level,
                  parent_name, parent_phone, parent_relationship, parent_occupation,
                  submission_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['official_name'], data['date_of_birth'], data['age'], data['residence'], 
               data['active_phone'], data['email'], profile_picture,
               data['school_name'], data['school_level'], data['school_class'], 
               data['school_house'], data['residence_status'], data['residence_name'],
               data['church_branch'], data['yoka_hall'], data['youth_camps_attended'],
               data['is_diaspora'], data['diaspora_country'], data['diaspora_job'], 
               data['diaspora_school'], data['diaspora_education_level'],
               data['parent_name'], data['parent_phone'], data['parent_relationship'], 
               data['parent_occupation'],
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

# Function to get all members with safe column selection
def get_all_members():
    conn = sqlite3.connect('kumasi_yoka_registration.db')
    
    c = conn.cursor()
    c.execute("PRAGMA table_info(members)")
    existing_columns = [column[1] for column in c.fetchall()]
    
    desired_columns = [
        'id', 'official_name', 'date_of_birth', 'age', 'residence', 'active_phone', 'email',
        'school_name', 'school_level', 'school_class', 'school_house', 'residence_status', 'residence_name',
        'church_branch', 'yoka_hall', 'youth_camps_attended',
        'is_diaspora', 'diaspora_country', 'diaspora_job', 'diaspora_school', 'diaspora_education_level',
        'parent_name', 'parent_phone', 'parent_relationship', 'parent_occupation', 'submission_date'
    ]
    
    select_columns = [col for col in desired_columns if col in existing_columns]
    
    if select_columns:
        query = f"SELECT {', '.join(select_columns)} FROM members"
        df = pd.read_sql_query(query, conn)
    else:
        df = pd.DataFrame()
    
    conn.close()
    return df

# Initialize database
init_database()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'is_diaspora' not in st.session_state:
    st.session_state.is_diaspora = False
if 'education_level' not in st.session_state:
    st.session_state.education_level = "SHS"
if 'page' not in st.session_state:
    st.session_state.page = "Login"
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .success-box {
        background-color: #d4edda;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation (only show when logged in)
if st.session_state.logged_in:
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    st.session_state.page = st.sidebar.radio("Go to", ["Registration Form", "View Registrations", "Export Data"])

# Login Page (Landing Page)
if not st.session_state.logged_in:
    st.title("⛪ Kumasi District YoKA Registration System")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### Welcome to Kumasi District YoKA")
        st.markdown("Please login to access the registration form")
        
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.info("Default admin credentials: username: admin, password: admin123")
        
        # Register new account option
        st.markdown("---")
        st.markdown("### New User?")
        with st.expander("Create New Account"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            if st.button("Create Account"):
                if new_password == confirm_password and new_username:
                    conn = sqlite3.connect('kumasi_yoka_registration.db')
                    c = conn.cursor()
                    try:
                        hashed_pw = hash_password(new_password)
                        c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                                (new_username, hashed_pw, 0))
                        conn.commit()
                        st.success("Account created! Please login.")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists!")
                    conn.close()
                else:
                    st.error("Passwords don't match or username is empty")

# Main Registration Form (only visible after login)
elif st.session_state.logged_in and st.session_state.page == "Registration Form":
    st.title("⛪ Kumasi District YoKA Registration Form")
    st.markdown(f"### Welcome, {st.session_state.username}!")
    st.markdown("Please fill out the form below to register with the Kumasi District YoKA.")
    
    # Show success message if form was just submitted
    if st.session_state.show_success:
        st.markdown("""
        <div class="success-box">
            <h3>✅ Registration Successful!</h3>
            <p><strong>Welcome to Kumasi District YoKA!</strong></p>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Register Another Member", key="register_another"):
                st.session_state.show_success = False
                st.session_state.form_submitted = False
                st.rerun()
        with col2:
            if st.button("View All Members", key="view_members"):
                st.session_state.show_success = False
                st.session_state.page = "View Registrations"
                st.rerun()
        st.stop()
    
    # Reset form submitted state when coming back to the form
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
    
    with st.form("registration_form", clear_on_submit=False):
        # Personal Information
        st.header("📋 Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            official_name = st.text_input("Full Name *", key="official_name")
            date_of_birth = st.date_input("Date of Birth (Optional)", min_value=datetime(1950,1,1), 
                                         max_value=datetime.now(), key="dob", value=None)
            residence = st.text_input("Residential Address *", key="residence")
            email = st.text_input("Email Address", key="email")
            
            # Profile Picture
            st.markdown("### 📸 Profile Picture")
            profile_pic = st.file_uploader("Upload Profile Picture", type=['jpg', 'jpeg', 'png'])
            if profile_pic:
                st.image(profile_pic, width=150, caption="Preview")
        
        with col2:
            # Manual age input
            age = st.number_input("Age *", min_value=1, max_value=120, value=18, step=1, key="age")
            active_phone = st.text_input("Active Phone Number(s) *", key="active_phone")
            
            if date_of_birth:
                calculated_age = datetime.now().year - date_of_birth.year
                st.caption(f"💡 Based on DOB: {calculated_age} years (if different, please adjust age above)")
        
        st.markdown("---")
        
        # School Information
        st.header("🎓 School Information")
        
        col3, col4 = st.columns(2)
        with col3:
            school_level = st.selectbox("Education Level *", 
                                       ["SHS", "Tertiary", "Graduate", "Other"],
                                       key="school_level")
            school_name = st.text_input("School Name *", key="school_name")
            school_class = st.text_input("Current Class/Level *", key="school_class")
        
        with col4:
            school_house = st.text_input("House (if applicable)", key="school_house")
            residence_status = st.selectbox("Residence Status *", 
                                           ["Day Student", "Boarder"], key="residence_status")
            residence_name = st.text_input("Residence/Hostel Name (if boarder)", key="residence_name")
        
        st.markdown("---")
        
        # Church Information
        st.header("⛪ Church Information")
        
        # Branch selection
        branches = ["", "Kumasi Central", "Asokwa", "Tafo", "Suame", "Bantama", 
                   "Oforikrom", "Ayigya", "Kentinkrono", "Ahinsan", "Atonsu", 
                   "Bohyen", "Dichemso", "Abuakwa", "Other (Ghana)", "Other Country"]
        
        col5, col6 = st.columns(2)
        with col5:
            church_branch = st.selectbox("Church Branch *", branches, key="church_branch")
            if church_branch == "Other (Ghana)":
                church_branch = st.text_input("Specify Branch in Ghana *", key="other_branch_gh")
            elif church_branch == "Other Country":
                church_branch = st.text_input("Specify Branch and Country *", key="other_branch_country")
        
        with col6:
            yoka_hall = st.selectbox("YoKA Hall *", 
                                    ["", "Hall A", "Hall B", "Hall C", "Hall D", "Hall E", "Other"],
                                    key="yoka_hall")
            if yoka_hall == "Other":
                yoka_hall = st.text_input("Specify Hall", key="other_hall")
        
        # Number of youth camps attended with range selector
        youth_camps = st.slider("Number of YoKA Youth Camps Attended *", 
                               min_value=0, max_value=20, value=0, step=1,
                               key="youth_camps")
        st.markdown(f"**Selected:** {youth_camps} camp(s)")
        
        st.markdown("---")
        
        # Diaspora Information
        st.header("🌍 Diaspora Information")
        is_diaspora = st.checkbox("Are you currently in the diaspora (outside Ghana)?", key="is_diaspora")
        
        if is_diaspora:
            col7, col8 = st.columns(2)
            with col7:
                diaspora_country = st.text_input("Which country are you in? *", key="diaspora_country")
                
                # Radio button to choose between job or school
                diaspora_status = st.radio("Are you:", ["Working", "Studying", "Both"], key="diaspora_status")
                
                if diaspora_status in ["Working", "Both"]:
                    diaspora_job = st.text_input("Current Job/Profession", key="diaspora_job")
                else:
                    diaspora_job = ""
                
                if diaspora_status in ["Studying", "Both"]:
                    diaspora_school = st.text_input("School/Institution", key="diaspora_school")
                    diaspora_education_level = st.selectbox("Level of Education", 
                                                           ["Undergraduate", "Graduate", "Masters", "PhD", "Other"],
                                                           key="diaspora_education_level")
                else:
                    diaspora_school = ""
                    diaspora_education_level = ""
            with col8:
                st.info("📌 Note: As a diaspora member, you'll be connected to our online YoKA programs and events.")
        else:
            diaspora_country = ""
            diaspora_job = ""
            diaspora_school = ""
            diaspora_education_level = ""
        
        st.markdown("---")
        
        # Parent/Guardian Information
        st.header("👨‍👩‍👧 Parent/Guardian Information")
        
        col9, col10 = st.columns(2)
        with col9:
            parent_name = st.text_input("Parent/Guardian Full Name *", key="parent_name")
            parent_phone = st.text_input("Parent/Guardian Phone Number *", key="parent_phone")
        
        with col10:
            parent_relationship = st.selectbox("Relationship *", 
                                              ["", "Father", "Mother", "Guardian", "Other"],
                                              key="parent_relationship")
            parent_occupation = st.text_input("Occupation *", key="parent_occupation")
        
        st.markdown("---")
        
        # Submit button inside form
        submitted = st.form_submit_button("Register for Kumasi District YoKA", use_container_width=True)
        
        if submitted:
            # Validate required fields
            required_fields = [
                official_name, residence, active_phone, age,
                school_name, school_class, residence_status,
                church_branch, yoka_hall,
                parent_name, parent_phone, parent_relationship, parent_occupation
            ]
            
            if is_diaspora:
                if not diaspora_country:
                    st.error("Please specify your diaspora country")
                    st.stop()
            
            if all(required_fields) and school_level and church_branch and yoka_hall and parent_relationship:
                # Convert date of birth to string if provided
                dob_str = date_of_birth.strftime("%Y-%m-%d") if date_of_birth else ""
                
                # Convert profile picture to bytes
                profile_pic_bytes = None
                if profile_pic:
                    profile_pic_bytes = profile_pic.getvalue()
                
                # Prepare data for saving
                data = {
                    'official_name': official_name,
                    'date_of_birth': dob_str,
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
                    
                    'is_diaspora': is_diaspora,
                    'diaspora_country': diaspora_country if is_diaspora else "",
                    'diaspora_job': diaspora_job if is_diaspora else "",
                    'diaspora_school': diaspora_school if is_diaspora else "",
                    'diaspora_education_level': diaspora_education_level if is_diaspora else "",
                    
                    'parent_name': parent_name,
                    'parent_phone': parent_phone,
                    'parent_relationship': parent_relationship,
                    'parent_occupation': parent_occupation
                }
                
                save_member(data, profile_pic_bytes)
                st.session_state.form_submitted = True
                st.session_state.show_success = True
                st.rerun()
            else:
                st.error("Please fill in all required fields (*)")

# View Registrations Page
elif st.session_state.logged_in and st.session_state.page == "View Registrations":
    st.title("📋 Kumasi District YoKA - Registered Members")
    
    df = get_all_members()
    
    if not df.empty:
        # Statistics
        st.header("District Statistics")
        
        stat_cols = []
        if 'official_name' in df.columns:
            stat_cols.append(("Total Members", len(df)))
        if 'age' in df.columns:
            stat_cols.append(("Average Age", round(df['age'].mean(), 1)))
        if 'youth_camps_attended' in df.columns:
            stat_cols.append(("Youth Camps (Avg)", round(df['youth_camps_attended'].mean(), 1)))
        if 'is_diaspora' in df.columns:
            stat_cols.append(("Diaspora Members", df['is_diaspora'].sum()))
        if 'church_branch' in df.columns:
            stat_cols.append(("Unique Branches", df['church_branch'].nunique()))
        
        if stat_cols:
            cols = st.columns(len(stat_cols))
            for idx, (label, value) in enumerate(stat_cols):
                with cols[idx]:
                    st.metric(label, value)
        
        st.divider()
        
        # Search and filter
        st.header("Member List")
        col_search, col_filter1, col_filter2 = st.columns([2, 1, 1])
        with col_search:
            search_term = st.text_input("Search by name or phone")
        with col_filter1:
            if 'school_level' in df.columns:
                level_filter = st.selectbox("Filter by Level", ["All"] + sorted(df['school_level'].dropna().unique().tolist()))
            else:
                level_filter = "All"
        with col_filter2:
            if 'is_diaspora' in df.columns:
                diaspora_filter = st.selectbox("Filter by Location", ["All", "Ghana", "Diaspora"])
            else:
                diaspora_filter = "All"
        
        # Apply filters
        df_filtered = df.copy()
        if search_term and 'official_name' in df.columns:
            mask = (df_filtered['official_name'].str.contains(search_term, case=False, na=False) | 
                   df_filtered['active_phone'].str.contains(search_term, case=False, na=False))
            df_filtered = df_filtered[mask]
        if level_filter != "All" and 'school_level' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['school_level'] == level_filter]
        if diaspora_filter != "All" and 'is_diaspora' in df_filtered.columns:
            if diaspora_filter == "Ghana":
                df_filtered = df_filtered[df_filtered['is_diaspora'] == 0]
            else:
                df_filtered = df_filtered[df_filtered['is_diaspora'] == 1]
        
        # Display table
        display_columns = ['id', 'official_name', 'age', 'active_phone', 'church_branch', 'yoka_hall', 'youth_camps_attended', 'submission_date']
        available_display = [col for col in display_columns if col in df_filtered.columns]
        if available_display:
            st.dataframe(df_filtered[available_display], use_container_width=True)
        
        # View individual record
        st.header("View Member Details")
        if len(df_filtered) > 0 and 'id' in df_filtered.columns:
            selected_id = st.selectbox("Select Member ID", df_filtered['id'].tolist())
            if selected_id:
                record = df_filtered[df_filtered['id'] == selected_id].iloc[0]
                
                with st.expander("Personal Information", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Full Name:** {record.get('official_name', 'N/A')}")
                        st.write(f"**Date of Birth:** {record.get('date_of_birth', 'Not provided')}")
                        st.write(f"**Age:** {record.get('age', 'N/A')}")
                        st.write(f"**Residence:** {record.get('residence', 'N/A')}")
                    with col2:
                        st.write(f"**Phone:** {record.get('active_phone', 'N/A')}")
                        st.write(f"**Email:** {record.get('email', 'N/A')}")
                
                if 'school_name' in record.index:
                    with st.expander("School Information"):
                        st.write(f"**School Level:** {record.get('school_level', 'N/A')}")
                        st.write(f"**School Name:** {record.get('school_name', 'N/A')}")
                        st.write(f"**Class/Level:** {record.get('school_class', 'N/A')}")
                        st.write(f"**House:** {record.get('school_house', 'N/A')}")
                        st.write(f"**Residence Status:** {record.get('residence_status', 'N/A')}")
                        if record.get('residence_name'):
                            st.write(f"**Residence Name:** {record.get('residence_name', 'N/A')}")
                
                if 'church_branch' in record.index:
                    with st.expander("Church & YoKA Information"):
                        st.write(f"**Church Branch:** {record.get('church_branch', 'N/A')}")
                        st.write(f"**YoKA Hall:** {record.get('yoka_hall', 'N/A')}")
                        st.write(f"**Youth Camps Attended:** {record.get('youth_camps_attended', 'N/A')}")
                
                if record.get('is_diaspora'):
                    with st.expander("Diaspora Information"):
                        st.write(f"**Country:** {record.get('diaspora_country', 'N/A')}")
                        st.write(f"**Job:** {record.get('diaspora_job', 'N/A')}")
                        st.write(f"**School:** {record.get('diaspora_school', 'N/A')}")
                        st.write(f"**Education Level:** {record.get('diaspora_education_level', 'N/A')}")
                
                if 'parent_name' in record.index:
                    with st.expander("Parent/Guardian Information"):
                        st.write(f"**Name:** {record.get('parent_name', 'N/A')}")
                        st.write(f"**Phone:** {record.get('parent_phone', 'N/A')}")
                        st.write(f"**Relationship:** {record.get('parent_relationship', 'N/A')}")
                        st.write(f"**Occupation:** {record.get('parent_occupation', 'N/A')}")
                
                st.write(f"**Registered on:** {record.get('submission_date', 'N/A')}")
    else:
        st.info("No registrations yet. Please register a new member to get started.")

# Export Data Page
elif st.session_state.logged_in and st.session_state.page == "Export Data":
    st.title("📥 Export Registration Data")
    
    df = get_all_members()
    
    if not df.empty:
        st.write(f"Total registered members: {len(df)}")
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"kumasi_district_yoka_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("No data to export.")

# Footer
st.sidebar.divider()
st.sidebar.caption("Kumasi District YoKA Registration System v2.0")
st.sidebar.caption("© 2024 All Rights Reserved")


