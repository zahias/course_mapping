import streamlit as st
import pandas as pd
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

# Define the grading system here.
grading_system = {
    'Counted': ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-'],
    'Not Counted': ['F', 'R', 'W', 'WF', 'I']
}

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

        # Process progress report using dynamic courses configuration.
        required_courses_df, intensive_courses_df, extra_courses_df, _ = process_progress_report(
            df,
            target_courses,
            intensive_courses,
            grading_system,  # Now defined locally above.
            per_student_assignments,
            equivalent_courses_mapping
        )

        credits_df = required_courses_df.apply(lambda row: calculate_credits(row, target_courses, grading_system), axis=1)
        required_courses_df = pd.concat([required_courses_df, credits_df], axis=1)
        intensive_credits_df = intensive_courses_df.apply(lambda row: calculate_credits(row, intensive_courses, grading_system), axis=1)
        intensive_courses_df = pd.concat([intensive_courses_df, intensive_credits_df], axis=1)

        allowed_assignment_types = get_allowed_assignment_types()
        grade_toggle = st.checkbox(
            "Show All Grades",
            value=False,
            help="If checked, display all grades (e.g., 'F, F, D | 3'); if unchecked, show only the primary grade letter."
        )
        completed_toggle = st.checkbox(
            "Show Completed/Not Completed Only",
            value=False,
            help="If checked, display 'c' if completed and '' if not, instead of the grade letters."
        )

        with st.expander("Advanced Filters"):
            req_id_filter = st.text_input("Filter by Student ID", key="req_id_filter")
            req_name_filter = st.text_input("Filter by Student Name", key="req_name_filter")
            req_courses_filter = st.multiselect("Select Courses to Display", options=list(target_courses.keys()), key="req_courses_filter")
            if "# of Credits Completed" in required_courses_df.columns:
                min_credits = int(required_courses_df["# of Credits Completed"].min())
                max_credits = int(required_courses_df["# of Credits Completed"].max())
                credits_range = st.slider("Filter by Completed Credits", min_value=min_credits, max_value=max_credits, value=(min_credits, max_credits))
            else:
                credits_range = (0, 0)

        displayed_df = required_courses_df.copy()
        if req_id_filter:
            displayed_df = displayed_df[displayed_df["ID"].str.contains(req_id_filter, case=False)]
        if req_name_filter:
            displayed_df = displayed_df[displayed_df["NAME"].str.contains(req_name_filter, case=False)]
        if req_courses_filter:
            keep_cols = ["ID", "NAME"]
            selected_courses = [course for course in req_courses_filter if course in displayed_df.columns]
            keep_cols.extend(selected_courses)
            for col in ["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]:
                if col in displayed_df.columns:
                    keep_cols.append(col)
            displayed_df = displayed_df[keep_cols]
            filtered_target_courses = {course: target_courses[course] for course in selected_courses}
        else:
            filtered_target_courses = target_courses

        if "# of Credits Completed" in displayed_df.columns:
            displayed_df = displayed_df[(displayed_df["# of Credits Completed"] >= credits_range[0]) & 
                                        (displayed_df["# of Credits Completed"] <= credits_range[1])]

        intensive_displayed_df = intensive_courses_df.copy()

        if completed_toggle:
            for course in filtered_target_courses:
                if course in displayed_df.columns:
                    displayed_df[course] = displayed_df[course].apply(
                        lambda x: 'c' if isinstance(x, str) and any(
                            g.strip() in filtered_target_courses[course]["counted_grades"] or g.strip().upper() == 'CR'
                            for g in x.split(",") if g.strip()
                        ) else ''
                    )
            for course in intensive_courses:
                if course in intensive_displayed_df.columns:
                    intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                        lambda x: 'c' if isinstance(x, str) and any(
                            g.strip() in intensive_courses[course]["counted_grades"] or g.strip().upper() == 'CR'
                            for g in x.split(",") if g.strip()
                        ) else ''
                    )
        else:
            for course in filtered_target_courses:
                if course in displayed_df.columns:
                    displayed_df[course] = displayed_df[course].apply(
                        lambda x: extract_primary_grade(x, filtered_target_courses[course], grade_toggle)
                    )
            for course in intensive_courses:
                if course in intensive_displayed_df.columns:
                    intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                        lambda x: extract_primary_grade(x, intensive_courses[course], grade_toggle)
                    )

        def make_color_format(course_config):
            def formatter(val):
                if isinstance(val, str):
                    if val.upper().startswith("CR"):
                        return "background-color: #FFFACD"  # light yellow
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
        for course in filtered_target_courses:
            if course in displayed_df.columns:
                styled_df = styled_df.applymap(make_color_format(filtered_target_courses[course]), subset=pd.IndexSlice[:, course])
        styled_intensive_df = intensive_displayed_df.style
        for course in intensive_courses:
            if course in intensive_displayed_df.columns:
                styled_intensive_df = styled_intensive_df.applymap(make_color_format(intensive_courses[course]), subset=pd.IndexSlice[:, course])

        from ui_components import display_dataframes, add_assignment_selection
        display_dataframes(styled_df, styled_intensive_df, extra_courses_df, df)

        st.subheader("Assign Courses")
        # Search bar for extra courses.
        search_student = st.text_input("Search Extra Courses by Student ID or Name", help="Type to filter extra courses", key="extra_search")
        # Inline editable assignment table.
        edited_extra_courses_df = add_assignment_selection(extra_courses_df)
        # Row of three buttons.
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Assignments", help="Save the updated assignments to Google Drive"):
                from assignment_utils import save_assignments, validate_assignments
                errors, updated_per_student_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
                if errors:
                    st.error("Please resolve the following issues before saving assignments:")
                    for error in errors:
                        st.write(f"- {error}")
                else:
                    save_assignments(updated_per_student_assignments)
                    st.success("Assignments saved.")
                    st.experimental_rerun()
        with col2:
            if st.button("Reset All Assignments", help="Clears all saved assignments"):
                from assignment_utils import reset_assignments
                reset_assignments()
                st.success("All assignments have been reset.")
                st.experimental_rerun()
        with col3:
            st.download_button(
                label="Download Processed Report",
                data=st.session_state.get('output', b''),
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_btn"
            )

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
        # (Do not call add_assignment_selection() a second time to avoid duplicate keys.)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp, filtered_target_courses)
        st.session_state['output'] = output.getvalue()
        from logging_utils import log_action
        log_action(f"Report generated at {timestamp}")
        st.download_button(
            label="Download Processed Report",
            data=st.session_state['output'],
            file_name="student_progress_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
