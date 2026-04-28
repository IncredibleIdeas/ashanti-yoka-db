"""Registration form UI"""
import streamlit as st
from datetime import datetime
from services.member_service import save_member
from services.branch_service import get_all_branches

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
            if not branches_df.empty:
                branch_options = branches_df['branch_name'].tolist()
                church_branch = st.selectbox("Church Branch *", branch_options)
            else:
                church_branch = st.text_input("Church Branch *")
        
        yoka_hall = st.selectbox("YoKA Hall *", ["Hall A", "Hall B", "Hall C", "Hall D", "Hall E", "Other"])
        if yoka_hall == "Other":
            yoka_hall = st.text_input("Specify Hall")
        
        youth_camps = st.slider("Number of YoKA Youth Camps Attended *", min_value=0, max_value=20, value=0)
        
        # Church Position/Service Information
        st.subheader("🙏 Church Leadership & Service")
        st.caption("Please indicate if you currently hold or have formerly held a church position")
        
        has_church_position = st.radio("Do you currently hold or have you formerly held a church position?", 
                                       ["No", "Yes - Presently Holding", "Yes - Formerly Held"], 
                                       index=0)
        
        church_position_status = ""
        church_position_type = ""
        church_position_name = ""
        church_position_duration = ""
        
        if has_church_position != "No":
            col_pos1, col_pos2 = st.columns(2)
            with col_pos1:
                church_position_type = st.selectbox("Position Type", ["Sevent Member", "YoKA Executive", "Other"])
                if church_position_type == "Other":
                    church_position_name = st.text_input("Please specify the position name")
                else:
                    church_position_name = church_position_type
            with col_pos2:
                church_position_duration = st.text_input("How long have you been/had been in this position?", 
                                                        placeholder="e.g., 2 years, 6 months, 1 year 3 months")
            
            if has_church_position == "Yes - Presently Holding":
                church_position_status = "Present"
            else:
                church_position_status = "Former"
        
        # Work Information
        st.header("💼 Work Information")
        col_work1, col_work2 = st.columns(2)
        with col_work1:
            work_status = st.selectbox("Work Status", ["None", "Apprenticeship", "Internship", "Permanent Staff", "Part-time"])
        with col_work2:
            work_type = ""
            if work_status != "None":
                work_type = st.selectbox("Type of Work", ["Formal Employment", "Self-Employed", "Freelance", "Volunteer", "Other"])
        
        work_name = work_position = work_location = ""
        work_experience_years = 0
        
        if work_status != "None":
            col_work3, col_work4 = st.columns(2)
            with col_work3:
                work_name = st.text_input("Name of Workplace/Organization")
                work_position = st.text_input("Your Position/Title")
            with col_work4:
                work_location = st.text_input("Work Location (City/Country)")
                work_experience_years = st.number_input("Number of Years of Experience", min_value=0, max_value=30, value=0)
        
        # Diaspora Information
        st.header("🌍 Diaspora Information")
        is_diaspora = st.checkbox("Are you currently in the diaspora (outside Ghana)?")
        
        diaspora_country = diaspora_status = diaspora_job = diaspora_school = diaspora_education_level = ""
        
        if is_diaspora:
            col_dias1, col_dias2 = st.columns(2)
            with col_dias1:
                diaspora_country = st.text_input("Which country are you in? *")
                diaspora_status = st.selectbox("Status in Diaspora", ["Working", "Studying", "Both"])
            
            with col_dias2:
                if diaspora_status in ["Working", "Both"]:
                    diaspora_job = st.text_input("Current Job/Profession")
                
                if diaspora_status in ["Studying", "Both"]:
                    diaspora_school = st.text_input("School/Institution")
                    diaspora_education_level = st.selectbox("Level of Education", 
                                                           ["Undergraduate", "Graduate", "Masters", "PhD", "Other"])
        
        # Parent/Guardian Information
        st.header("👨‍👩‍👧 Parent/Guardian Information")
        st.info("Please provide information for at least one parent or guardian")
        
        # Mother's Information
        st.subheader("👩 Mother's Information")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mother_name = st.text_input("Mother's Full Name")
            mother_phone = st.text_input("Mother's Phone Number")
        with col_m2:
            mother_occupation = st.text_input("Mother's Occupation")
        
        st.divider()
        
        # Father's Information
        st.subheader("👨 Father's Information")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            father_name = st.text_input("Father's Full Name")
            father_phone = st.text_input("Father's Phone Number")
        with col_f2:
            father_occupation = st.text_input("Father's Occupation")
        
        st.divider()
        
        # Guardian's Information (Optional)
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
            has_parent_guardian = (mother_name and mother_phone) or (father_name and father_phone) or (guardian_name and guardian_phone)
            
            if all([official_name, residence, active_phone, school_name, school_class, residence_status, yoka_hall, gender, church_branch, school_level]) and has_parent_guardian:
                # Process talents and interests
                talents_str = ', '.join(talents) if talents else ''
                interests_str = ', '.join(interests) if interests else ''
                
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
                    'school_house': school_house if school_house else "",
                    'residence_status': residence_status,
                    'residence_name': residence_name if residence_status == "Boarder" else "",
                    'church_branch': church_branch,
                    'yoka_hall': yoka_hall,
                    'youth_camps_attended': youth_camps,
                    'has_church_position': has_church_position != "No",
                    'church_position_status': church_position_status,
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
                    'talents': talents_str,
                    'interests': interests_str
                }
                
                try:
                    save_member(data, created_by=st.session_state.user_id)
                    st.success("Member registered successfully!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving member: {str(e)}")
            else:
                missing = []
                if not official_name: missing.append("Full Name")
                if not residence: missing.append("Address")
                if not active_phone: missing.append("Phone")
                if not school_name: missing.append("School")
                if not church_branch: missing.append("Branch")
                if not has_parent_guardian: missing.append("Parent/Guardian")
                if missing:
                    st.error(f"Please fill: {', '.join(missing)}")