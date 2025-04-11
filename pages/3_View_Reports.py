import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from logging_utils import log_action
from google_drive_utils import authenticate_google_drive, download_file, search_file
from googleapiclient.discovery import build
from datetime import datetime
import os
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from config import get_allowed_assignment_types, GRADE_ORDER, cell_color, CourseResult

st.title("View Reports")
st.markdown("---")

if st.button("Reload Equivalent Courses", help="Reload equivalent courses mapping from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        fid = search_file(service, "equivalent_courses.csv")
        if fid:
            download_file(service, fid, "equivalent_courses.csv")
            st.success("Equivalent courses reloaded.")
        else:
            st.error("Equivalent courses file not found.")
    except Exception as e:
        st.error(f"Error: {e}")

if st.button("Reload Courses Configuration", help="Reload courses configuration from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        fid = search_file(service, "courses_config.csv")
        if fid:
            download_file(service, fid, "courses_config.csv")
            st.success("Courses configuration reloaded.")
        else:
            st.error("Courses configuration file not found.")
    except Exception as e:
        st.error(f"Error: {e}")

if 'raw_df' not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' and configure courses in 'Customize Courses'.")
else:
    df = st.session_state['raw_df']
    target_courses = st.session_state.get('target_courses')
    intensive_courses = st.session_state.get('intensive_courses')
    if target_courses is None or intensive_courses is None:
        st.warning("Courses not defined yet. Go to 'Customize Courses'.")
    else:
        per_student_assignments = load_assignments()
        eq_df = None
        if os.path.exists('equivalent_courses.csv'):
            eq_df = pd.read_csv('equivalent_courses.csv')
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        required_courses_df, intensive_courses_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )
        credits_df = required_courses_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        required_courses_df = pd.concat([required_courses_df, credits_df], axis=1)
        intensive_credits_df = intensive_courses_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_courses_df = pd.concat([intensive_courses_df, intensive_credits_df], axis=1)

        allowed_assignment_types = get_allowed_assignment_types()

        grade_toggle = st.checkbox("Show All Grades", value=False,
            help="Display full grade tokens if checked; otherwise show only the primary grade.")
        completed_toggle = st.checkbox("Show Completed/Not Completed Only", value=False,
            help="Replace course grade values with 'c' for passed courses; otherwise, show full grade information.")

        def extract_primary_grade(cell):
            if not isinstance(cell, CourseResult):
                return str(cell)
            # When toggle is on, return full grade tokens (everything before the pipe)
            if grade_toggle:
                return cell.display.split("|")[0].strip()
            else:
                tokens = [g.strip() for g in cell.display.split("|")[0].split(",") if g.strip()]
                for grade in GRADE_ORDER:
                    if grade in tokens:
                        return grade
                return tokens[0] if tokens else ""

        displayed_df = required_courses_df.copy()
        intensive_displayed_df = intensive_courses_df.copy()
        if completed_toggle:
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(lambda x: 'c' if isinstance(x, CourseResult) and x.passed else '')
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(lambda x: 'c' if isinstance(x, CourseResult) and x.passed else '')
        else:
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(extract_primary_grade)
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(extract_primary_grade)

        def color_format(cell):
            if isinstance(cell, CourseResult):
                return cell_color(cell)
            return cell_color(str(cell))
        styled_df = displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(target_courses.keys())])
        intensive_styled_df = intensive_displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(intensive_courses.keys())])
        from ui_components import display_dataframes
        display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df)

        st.markdown("**Color Legend:**")
        st.markdown("- Light Green: Passed courses")
        st.markdown("- Light Yellow: Currently Registered (CR) courses")
        st.markdown("- Pink: Failed or not counted courses")
        st.subheader("Assign Courses")
        st.markdown("Select one course per student for each assignment type from extra courses.")
        if st.button("Reset All Assignments", help="Clear all saved assignments"):
            reset_assignments()
            st.success("All assignments have been reset.")
            st.experimental_rerun()
        search_student = st.text_input("Search by Student ID or Name", help="Filter extra courses by student or course")
        extra_courses_df['ID'] = extra_courses_df['ID'].astype(str)
        for a in allowed_assignment_types:
            extra_courses_df[a] = False
        for idx, row in extra_courses_df.iterrows():
            student_id = row['ID']
            course = row['Course']
            if student_id in per_student_assignments:
                assignments = per_student_assignments[student_id]
                for a in allowed_assignment_types:
                    if assignments.get(a) == course:
                        extra_courses_df.at[idx, a] = True
        if search_student:
            extra_courses_df = extra_courses_df[
                extra_courses_df['ID'].str.contains(search_student, case=False, na=False) |
                extra_courses_df['NAME'].str.contains(search_student, case=False, na=False)
            ]
        from ui_components import add_assignment_selection
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        errors, updated_per_student_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
        if errors:
            st.error("Please resolve the following issues before saving assignments:")
            for error in errors:
                st.write(f"- {error}")
        else:
            if st.button("Save Assignments", help="Save the updated assignments to Google Drive"):
                save_assignments(updated_per_student_assignments)
                st.success("Assignments saved.")
                st.experimental_rerun()

        if '# of Credits Completed' in required_courses_df.columns and '# Remaining' in required_courses_df.columns:
            summary_df = required_courses_df[['ID', 'NAME', '# of Credits Completed', '# Remaining']].copy()
            fig = px.bar(
                summary_df,
                x='NAME',
                y=['# of Credits Completed', '# Remaining'],
                barmode='group',
                title="Completed vs. Remaining Credits per Student"
            )
            st.plotly_chart(fig, use_container_width=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp)
        st.session_state['output'] = output.getvalue()
        log_action(f"Report generated at {timestamp}")
        st.download_button(
            label="Download Processed Report",
            data=st.session_state['output'],
            file_name="student_progress_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        import shutil, datetime
        def backup_files():
            t_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"backups/{t_str}"
            os.makedirs(backup_folder, exist_ok=True)
            for f in ["equivalent_courses.csv", "sce_fec_assignments.csv", "courses_config.csv", "app.log"]:
                if os.path.exists(f):
                    shutil.copy(f, backup_folder)
        if st.button("Perform Manual Backup", help="Backup key files with a timestamp"):
            backup_files()
            st.success("Backup completed.")
