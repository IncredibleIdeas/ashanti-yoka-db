"""View members page UI"""
import streamlit as st
import pandas as pd
from services.member_service import get_members_by_role, get_member_by_id, verify_member, delete_member
from services.branch_service import get_all_branches

def view_members_ui():
    """View members with role-based access"""
    st.title("📋 Registered Members")
    
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"Showing members from {st.session_state.branch_name} branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        if not branches_df.empty:
            branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
            selected_branch = st.selectbox("Filter by Branch", branch_options)
            if selected_branch != "All Branches":
                members_df = members_df[members_df['church_branch'] == selected_branch]
    
    if not members_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Members", len(members_df))
        with col2:
            st.metric("Average Age", round(members_df['age'].mean(), 1))
        with col3:
            st.metric("Youth Camps (Avg)", round(members_df['youth_camps_attended'].mean(), 1))
        with col4:
            st.metric("Verified", members_df['is_verified'].sum())
        
        search_term = st.text_input("🔍 Search by name or phone")
        if search_term:
            members_df = members_df[members_df['official_name'].str.contains(search_term, case=False, na=False) | 
                                   members_df['active_phone'].str.contains(search_term, case=False, na=False)]
        
        display_cols = ['id', 'official_name', 'age', 'gender', 'active_phone', 'church_branch', 'yoka_hall', 'submission_date', 'is_verified']
        available_cols = [col for col in display_cols if col in members_df.columns]
        st.dataframe(members_df[available_cols], use_container_width=True)
        
        if len(members_df) > 0:
            selected_id = st.selectbox("Select Member to View Details", members_df['id'].tolist())
            if selected_id:
                member = get_member_by_id(selected_id, st.session_state.user_role, st.session_state.user_branch_id)
                if member:
                    with st.expander("Member Details", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Name:** {member[1] if len(member) > 1 else 'N/A'}")
                            st.write(f"**Gender:** {member[55] if len(member) > 55 else 'N/A'}")
                            st.write(f"**Age:** {member[3] if len(member) > 3 else 'N/A'}")
                            st.write(f"**Phone:** {member[5] if len(member) > 5 else 'N/A'}")
                            st.write(f"**Email:** {member[6] if len(member) > 6 else 'N/A'}")
                            st.write(f"**Residence:** {member[4] if len(member) > 4 else 'N/A'}")
                        with col2:
                            st.write(f"**Branch:** {member[16] if len(member) > 16 else 'N/A'}")
                            st.write(f"**Hall:** {member[18] if len(member) > 18 else 'N/A'}")
                            st.write(f"**School:** {member[12] if len(member) > 12 else 'N/A'}")
                            st.write(f"**Class:** {member[14] if len(member) > 14 else 'N/A'}")
                            st.write(f"**Registered:** {member[51] if len(member) > 51 else 'N/A'}")
                        
                        # Church Position Section
                        if len(member) > 20 and member[20]:
                            st.subheader("⛪ Church Position")
                            position_status = member[21] if len(member) > 21 else 'N/A'
                            status_icon = "✅" if position_status == "Present" else "📜"
                            st.write(f"{status_icon} **Status:** {position_status} Position")
                            st.write(f"**Position Type:** {member[22] if len(member) > 22 else 'N/A'}")
                            st.write(f"**Position Name:** {member[23] if len(member) > 23 else 'N/A'}")
                            st.write(f"**Duration:** {member[24] if len(member) > 24 else 'N/A'}")
                        
                        # Verification and Actions
                        if len(member) > 52 and member[52]:
                            st.success("✅ Verified Member")
                        else:
                            st.warning("⏳ Pending Verification")
                        
                        if st.session_state.user_role in ['super_admin', 'admin'] and (len(member) > 52 and not member[52]):
                            if st.button("Verify Member"):
                                verify_member(selected_id, st.session_state.user_id)
                                st.success("Member verified!")
                                st.rerun()
                        
                        if st.session_state.user_role == 'super_admin':
                            if st.button("Delete Member", type="secondary"):
                                success, message = delete_member(selected_id, st.session_state.user_id, 
                                                                st.session_state.user_role, st.session_state.user_branch_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
    else:
        st.info("No members registered yet")