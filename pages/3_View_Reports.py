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

# Set the page title etc.
st.title("View Reports")
st.markdown("---")

# Reload buttons for equivalent courses and courses configuration
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

# Check if progress data is available
if 'raw_df' not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
else:
    df = st.session_state['raw_df']

    target_courses = st.session_state.get('target_courses')
    intensive_courses = st.session_state.get('intensive_courses')

    if target_courses is None or intensive_courses is None:
        st.warning("Courses not defined yet. Go to 'Customize Courses'.")
    else:
        # Load previously saved assignments, if any
        per_student_assignments = load_assignments()

        # Load equivalent courses mapping from local file (downloaded from Google Drive)
        eq_df = None
        if os.path.exists('equivalent_courses.csv'):
            eq_df = pd.read_csv('equivalent_courses.csv')
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process the progress report data
        required_courses_df, intensive_courses_df, extra_courses_df, _ = process_progress_report(
            df,
            target_courses,
            intensive_courses,
            per_student_assignments,
            equivalent_courses_mapping
        )

        # Calculate credits and append results to the dataframes
        credits_df = required_courses_df.apply(
            lambda row: calculate_credits(row, target_courses), axis=1
        )
        required_courses_df = pd.concat([required_courses_df, credits_df], axis=1)

        intensive_credits_df = intensive_courses_df.apply(
            lambda row: calculate_credits(row, intensive_courses), axis=1
        )
        intensive_courses_df = pd.concat([intensive_courses_df, intensive_credits_df], axis=1)

        # --- Toggle Options ---
        # Toggle to show complete grade tokens versus primary grade only.
        grade_toggle = st.checkbox(
            "Show All Grades",
            value=False,
            help="When checked, display all recorded grade tokens for each course. Otherwise, show only the primary (highest-priority) grade."
        )

        # Toggle for simplified display: if enabled, show 'c' for passed courses and blank for failing ones.
        completed_toggle = st.checkbox(
            "Show Completed/Not Completed Only",
            value=False,
            help="When checked, replace course grade values with a simple 'c' for passed courses; otherwise, show the grade information."
        )

        # --- Helper Function for Grade Extraction ---
        def extract_primary_grade(value):
            """
            Given a processed grade string of the form "grade tokens | credit_or_marker",
            return either all grade tokens (if grade_toggle is True) or the primary grade (based on GRADE_ORDER) if False.
            """
            if not isinstance(value, str):
                return value
            parts = value.split(" | ")
            if len(parts) < 2:
                return value.strip()
            # grades_part contains the grade tokens (e.g., "B+, A, C")
            grades_part = parts[0].strip()
            # When showing all grades, just return all the tokens.
            if grade_toggle:
                return grades_part
            else:
                # Otherwise, select the primary grade based on GRADE_ORDER.
                grades_list = [g.strip() for g in grades_part.split(",") if g.strip()]
                for grade in GRADE_ORDER:
                    if grade in grades_list:
                        return grade
                return grades_list[0] if grades_list else ""

        # Prepare displayed dataframes
        displayed_df = required_courses_df.copy()
        intensive_displayed_df = intensive_courses_df.copy()

        if completed_toggle:
            # Replace each cell with 'c' (for passed) if the cell's marker indicates the course is passed.
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(
                    lambda x: 'c' if (isinstance(x, str) and len(x.split('|')) == 2 and 
                                      x.split('|')[1].strip() not in ['0', 'FAIL']) else ''
                )
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                    lambda x: 'c' if (isinstance(x, str) and len(x.split('|')) == 2 and 
                                      x.split('|')[1].strip() not in ['0', 'FAIL']) else ''
                )
        else:
            # Otherwise, apply the extraction of either full or primary grade tokens.
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(extract_primary_grade)
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(extract_primary_grade)

        # --- Cell Formatting ---
        def color_format(val):
            return cell_color(str(val))

        styled_df = displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(target_courses.keys())])
        intensive_styled_df = intensive_displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(intensive_courses.keys())])

        # Display the processed report in separate tabs
        from ui_components import display_dataframes
        display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df)

        st.markdown("**Color Legend:**")
        st.markdown("- Light Green: Passed courses")
        st.markdown("- Light Yellow: Currently Registered (CR) courses")
        st.markdown("- Pink: Failed or not counted courses")

        # --- Assignment Section (unchanged) ---
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

        # Display summary chart for completed vs. remaining credits
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

        # Generate and provide the processed report file for download
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

        # Manual backup option
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
