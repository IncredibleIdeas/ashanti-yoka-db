"""Export data UI"""
import streamlit as st
from datetime import datetime
import pandas as pd
from services.member_service import get_members_by_role
from services.branch_service import get_all_branches
from services.audit_service import log_audit
from io import BytesIO

def export_to_excel(df):
    """Export DataFrame to Excel with formatting"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Members', index=False)
        
        from openpyxl.styles import Font, PatternFill, Alignment
        
        workbook = writer.book
        worksheet = writer.sheets['Members']
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return output.getvalue()

def advanced_export_ui():
    """Export data with multiple format options"""
    st.title("📥 Advanced Data Export")
    
    # Get data based on role
    if st.session_state.user_role == 'branch_executive':
        members_df = get_members_by_role(st.session_state.user_role, st.session_state.user_branch_id)
        st.info(f"Exporting data from {st.session_state.branch_name} branch")
    else:
        members_df = get_members_by_role(st.session_state.user_role)
        branches_df = get_all_branches()
        if not branches_df.empty:
            branch_options = ["All Branches"] + branches_df['branch_name'].tolist()
            selected_branch = st.selectbox("Select Branch to Export", branch_options)
            if selected_branch != "All Branches":
                members_df = members_df[members_df['church_branch'] == selected_branch]
                st.info(f"Exporting data from {selected_branch} branch")
            else:
                st.info("Exporting data from ALL branches")
    
    if not members_df.empty:
        st.subheader("Export Options")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Format", ["Excel (.xlsx)", "CSV", "JSON"])
        
        with col2:
            date_range = st.date_input("Date Range", [])
            if len(date_range) == 2:
                members_df['submission_date'] = pd.to_datetime(members_df['submission_date'])
                members_df = members_df[(members_df['submission_date'] >= pd.to_datetime(date_range[0])) &
                                       (members_df['submission_date'] <= pd.to_datetime(date_range[1]))]
        
        # Select columns to export
        st.subheader("Select Columns to Export")
        exclude_columns = ['profile_picture', 'branch_id', 'created_by', 'last_modified_by']
        available_columns = [col for col in members_df.columns if col not in exclude_columns]
        
        selected_columns = st.multiselect("Columns", available_columns, default=available_columns[:15] if len(available_columns) > 15 else available_columns)
        
        if selected_columns:
            export_df = members_df[selected_columns]
            
            st.subheader("Preview")
            st.dataframe(export_df.head(10), use_container_width=True)
            
            st.info(f"📊 Total records to export: {len(export_df)}")
            
            if st.button("📥 Export Data", type="primary", use_container_width=True):
                if export_format == "Excel (.xlsx)":
                    excel_data = export_to_excel(export_df)
                    st.download_button("Download Excel File", excel_data, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                elif export_format == "CSV":
                    csv = export_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                elif export_format == "JSON":
                    json_str = export_df.to_json(orient='records', indent=2)
                    st.download_button("Download JSON", json_str, 
                                     file_name=f"yoka_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
                log_audit(st.session_state.user_id, st.session_state.username, 'EXPORT_DATA', 
                         'members', len(export_df), f"Exported {len(export_df)} records in {export_format}")
    else:
        st.info("No data to export")