"""Analytics dashboard UI"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from services.member_service import get_members_by_role
from services.branch_service import get_all_branches
from io import BytesIO

def analytics_dashboard_ui():
    """Comprehensive analytics dashboard with charts"""
    st.title("📊 YoKA Analytics Dashboard")
    
    # Get data based on role
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"📈 Analytics for {st.session_state.branch_name} Branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        if not branches_df.empty:
            branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
            selected_branch = st.selectbox("Filter by Branch", branch_options)
            if selected_branch != "All Branches":
                members_df = members_df[members_df['church_branch'] == selected_branch]
                st.info(f"📈 Analytics for {selected_branch} Branch")
            else:
                st.info("📈 Analytics for ALL Branches")
    
    if not members_df.empty:
        members_df['submission_date'] = pd.to_datetime(members_df['submission_date'])
        
        # Key Metrics
        st.subheader("📈 Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_members = len(members_df)
            new_this_month = len(members_df[members_df['submission_date'] > datetime.now() - pd.Timedelta(days=30)])
            st.metric("Total Members", total_members, delta=f"+{new_this_month} this month")
        
        with col2:
            avg_age = round(members_df['age'].mean(), 1)
            st.metric("Average Age", f"{avg_age} years")
        
        with col3:
            verification_rate = (members_df['is_verified'].sum() / len(members_df)) * 100
            st.metric("Verification Rate", f"{verification_rate:.1f}%")
        
        with col4:
            unique_schools = members_df['school_name'].nunique()
            st.metric("Schools", unique_schools)
        
        with col5:
            avg_camps = round(members_df['youth_camps_attended'].mean(), 1)
            st.metric("Avg Camps", avg_camps)
        
        st.divider()
        
        # Growth Trends
        st.subheader("📅 Registration Trends")
        col1, col2 = st.columns(2)
        
        with col1:
            daily_regs = members_df.set_index('submission_date').resample('D').size()
            if len(daily_regs) > 0:
                fig_daily = px.line(x=daily_regs.index, y=daily_regs.values, 
                                    title="Daily Registration Trend",
                                    labels={'x': 'Date', 'y': 'Registrations'})
                fig_daily.update_layout(showlegend=False, hovermode='x unified')
                st.plotly_chart(fig_daily, use_container_width=True)
        
        with col2:
            monthly_regs = members_df.set_index('submission_date').resample('ME').size()
            if len(monthly_regs) > 0:
                fig_monthly = px.bar(x=monthly_regs.index, y=monthly_regs.values,
                                     title="Monthly Registration Trend",
                                     labels={'x': 'Month', 'y': 'Registrations'})
                fig_monthly.update_layout(showlegend=False)
                st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Demographics
        st.subheader("👥 Demographics Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            age_bins = [13, 16, 19, 22, 25, 30]
            age_labels = ['13-15', '16-18', '19-21', '22-24', '25-30']
            members_df['age_group'] = pd.cut(members_df['age'], bins=age_bins, labels=age_labels, right=False)
            age_dist = members_df['age_group'].value_counts().sort_index()
            
            if len(age_dist) > 0:
                fig_age = px.pie(values=age_dist.values, names=age_dist.index, title="Age Distribution")
                fig_age.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            school_level_dist = members_df['school_level'].value_counts()
            if len(school_level_dist) > 0:
                fig_school = px.bar(x=school_level_dist.index, y=school_level_dist.values,
                                   title="Education Levels",
                                   labels={'x': 'Level', 'y': 'Count'})
                fig_school.update_layout(showlegend=False)
                st.plotly_chart(fig_school, use_container_width=True)
        
        with col3:
            hall_dist = members_df['yoka_hall'].value_counts().head(10)
            if len(hall_dist) > 0:
                fig_hall = px.bar(x=hall_dist.index, y=hall_dist.values,
                                 title="YoKA Hall Distribution",
                                 labels={'x': 'Hall', 'y': 'Members'})
                fig_hall.update_layout(showlegend=False)
                st.plotly_chart(fig_hall, use_container_width=True)
        
        # Church Positions Analysis
        if 'has_church_position' in members_df.columns:
            st.subheader("⛪ Church Leadership & Service")
            pos_holders = members_df[members_df['has_church_position'] == 1]
            st.metric("Members with Church Positions", len(pos_holders))
            
            if not pos_holders.empty and 'church_position_status' in pos_holders.columns:
                col1, col2 = st.columns(2)
                with col1:
                    pos_status = pos_holders['church_position_status'].value_counts()
                    if len(pos_status) > 0:
                        fig_status = px.pie(values=pos_status.values, names=pos_status.index, title="Position Status")
                        st.plotly_chart(fig_status, use_container_width=True)
                with col2:
                    if 'church_position_type' in pos_holders.columns:
                        pos_types = pos_holders['church_position_type'].value_counts()
                        if len(pos_types) > 0:
                            fig_pos = px.bar(x=pos_types.index, y=pos_types.values, title="Position Types")
                            st.plotly_chart(fig_pos, use_container_width=True)
    else:
        st.info("No data available for analytics. Start registering members to see insights!")