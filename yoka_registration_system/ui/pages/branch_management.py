"""Branch management UI"""
import streamlit as st
from services.branch_service import get_all_branches, get_branch_by_id, create_branch, update_branch, delete_branch

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
                        new_location = st.text_input("Location", branch_data[3] if len(branch_data) > 3 else '')
                        new_contact_person = st.text_input("Contact Person", branch_data[4] if len(branch_data) > 4 else '')
                        new_contact_phone = st.text_input("Contact Phone", branch_data[5] if len(branch_data) > 5 else '')
                        
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
                        success, result = create_branch(branch_name, branch_code, location, contact_person, 
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