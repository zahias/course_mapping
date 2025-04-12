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
from config import get_allowed_assignment_types, GRADE_ORDER, cell_color

st.title("View Reports")
st.markdown("---")

# Reload equivalent courses.
if st.button("Reload Equivalent Courses", help="Download the latest equivalent courses mapping from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, "equivalent_courses.csv")
        if file_id:
            download_file(service, file_id, "equivalent_courses.csv")
            st.success("Equivalent courses reloaded successfully.")
        else:
            st.error("Equivalent courses file not found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading equivalent courses: {e}")

# Reload courses configuration.
if st.button("Reload Courses Configuration", help="Reload courses configuration from Google Drive"):
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, "courses_config.csv")
        if file_id:
            download_file(service, file_id, "courses_config.csv")
            st.success("Courses configuration reloaded successfully.")
        else:
            st.error("Courses configuration file not found on Google Drive.")
    except Exception as e:
        st.error(f"Error reloading courses configuration: {e}")

if 'raw_df' not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
else:
    df = st.session_state['raw_df']
    target_courses = st.session_state.get('target_courses')
    intensive_courses = st.session_state.get('intensive_courses')
    if target_courses is None or intensive_courses is None:
        st.warning("Courses not defined yet. Go to 'Customize Courses'.")
    else:
        per_student_assignments = load_assignments()

        # Load equivalent courses mapping
        eq_df = None
        if os.path.exists('equivalent_courses.csv'):
            eq_df = pd.read_csv('equivalent_courses.csv')
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process progress report; pivot tables now contain tuples.
        pivot_df, intensive_pivot_df, extra_courses_df, _ = process_progress_report(
            df,
            target_courses,
            intensive_courses,
            per_student_assignments,
            equivalent_courses_mapping
        )

        # Create separate DataFrames: one for grade display and one for status
        grade_df = pivot_df.copy()
        status_df = pivot_df.copy()
        for course in target_courses:
            grade_df[course] = grade_df[course].apply(lambda tup: tup[0] if isinstance(tup, tuple) else tup)
            status_df[course] = status_df[course].apply(lambda tup: tup[1] if isinstance(tup, tuple) else "FAILED")
        
        intensive_grade_df = intensive_pivot_df.copy()
        intensive_status_df = intensive_pivot_df.copy()
        for course in intensive_courses:
            intensive_grade_df[course] = intensive_grade_df[course].apply(lambda tup: tup[0] if isinstance(tup, tuple) else tup)
            intensive_status_df[course] = intensive_status_df[course].apply(lambda tup: tup[1] if isinstance(tup, tuple) else "FAILED")
        
        # Calculate credits
        credits_df = pivot_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        pivot_df = pd.concat([pivot_df, credits_df], axis=1)
        intensive_credits_df = intensive_pivot_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_pivot_df = pd.concat([intensive_pivot_df, intensive_credits_df], axis=1)
        
        # Toggle options.
        grade_toggle = st.checkbox(
            "Show All Grades",
            value=False,
            help="When checked, display all grade tokens; otherwise, show only the primary grade."
        )
        completed_toggle = st.checkbox(
            "Show Completed/Not Completed Only",
            value=False,
            help="When enabled, display 'c' for passed courses and blank for failed courses."
        )

        def extract_primary_grade(value):
            """
            For a given grade string, if grade_toggle is True, return all tokens; otherwise,
            return the primary grade from GRADE_ORDER.
            """
            if not isinstance(value, str):
                return value
            parts = value.split(" | ")
            if len(parts) < 2:
                return value.strip()
            tokens = [g.strip() for g in parts[0].split(",") if g.strip()]
            if grade_toggle:
                return ", ".join(tokens)
            else:
                for grade in GRADE_ORDER:
                    if grade in tokens:
                        return grade
                return tokens[0] if tokens else ""

        # Depending on completed_toggle, update the display DataFrame.
        if completed_toggle:
            for course in target_courses:
                grade_df[course] = grade_df[course].apply(
                    lambda x: 'c' if status_df[course].loc[x.index] == "PASSED" else ''
                )
            for course in intensive_courses:
                intensive_grade_df[course] = intensive_grade_df[course].apply(
                    lambda x: 'c' if intensive_status_df[course].loc[x.index] == "PASSED" else ''
                )
        else:
            for course in target_courses:
                grade_df[course] = grade_df[course].apply(extract_primary_grade)
            for course in intensive_courses:
                intensive_grade_df[course] = intensive_grade_df[course].apply(extract_primary_grade)

        # New cell color function based solely on status.
        def cell_color_from_status(status):
            if status.upper() == "CR":
                return 'background-color: #FFFACD'
            elif status.upper() == "PASSED":
                return 'background-color: lightgreen'
            elif status.upper() in ["FAILED", "NR"]:
                return 'background-color: pink'
            else:
                return 'background-color: pink'

        # Apply column-specific styling using the status DataFrame.
        required_styler = grade_df.style
        for course in target_courses.keys():
            required_styler = required_styler.apply(
                lambda s: s.apply(lambda x, course=course: cell_color_from_status(status_df[course].loc[s.index[0]] if not s.empty else "FAILED")),
                subset=[course]
            )
        # Alternatively, you may iterate cell-by-cell. Here, for simplicity, we apply styling based on the status.
        # (Adjust this logic as needed for your implementation.)

        intensive_styler = intensive_grade_df.style
        for course in intensive_courses.keys():
            intensive_styler = intensive_styler.apply(
                lambda s: s.apply(lambda x, course=course: cell_color_from_status(intensive_status_df[course].loc[s.index[0]] if not s.empty else "FAILED")),
                subset=[course]
            )
        
        from ui_components import display_dataframes
        display_dataframes(required_styler, intensive_styler, extra_courses_df, df)

        st.markdown("**Color Legend:**")
        st.markdown("- Light Green: Passed courses")
        st.markdown("- Light Yellow: Currently Registered (CR) courses")
        st.markdown("- Pink: Failed or not counted courses")

        # Assignment Section (unchanged)
        st.subheader("Assign Courses")
        st.markdown("Select one course per student for each assignment type from extra courses.")
        if st.button("Reset All Assignments", help="Clears all saved assignments"):
            reset_assignments()
            st.success("All assignments have been reset.")
            st.experimental_rerun()
        search_student = st.text_input("Search by Student ID or Name", help="Type to filter extra courses by student or course")
        extra_courses_df['ID'] = extra_courses_df['ID'].astype(str)
        allowed_assignment_types = get_allowed_assignment_types()
        for assign_type in allowed_assignment_types:
            extra_courses_df[assign_type] = False
        for idx, row in extra_courses_df.iterrows():
            student_id = row['ID']
            course = row['Course']
            if student_id in per_student_assignments:
                assignments = per_student_assignments[student_id]
                for assign_type in allowed_assignment_types:
                    if assignments.get(assign_type) == course:
                        extra_courses_df.at[idx, assign_type] = True
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
        
        if '# of Credits Completed' in pivot_df.columns and '# Remaining' in pivot_df.columns:
            summary_df = pivot_df[['ID', 'NAME', '# of Credits Completed', '# Remaining']].copy()
            fig = px.bar(
                summary_df,
                x='NAME',
                y=['# of Credits Completed', '# Remaining'],
                barmode='group',
                title="Completed vs. Remaining Credits per Student"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = save_report_with_formatting(grade_df, intensive_grade_df, timestamp)
        st.session_state['output'] = output.getvalue()
        from logging_utils import log_action
        log_action(f"Report generated at {timestamp}")
        st.download_button(
            label="Download Processed Report",
            data=st.session_state['output'],
            file_name="student_progress_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        import shutil, datetime
        def backup_files():
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"backups/{timestamp_str}"
            os.makedirs(backup_folder, exist_ok=True)
            for f in ["equivalent_courses.csv", "sce_fec_assignments.csv", "courses_config.csv", "app.log"]:
                if os.path.exists(f):
                    shutil.copy(f, backup_folder)
        if st.button("Perform Manual Backup", help="Create a timestamped backup of key files"):
            backup_files()
            st.success("Backup completed.")
