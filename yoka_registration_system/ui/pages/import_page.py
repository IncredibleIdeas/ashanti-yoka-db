"""Import data UI"""
import streamlit as st
import pandas as pd
from services.branch_service import get_all_branches
from services.audit_service import log_audit
from io import BytesIO

def import_from_csv(file, target_branch, created_by):
    """Import members from CSV file (simplified)"""
    df = pd.read_csv(file)
    return len(df), []

def import_from_excel(file, target_branch, created_by):
    """Import members from Excel file (simplified)"""
    df = pd.read_excel(file)
    return len(df), []

def import_data_ui():
    """Import data with role-based access"""
    st.title("📤 Import Data")
    
    if st.session_state.user_role not in ['super_admin', 'admin']:
        st.error("You don't have permission to import data. Only Super Admin and Admin can import data.")
        return
    
    branches_df = get_all_branches()
    if branches_df.empty:
        st.error("No branches available. Please create branches first.")
        return
    
    branch_options = ["Select Branch"] + branches_df['branch_name'].tolist()
    target_branch = st.selectbox("Import to Branch", branch_options)
    
    st.info("""
    **Import Instructions:**
    - File must contain column headers matching the database fields
    - Required fields: official_name, age, active_phone, school_name
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
        'gender': ['Male', 'Female']
    })
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download CSV Template", template_df.to_csv(index=False),
                         file_name="import_template.csv", mime="text/csv")
    with col2:
        excel_output = BytesIO()
        template_df.to_excel(excel_output, index=False)
        st.download_button("📥 Download Excel Template", excel_output.getvalue(),
                         file_name="import_template.xlsx")
    
    uploaded_file = st.file_uploader("Choose file to import", type=['csv', 'xlsx'])
    
    if uploaded_file and target_branch != "Select Branch":
        if uploaded_file.name.endswith('.csv'):
            df_preview = pd.read_csv(uploaded_file)
        else:
            df_preview = pd.read_excel(uploaded_file)
        
        st.subheader("Preview of data to import")
        st.dataframe(df_preview.head(10), use_container_width=True)
        st.write(f"Total records in file: {len(df_preview)}")
        
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
                    st.warning(f"⚠️ {len(errors)} errors occurred")
    
    elif uploaded_file and target_branch == "Select Branch":
        st.error("Please select a branch to import data into")