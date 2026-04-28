"""User management UI"""
import streamlit as st
from services.user_service import get_all_users, get_user_by_id, create_user, update_user, delete_user, reset_user_password
from services.branch_service import get_all_branches

def user_management_ui():
    """UI for super admin to manage users"""
    st.header("👥 User Management")
    
    tab1, tab2 = st.tabs(["All Users", "Create New User"])
    
    with tab1:
        users_df = get_all_users()
        if not users_df.empty:
            st.dataframe(users_df[['id', 'username', 'full_name', 'email', 'role', 'assigned_branch', 'is_active']], 
                        use_container_width=True)
            
            selected_user = st.selectbox("Select User to Edit", users_df['id'].tolist(),
                                        format_func=lambda x: f"{x} - {users_df[users_df['id']==x]['full_name'].iloc[0]}")
            if selected_user:
                with st.expander("Edit User"):
                    user_data = get_user_by_id(selected_user)
                    if user_data:
                        new_full_name = st.text_input("Full Name", user_data[3] if len(user_data) > 3 else '')
                        new_email = st.text_input("Email", user_data[4] if len(user_data) > 4 else '')
                        new_phone = st.text_input("Phone", user_data[5] if len(user_data) > 5 else '')
                        new_role = st.selectbox("Role", ['super_admin', 'admin', 'branch_executive'], 
                                               index=['super_admin', 'admin', 'branch_executive'].index(user_data[6]) if len(user_data) > 6 else 0)
                        
                        branches_df = get_all_branches()
                        if not branches_df.empty:
                            branch_options = {row['id']: row['branch_name'] for _, row in branches_df.iterrows()}
                            current_branch = user_data[7] if len(user_data) > 7 else None
                            branch_index = list(branch_options.keys()).index(current_branch) if current_branch in branch_options.keys() else 0
                            new_branch = st.selectbox("Assigned Branch", list(branch_options.keys()),
                                                     format_func=lambda x: branch_options.get(x, 'None'),
                                                     index=branch_index)
                        else:
                            new_branch = None
                            st.warning("No branches available")
                        
                        is_active = st.checkbox("Active", user_data[8] == 1 if len(user_data) > 8 else True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update User"):
                                if new_branch:
                                    update_user(selected_user, new_full_name, new_email, new_phone, new_role, 
                                              new_branch, is_active, st.session_state.user_id)
                                    st.success("User updated successfully!")
                                    st.rerun()
                        with col2:
                            new_password = st.text_input("New Password (leave blank to keep current)", type="password")
                            if st.button("Reset Password") and new_password:
                                reset_user_password(selected_user, new_password, st.session_state.user_id)
                                st.success("Password reset and email sent successfully!")
        else:
            st.info("No users found")
    
    with tab2:
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username *")
                full_name = st.text_input("Full Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone *")
            with col2:
                password = st.text_input("Password *", type="password")
                role = st.selectbox("Role *", ['branch_executive', 'admin'])
                
                branches_df = get_all_branches()
                if not branches_df.empty:
                    branch_options = {row['id']: row['branch_name'] for _, row in branches_df.iterrows()}
                    assigned_branch = st.selectbox("Assigned Branch *", list(branch_options.keys()), 
                                                  format_func=lambda x: branch_options[x])
                else:
                    assigned_branch = None
                    st.error("No branches available. Please create a branch first.")
            
            if st.form_submit_button("Create User"):
                if all([username, full_name, email, phone, password, assigned_branch]):
                    success, result = create_user(username, password, full_name, email, phone, role, 
                                                 assigned_branch, st.session_state.user_id)
                    if success:
                        st.success(f"User {username} created successfully! Credentials sent to their email.")
                        st.rerun()
                    else:
                        st.error(result)
                else:
                    st.error("Please fill all required fields")