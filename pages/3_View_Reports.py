import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses,
    extract_primary_grade
)
from ui_components import display_dataframes, add_assignment_selection
from logging_utils import log_action
from google_drive_utils import authenticate_google_drive, download_file, search_file
from googleapiclient.discovery import build
from datetime import datetime
import os
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from config import get_allowed_assignment_types

st.title("View Reports")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' and set courses in 'Customize Courses'.")
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
            df,
            target_courses,
            intensive_courses,
            per_student_assignments,
            equivalent_courses_mapping
        )

        credits_df = required_courses_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        required_courses_df = pd.concat([required_courses_df, credits_df], axis=1)
        intensive_credits_df = intensive_courses_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_courses_df = pd.concat([intensive_courses_df, intensive_credits_df], axis=1)

        allowed_assignment_types = get_allowed_assignment_types()
        grade_toggle = st.checkbox(
            "Show All Grades",
            value=False,
            help="If checked, display all grades for each course (e.g., 'F, F, D | 3'); if unchecked, only the primary counted grade is shown."
        )
        completed_toggle = st.checkbox(
            "Show Completed/Not Completed Only",
            value=False,
            help="If checked, shows 'c' if completed and '' if not, instead of actual grade letters."
        )

        # Create copies for toggling
        displayed_df = required_courses_df.copy()
        intensive_displayed_df = intensive_courses_df.copy()

        if completed_toggle:
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(
                    lambda x: 'c' if isinstance(x, str) and any(
                        g.strip() in target_courses[course]["counted_grades"] or g.strip().upper() == 'CR'
                        for g in x.split(",") if g.strip()
                    ) else ''
                )
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                    lambda x: 'c' if isinstance(x, str) and any(
                        g.strip() in intensive_courses[course]["counted_grades"] or g.strip().upper() == 'CR'
                        for g in x.split(",") if g.strip()
                    ) else ''
                )
        else:
            for course in target_courses:
                displayed_df[course] = displayed_df[course].apply(
                    lambda x: extract_primary_grade(x, target_courses[course], grade_toggle)
                )
            for course in intensive_courses:
                intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                    lambda x: extract_primary_grade(x, intensive_courses[course], grade_toggle)
                )

        def make_color_format(course_config):
            def formatter(val):
                if isinstance(val, str):
                    if val.upper().startswith("CR"):
                        return "background-color: #FFFACD"
                    parts = val.split("|")
                    if parts:
                        grade_part = parts[0].strip()
                        grades_list = [g.strip() for g in grade_part.split(",") if g.strip()]
                        if any(g in course_config["counted_grades"] for g in grades_list):
                            return "background-color: lightgreen"
                        else:
                            return "background-color: pink"
                return ""
            return formatter

        styled_df = displayed_df.style
        for course in target_courses:
            if course in displayed_df.columns:
                styled_df = styled_df.applymap(make_color_format(target_courses[course]), subset=pd.IndexSlice[:, course])
        intensive_styled_df = intensive_displayed_df.style
        for course in intensive_courses:
            if course in intensive_displayed_df.columns:
                intensive_styled_df = intensive_styled_df.applymap(make_color_format(intensive_courses[course]), subset=pd.IndexSlice[:, course])

        from ui_components import display_dataframes, add_assignment_selection
        display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df)

        st.markdown("**Color Legend:**")
        st.markdown("- Light Green: Completed courses")
        st.markdown("- Light Yellow: Currently Registered (CR) courses")
        st.markdown("- Pink: Not Completed/Not Counted courses")

        st.subheader("Assign Courses")
        st.markdown("Select one course per student for each assignment type from extra courses.")
        if st.button("Reset All Assignments", help="Clears all saved assignments"):
            reset_assignments()
            st.success("All assignments have been reset.")
            st.rerun()

        search_student = st.text_input("Search by Student ID or Name", help="Type to filter extra courses by student or course")
        extra_courses_df['ID'] = extra_courses_df['ID'].astype(str)
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
                st.rerun()

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
        output = save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp, target_courses)
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
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = f"backups/{timestamp}"
            os.makedirs(backup_folder, exist_ok=True)
            for f in ["equivalent_courses.csv", "sce_fec_assignments.csv", "app.log"]:
                if os.path.exists(f):
                    shutil.copy(f, backup_folder)
        if st.button("Perform Manual Backup", help="Create a timestamped backup of key files"):
            backup_files()
            st.success("Backup completed.")
