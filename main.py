# main.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime

from config import get_default_target_courses, get_default_grading_system, get_intensive_courses
from utilities import save_uploaded_file
from data_processing import read_progress_report, process_progress_report, calculate_credits, save_report_with_formatting
from ui_components import display_sidebar, display_main_interface, display_dataframes, add_sce_fec_selection
from logging_utils import setup_logging, log_action

def load_assignments(file_path='sce_fec_assignments.csv'):
    if os.path.exists(file_path):
        assignments_df = pd.read_csv(file_path)
        per_student_assignments = {}
        for _, row in assignments_df.iterrows():
            student_id = str(row['student_id'])
            assignment_type = row['assignment_type']
            course = row['course']
            if student_id not in per_student_assignments:
                per_student_assignments[student_id] = {}
            per_student_assignments[student_id][assignment_type] = course
        return per_student_assignments
    else:
        return {}

def save_assignments(per_student_assignments, file_path='sce_fec_assignments.csv'):
    assignments_list = []
    for student_id, assignments in per_student_assignments.items():
        for assignment_type, course in assignments.items():
            assignments_list.append({'student_id': student_id, 'assignment_type': assignment_type, 'course': course})
    assignments_df = pd.DataFrame(assignments_list)
    assignments_df.to_csv(file_path, index=False)

def reset_assignments(file_path='sce_fec_assignments.csv'):
    if os.path.exists(file_path):
        os.remove(file_path)

def validate_assignments(edited_df, per_student_assignments):
    errors = []
    new_assignments = {}

    for _, row in edited_df.iterrows():
        student_id = str(row['ID'])
        sce_selected = row['S.C.E.']
        fec_selected = row['F.E.C.']
        course = row['Course']

        if student_id not in new_assignments:
            new_assignments[student_id] = {}

        if sce_selected and fec_selected:
            errors.append(f"Course {course} for Student ID {student_id} cannot be both S.C.E. and F.E.C.")
            continue

        if sce_selected:
            if 'S.C.E.' in new_assignments[student_id]:
                errors.append(f"Student ID {student_id} has multiple S.C.E. courses selected.")
            else:
                new_assignments[student_id]['S.C.E.'] = course
        if fec_selected:
            if 'F.E.C.' in new_assignments[student_id]:
                errors.append(f"Student ID {student_id} has multiple F.E.C. courses selected.")
            else:
                new_assignments[student_id]['F.E.C.'] = course

    # Merge new assignments with existing ones
    for student_id, assignments in new_assignments.items():
        if student_id not in per_student_assignments:
            per_student_assignments[student_id] = assignments
        else:
            per_student_assignments[student_id].update(assignments)

    return errors, per_student_assignments

def main():
    setup_logging()
    display_main_interface()

    default_grading_system = get_default_grading_system()
    target_courses = get_default_target_courses()
    intensive_courses = get_intensive_courses()

    # File uploader for progress report
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key='progress_report')
    if uploaded_file is not None:
        filepath = save_uploaded_file(uploaded_file)
        df = read_progress_report(filepath)
        if df is not None:
            df['ID'] = df['ID'].astype(str)
            df['Semester'] = pd.Categorical(df['Semester'], categories=['Spring', 'Summer', 'Fall'], ordered=True)
            df['Course'] = df['Course'].str.strip().str.upper()
            df['Grade'] = df['Grade'].str.strip().str.upper()

            # Load previous assignments
            per_student_assignments = load_assignments()

            # Process the report with per_student_assignments
            required_courses_df, intensive_courses_df, extra_courses_df, _ = process_progress_report(
                df, target_courses, intensive_courses, default_grading_system, per_student_assignments
            )

            # Recalculate credits for required courses
            credits_df = required_courses_df.apply(
                lambda row: calculate_credits(row, target_courses, default_grading_system), axis=1
            )
            required_courses_df = pd.concat([required_courses_df, credits_df], axis=1)

            # Recalculate credits for intensive courses
            intensive_credits_df = intensive_courses_df.apply(
                lambda row: calculate_credits(row, intensive_courses, default_grading_system), axis=1
            )
            intensive_courses_df = pd.concat([intensive_courses_df, intensive_credits_df], axis=1)

            # Define a function to extract the primary grade
            def extract_primary_grade(value, grading_system, show_all_grades):
                if isinstance(value, str):
                    parts = value.split(' | ')
                    grades_part = parts[0]
                    grades_list = [g.strip() for g in grades_part.split(',') if g.strip()]
                    if show_all_grades:
                        return ', '.join(grades_list)
                    else:
                        for grade in grading_system['Counted']:
                            if grade in grades_list:
                                return grade
                        return grades_list[0] if grades_list else ''
                return value

            # Display the DataFrame based on toggles
            displayed_df = required_courses_df.copy()
            intensive_displayed_df = intensive_courses_df.copy()

            # Now display the sidebar
            target_courses_custom, grading_system, grade_toggle, completed_toggle = display_sidebar(
                default_grading_system
            )

            if target_courses_custom is not None:
                target_courses = target_courses_custom

            if completed_toggle:
                for course in target_courses:
                    displayed_df[course] = displayed_df[course].apply(
                        lambda x: 'c' if isinstance(x, str) and (
                            any(grade.strip() in grading_system['Counted'] or 'CR' in grade.strip().upper()
                                for grade in x.split(' | ')[0].split(',') if grade.strip())
                        ) else ''
                    )
                for course in intensive_courses:
                    intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                        lambda x: 'c' if isinstance(x, str) and (
                            any(grade.strip() in grading_system['Counted'] or 'CR' in grade.strip().upper()
                                for grade in x.split(' | ')[0].split(',') if grade.strip())
                        ) else ''
                    )
            else:
                for course in target_courses:
                    displayed_df[course] = displayed_df[course].apply(
                        lambda x: extract_primary_grade(x, grading_system, grade_toggle)
                    )
                for course in intensive_courses:
                    intensive_displayed_df[course] = intensive_displayed_df[course].apply(
                        lambda x: extract_primary_grade(x, grading_system, grade_toggle)
                    )

            # Apply color-coding to the DataFrames
            def color_format(val):
                if val == 'c':
                    return 'background-color: lightgreen'
                elif val == '':
                    return 'background-color: pink'
                else:
                    if isinstance(val, str):
                        grades_list = [g.strip() for g in val.split(',') if g.strip()]
                        if any(grade in grading_system['Counted'] or 'CR' == grade.upper() for grade in grades_list):
                            return 'background-color: lightgreen'
                        else:
                            return 'background-color: pink'
                return ''

            styled_df = displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(target_courses.keys())])
            intensive_styled_df = intensive_displayed_df.style.applymap(color_format, subset=pd.IndexSlice[:, list(intensive_courses.keys())])

            # Display dataframes
            display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df)

            # Provide a place to assign S.C.E and F.E.C under 'Extra Courses' tab
            st.subheader("Assign S.C.E. and F.E.C. Courses")
            st.write("Select one S.C.E. and one F.E.C. course per student from extra courses.")

            # Add reset button
            if st.button("Reset All Assignments"):
                reset_assignments()
                st.success("All assignments have been reset.")
                st.rerun()

            # Add search function
            search_student = st.text_input("Search by Student ID or Name", key='search_student')

            # Prepare the DataFrame for assignment
            extra_courses_df['ID'] = extra_courses_df['ID'].astype(str)
            extra_courses_df['S.C.E.'] = False
            extra_courses_df['F.E.C.'] = False

            # Load previous assignments into the DataFrame
            for idx, row in extra_courses_df.iterrows():
                student_id = row['ID']
                course = row['Course']
                if student_id in per_student_assignments:
                    assignments = per_student_assignments[student_id]
                    if assignments.get('S.C.E.') == course:
                        extra_courses_df.at[idx, 'S.C.E.'] = True
                    if assignments.get('F.E.C.') == course:
                        extra_courses_df.at[idx, 'F.E.C.'] = True

            # Filter the DataFrame based on search input
            if search_student:
                extra_courses_df = extra_courses_df[
                    extra_courses_df['ID'].str.contains(search_student, case=False, na=False) |
                    extra_courses_df['NAME'].str.contains(search_student, case=False, na=False)
                ]

            # Allow assignment of S.C.E and F.E.C
            edited_extra_courses_df = add_sce_fec_selection(extra_courses_df)

            # Validate assignments
            errors, updated_per_student_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)

            if errors:
                st.error("Please resolve the following issues before proceeding:")
                for error in errors:
                    st.write(f"- {error}")
            else:
                if st.button("Save Assignments"):
                    save_assignments(updated_per_student_assignments)
                    st.success("Assignments saved.")
                    st.rerun()

            # Save the report (including formatting)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp, grading_system)
            st.session_state['output'] = output.getvalue()
            log_action(f"Report generated at {timestamp}")

            # Provide Download Button for Processed Report
            st.download_button(
                label="Download Processed Report",
                data=st.session_state['output'],
                file_name="student_progress_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Failed to read data from the uploaded progress report.")
    else:
        st.info("Please upload an Excel file to proceed.")

if __name__ == "__main__":
    main()
