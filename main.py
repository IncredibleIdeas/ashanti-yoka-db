import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os

# Database setup
def init_database():
    conn = sqlite3.connect('yoka_volunteers.db')
    c = conn.cursor()
    
    # Create volunteers table with new structure
    c.execute('''CREATE TABLE IF NOT EXISTS volunteers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  -- Personal Information
                  official_name TEXT NOT NULL,
                  date_of_birth TEXT NOT NULL,
                  age INTEGER NOT NULL,
                  residence TEXT NOT NULL,
                  active_phone TEXT NOT NULL,
                  email TEXT,
                  interests TEXT,
                  allergies TEXT,
                  
                  -- Father's Details
                  father_name TEXT NOT NULL,
                  father_phone TEXT NOT NULL,
                  father_church_member TEXT NOT NULL,
                  father_branch TEXT,
                  father_position TEXT,
                  father_residence TEXT NOT NULL,
                  father_occupation TEXT NOT NULL,
                  
                  -- Mother's Details
                  mother_name TEXT NOT NULL,
                  mother_phone TEXT NOT NULL,
                  mother_church_member TEXT NOT NULL,
                  mother_branch TEXT,
                  mother_position TEXT,
                  mother_residence TEXT NOT NULL,
                  mother_occupation TEXT NOT NULL,
                  
                  -- Guardian's Details
                  guardian_name TEXT,
                  guardian_phone TEXT,
                  guardian_church_member TEXT,
                  guardian_branch TEXT,
                  guardian_position TEXT,
                  guardian_residence TEXT,
                  guardian_occupation TEXT,
                  
                  -- Educational Information
                  shs_school TEXT NOT NULL,
                  shs_program TEXT NOT NULL,
                  tertiary_school TEXT,
                  tertiary_program TEXT,
                  current_class TEXT NOT NULL,
                  
                  -- Occupation/Apprenticeship
                  job_name TEXT,
                  job_position TEXT,
                  job_experience TEXT,
                  job_location TEXT,
                  
                  -- Church Information
                  church_branch TEXT NOT NULL,
                  church_duration TEXT NOT NULL,
                  church_position TEXT,
                  
                  -- YoKA Info
                  yoka_hall TEXT NOT NULL,
                  yoka_position TEXT,
                  yoka_participation TEXT,
                  youth_camps_attended TEXT,
                  
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
    conn = sqlite3.connect('yoka_volunteers.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

# Function to save volunteer data
def save_volunteer(data):
    conn = sqlite3.connect('yoka_volunteers.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO volunteers 
                 (official_name, date_of_birth, age, residence, active_phone, email, interests, allergies,
                  father_name, father_phone, father_church_member, father_branch, father_position, father_residence, father_occupation,
                  mother_name, mother_phone, mother_church_member, mother_branch, mother_position, mother_residence, mother_occupation,
                  guardian_name, guardian_phone, guardian_church_member, guardian_branch, guardian_position, guardian_residence, guardian_occupation,
                  shs_school, shs_program, tertiary_school, tertiary_program, current_class,
                  job_name, job_position, job_experience, job_location,
                  church_branch, church_duration, church_position,
                  yoka_hall, yoka_position, yoka_participation, youth_camps_attended,
                  submission_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['official_name'], data['date_of_birth'], data['age'], data['residence'], 
               data['active_phone'], data['email'], data['interests'], data['allergies'],
               data['father_name'], data['father_phone'], data['father_church_member'], 
               data['father_branch'], data['father_position'], data['father_residence'], data['father_occupation'],
               data['mother_name'], data['mother_phone'], data['mother_church_member'], 
               data['mother_branch'], data['mother_position'], data['mother_residence'], data['mother_occupation'],
               data['guardian_name'], data['guardian_phone'], data['guardian_church_member'], 
               data['guardian_branch'], data['guardian_position'], data['guardian_residence'], data['guardian_occupation'],
               data['shs_school'], data['shs_program'], data['tertiary_school'], data['tertiary_program'], data['current_class'],
               data['job_name'], data['job_position'], data['job_experience'], data['job_location'],
               data['church_branch'], data['church_duration'], data['church_position'],
               data['yoka_hall'], data['yoka_position'], data['yoka_participation'], data['youth_camps_attended'],
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

# Function to get all volunteers
def get_all_volunteers():
    conn = sqlite3.connect('yoka_volunteers.db')
    df = pd.read_sql_query("SELECT * FROM volunteers", conn)
    conn.close()
    return df

# Initialize database
init_database()

# Page configuration
st.set_page_config(page_title="YoKA Volunteer Form", page_icon="⛪", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Sidebar for navigation
st.sidebar.title("Navigation")
if st.session_state.logged_in:
    st.sidebar.write(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
    
    page = st.sidebar.radio("Go to", ["View Submissions", "Export Data"], key="nav_admin")
else:
    page = st.sidebar.radio("Go to", ["Volunteer Form", "Admin Login"], key="nav_public")

# Admin Login Page
if page == "Admin Login" and not st.session_state.logged_in:
    st.title("Admin Login")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.info("Default admin credentials: username: admin, password: admin123")

# Volunteer Form Page
elif page == "Volunteer Form" and not st.session_state.logged_in:
    st.title("⛪ YoKA Youth Volunteer Registration Form")
    st.write("Please fill out the form below to volunteer with YoKA.")
    st.markdown("---")
    
    # Reset form submitted state when coming back to the form
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
    
    with st.form("volunteer_form"):
        # Personal Information
        st.header("📋 Personal Information")
        col1, col2 = st.columns(2)
        
        with col1:
            official_name = st.text_input("Official Name *", key="official_name")
            date_of_birth = st.date_input("Date of Birth *", min_value=datetime(1950,1,1), 
                                         max_value=datetime.now(), key="dob")
            residence = st.text_input("Where you live *", key="residence")
            email = st.text_input("Email", key="email")
        
        with col2:
            # Calculate age from date of birth
            if date_of_birth:
                today = datetime.now().date()
                age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                st.write(f"**Age:** {age} years")
            else:
                age = 0
                st.write("**Age:** Will be calculated from DOB")
            
            active_phone = st.text_input("Active Phone Numbers *", key="active_phone")
            interests = st.text_area("Interests", key="interests", help="What are your hobbies and interests?")
            allergies = st.text_area("Any allergies", key="allergies", help="Please list any allergies we should know about")
        
        st.markdown("---")
        
        # Parents/Guardian Details
        st.header("👨‍👩‍👧 Parents/Guardian Details")
        
        # Father's Details
        st.subheader("Father's Information")
        col3, col4 = st.columns(2)
        
        with col3:
            father_name = st.text_input("Father's Name *", key="father_name")
            father_phone = st.text_input("Father's Phone Number *", key="father_phone")
            father_church_member = st.selectbox("Is he a church member? *", 
                                              ["", "Yes", "No"], key="father_church_member")
        
        with col4:
            father_branch = st.text_input("If church member, which branch?", key="father_branch")
            father_position = st.text_input("Any position (formal or current)", key="father_position")
        
        col5, col6 = st.columns(2)
        with col5:
            father_residence = st.text_input("Where he lives *", key="father_residence")
        with col6:
            father_occupation = st.text_input("Occupation *", key="father_occupation")
        
        st.markdown("---")
        
        # Mother's Details
        st.subheader("Mother's Information")
        col7, col8 = st.columns(2)
        
        with col7:
            mother_name = st.text_input("Mother's Name *", key="mother_name")
            mother_phone = st.text_input("Mother's Phone Number *", key="mother_phone")
            mother_church_member = st.selectbox("Is she a church member? *", 
                                              ["", "Yes", "No"], key="mother_church_member")
        
        with col8:
            mother_branch = st.text_input("If church member, which branch?", key="mother_branch")
            mother_position = st.text_input("Any position (formal or current)", key="mother_position")
        
        col9, col10 = st.columns(2)
        with col9:
            mother_residence = st.text_input("Where she lives *", key="mother_residence")
        with col10:
            mother_occupation = st.text_input("Occupation *", key="mother_occupation")
        
        st.markdown("---")
        
        # Guardian's Details (Optional)
        st.subheader("Guardian's Information (Optional - if applicable)")
        col11, col12 = st.columns(2)
        
        with col11:
            guardian_name = st.text_input("Guardian's Name", key="guardian_name")
            guardian_phone = st.text_input("Guardian's Phone Number", key="guardian_phone")
            guardian_church_member = st.selectbox("Is he/she a church member?", 
                                                ["", "Yes", "No"], key="guardian_church_member")
        
        with col12:
            guardian_branch = st.text_input("If church member, which branch?", key="guardian_branch")
            guardian_position = st.text_input("Any position (formal or current)", key="guardian_position")
        
        col13, col14 = st.columns(2)
        with col13:
            guardian_residence = st.text_input("Where he/she lives", key="guardian_residence")
        with col14:
            guardian_occupation = st.text_input("Occupation", key="guardian_occupation")
        
        st.markdown("---")
        
        # Educational Information
        st.header("🎓 Educational Information")
        
        st.subheader("Senior High School (SHS)")
        col15, col16 = st.columns(2)
        with col15:
            shs_school = st.text_input("Name of SHS attended *", key="shs_school")
        with col16:
            shs_program = st.text_input("Program offered *", key="shs_program")
        
        st.subheader("Tertiary Education (Optional)")
        col17, col18 = st.columns(2)
        with col17:
            tertiary_school = st.text_input("Name of Tertiary Institution", key="tertiary_school")
        with col18:
            tertiary_program = st.text_input("Program offered", key="tertiary_program")
        
        current_class = st.text_input("Current class or level *", key="current_class")
        
        st.markdown("---")
        
        # Occupation/Apprenticeship
        st.header("💼 Occupation/Apprenticeship")
        st.write("(Leave blank if not applicable)")
        
        col19, col20 = st.columns(2)
        with col19:
            job_name = st.text_input("Name of job", key="job_name")
            job_position = st.text_input("Position", key="job_position")
        
        with col20:
            job_experience = st.text_input("Number of years of experience", key="job_experience")
            job_location = st.text_input("Location of job", key="job_location")
        
        st.markdown("---")
        
        # Church Information
        st.header("⛪ Church Information")
        
        col21, col22 = st.columns(2)
        with col21:
            church_branch = st.text_input("Name of branch *", key="church_branch")
        with col22:
            church_duration = st.text_input("How long you've been at the branch *", key="church_duration")
        
        church_position = st.text_input("Position holding (formal/current)", key="church_position")
        
        st.markdown("---")
        
        # YoKA Info
        st.header("🌟 YoKA Information")
        
        col23, col24 = st.columns(2)
        with col23:
            yoka_hall = st.selectbox("Hall *", 
                                    ["", "Hall A", "Hall B", "Hall C", "Hall D", "Other"], 
                                    key="yoka_hall")
        with col24:
            yoka_position = st.text_input("Position (formal/current)", key="yoka_position")
        
        yoka_participation = st.text_area("Any participation at the hall", key="yoka_participation")
        youth_camps_attended = st.text_input("Number of Youth Camps attended", key="youth_camps_attended")
        
        st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("Submit Registration")
        
        if submitted:
            # Validate required fields
            required_fields = [
                official_name, date_of_birth, residence, active_phone,
                father_name, father_phone, father_church_member, father_residence, father_occupation,
                mother_name, mother_phone, mother_church_member, mother_residence, mother_occupation,
                shs_school, shs_program, current_class,
                church_branch, church_duration, yoka_hall
            ]
            
            # Check if all required fields are filled
            if all(required_fields) and father_church_member and mother_church_member and yoka_hall:
                
                # Calculate age
                today = datetime.now().date()
                age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
                
                # Prepare data for saving
                data = {
                    'official_name': official_name,
                    'date_of_birth': date_of_birth.strftime("%Y-%m-%d"),
                    'age': age,
                    'residence': residence,
                    'active_phone': active_phone,
                    'email': email,
                    'interests': interests,
                    'allergies': allergies,
                    
                    'father_name': father_name,
                    'father_phone': father_phone,
                    'father_church_member': father_church_member,
                    'father_branch': father_branch,
                    'father_position': father_position,
                    'father_residence': father_residence,
                    'father_occupation': father_occupation,
                    
                    'mother_name': mother_name,
                    'mother_phone': mother_phone,
                    'mother_church_member': mother_church_member,
                    'mother_branch': mother_branch,
                    'mother_position': mother_position,
                    'mother_residence': mother_residence,
                    'mother_occupation': mother_occupation,
                    
                    'guardian_name': guardian_name,
                    'guardian_phone': guardian_phone,
                    'guardian_church_member': guardian_church_member,
                    'guardian_branch': guardian_branch,
                    'guardian_position': guardian_position,
                    'guardian_residence': guardian_residence,
                    'guardian_occupation': guardian_occupation,
                    
                    'shs_school': shs_school,
                    'shs_program': shs_program,
                    'tertiary_school': tertiary_school,
                    'tertiary_program': tertiary_program,
                    'current_class': current_class,
                    
                    'job_name': job_name,
                    'job_position': job_position,
                    'job_experience': job_experience,
                    'job_location': job_location,
                    
                    'church_branch': church_branch,
                    'church_duration': church_duration,
                    'church_position': church_position,
                    
                    'yoka_hall': yoka_hall,
                    'yoka_position': yoka_position,
                    'yoka_participation': yoka_participation,
                    'youth_camps_attended': youth_camps_attended
                }
                
                save_volunteer(data)
                st.session_state.form_submitted = True
                st.success("Thank you for registering! Your information has been submitted successfully.")
                st.balloons()
                st.rerun()
            else:
                st.error("Please fill in all required fields (*)")
                if not father_church_member or not mother_church_member or not yoka_hall:
                    st.warning("Please ensure all dropdown selections are made (not left blank)")

# View Submissions Page (Admin only)
elif page == "View Submissions" and st.session_state.logged_in:
    st.title("📋 YoKA Volunteer Submissions")
    
    # Get all volunteers
    df = get_all_volunteers()
    
    if not df.empty:
        # Display statistics
        st.header("Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Volunteers", len(df))
        with col2:
            st.metric("Average Age", round(df['age'].mean(), 1) if 'age' in df.columns else "N/A")
        with col3:
            st.metric("Unique Branches", df['church_branch'].nunique() if 'church_branch' in df.columns else "N/A")
        with col4:
            st.metric("Halls", df['yoka_hall'].nunique() if 'yoka_hall' in df.columns else "N/A")
        
        st.divider()
        
        # Display data table
        st.header("Volunteer List")
        
        # Select columns to display
        display_columns = ['id', 'official_name', 'age', 'active_phone', 'church_branch', 'yoka_hall', 'submission_date']
        available_columns = [col for col in display_columns if col in df.columns]
        
        # Add search/filter
        search_term = st.text_input("Search by name or phone", key="search_term")
        if search_term and 'official_name' in df.columns:
            mask = (df['official_name'].str.contains(search_term, case=False, na=False) | 
                   df['active_phone'].str.contains(search_term, case=False, na=False))
            df_filtered = df[mask]
        else:
            df_filtered = df
        
        # Display the filtered dataframe
        st.dataframe(df_filtered[available_columns] if available_columns else df_filtered, 
                    use_container_width=True)
        
        # View individual record
        st.header("View Individual Record")
        if len(df_filtered) > 0 and 'id' in df_filtered.columns:
            selected_id = st.selectbox("Select volunteer ID", df_filtered['id'].tolist(), key="select_volunteer")
            if selected_id:
                record = df_filtered[df_filtered['id'] == selected_id].iloc[0]
                
                # Personal Information
                with st.expander("Personal Information", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Official Name:** {record.get('official_name', 'N/A')}")
                        st.write(f"**Date of Birth:** {record.get('date_of_birth', 'N/A')}")
                        st.write(f"**Age:** {record.get('age', 'N/A')}")
                        st.write(f"**Residence:** {record.get('residence', 'N/A')}")
                    with col2:
                        st.write(f"**Phone:** {record.get('active_phone', 'N/A')}")
                        st.write(f"**Email:** {record.get('email', 'N/A')}")
                        st.write(f"**Interests:** {record.get('interests', 'N/A')}")
                        st.write(f"**Allergies:** {record.get('allergies', 'N/A')}")
                
                # Parents Information
                with st.expander("Parents/Guardian Information"):
                    tab1, tab2, tab3 = st.tabs(["Father", "Mother", "Guardian"])
                    
                    with tab1:
                        st.write(f"**Name:** {record.get('father_name', 'N/A')}")
                        st.write(f"**Phone:** {record.get('father_phone', 'N/A')}")
                        st.write(f"**Church Member:** {record.get('father_church_member', 'N/A')}")
                        st.write(f"**Branch:** {record.get('father_branch', 'N/A')}")
                        st.write(f"**Position:** {record.get('father_position', 'N/A')}")
                        st.write(f"**Residence:** {record.get('father_residence', 'N/A')}")
                        st.write(f"**Occupation:** {record.get('father_occupation', 'N/A')}")
                    
                    with tab2:
                        st.write(f"**Name:** {record.get('mother_name', 'N/A')}")
                        st.write(f"**Phone:** {record.get('mother_phone', 'N/A')}")
                        st.write(f"**Church Member:** {record.get('mother_church_member', 'N/A')}")
                        st.write(f"**Branch:** {record.get('mother_branch', 'N/A')}")
                        st.write(f"**Position:** {record.get('mother_position', 'N/A')}")
                        st.write(f"**Residence:** {record.get('mother_residence', 'N/A')}")
                        st.write(f"**Occupation:** {record.get('mother_occupation', 'N/A')}")
                    
                    with tab3:
                        if record.get('guardian_name'):
                            st.write(f"**Name:** {record.get('guardian_name', 'N/A')}")
                            st.write(f"**Phone:** {record.get('guardian_phone', 'N/A')}")
                            st.write(f"**Church Member:** {record.get('guardian_church_member', 'N/A')}")
                            st.write(f"**Branch:** {record.get('guardian_branch', 'N/A')}")
                            st.write(f"**Position:** {record.get('guardian_position', 'N/A')}")
                            st.write(f"**Residence:** {record.get('guardian_residence', 'N/A')}")
                            st.write(f"**Occupation:** {record.get('guardian_occupation', 'N/A')}")
                        else:
                            st.info("No guardian information provided")
                
                # Educational Information
                with st.expander("Educational Information"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("SHS")
                        st.write(f"**School:** {record.get('shs_school', 'N/A')}")
                        st.write(f"**Program:** {record.get('shs_program', 'N/A')}")
                    with col2:
                        st.subheader("Tertiary")
                        st.write(f"**School:** {record.get('tertiary_school', 'N/A')}")
                        st.write(f"**Program:** {record.get('tertiary_program', 'N/A')}")
                    st.write(f"**Current Class/Level:** {record.get('current_class', 'N/A')}")
                
                # Occupation/Church/YoKA
                with st.expander("Occupation, Church & YoKA Information"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.subheader("Occupation")
                        st.write(f"**Job:** {record.get('job_name', 'N/A')}")
                        st.write(f"**Position:** {record.get('job_position', 'N/A')}")
                        st.write(f"**Experience:** {record.get('job_experience', 'N/A')} years")
                        st.write(f"**Location:** {record.get('job_location', 'N/A')}")
                    
                    with col2:
                        st.subheader("Church")
                        st.write(f"**Branch:** {record.get('church_branch', 'N/A')}")
                        st.write(f"**Duration:** {record.get('church_duration', 'N/A')}")
                        st.write(f"**Position:** {record.get('church_position', 'N/A')}")
                    
                    with col3:
                        st.subheader("YoKA")
                        st.write(f"**Hall:** {record.get('yoka_hall', 'N/A')}")
                        st.write(f"**Position:** {record.get('yoka_position', 'N/A')}")
                        st.write(f"**Participation:** {record.get('yoka_participation', 'N/A')}")
                        st.write(f"**Camps Attended:** {record.get('youth_camps_attended', 'N/A')}")
                
                st.write(f"**Submitted on:** {record.get('submission_date', 'N/A')}")
    else:
        st.info("No volunteer submissions yet.")

# Export Data Page (Admin only)
elif page == "Export Data" and st.session_state.logged_in:
    st.title("📥 Export Data")
    
    df = get_all_volunteers()
    
    if not df.empty:
        st.write(f"Total records: {len(df)}")
        
        # Export as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"yoka_volunteers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_button"
        )
        
        # Show preview
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
    else:
        st.info("No data to export.")

# Footer
st.sidebar.divider()
st.sidebar.caption("YoKA Volunteer Management System v1.0")
st.sidebar.caption("© 2024 All Rights Reserved")