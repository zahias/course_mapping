import streamlit as st
import pandas as pd
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from logging_utils import log_action
from datetime import datetime
import os
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from config import get_allowed_assignment_types, GRADE_ORDER, extract_primary_grade_from_full_value, cell_color

st.set_page_config(page_title="View Reports", layout="wide")
st.title("Required Courses Progress Report")
# Render the color legend on one line.
st.markdown("<p><strong>Color Legend:</strong> <span style='background-color: lightgreen; padding:2px 5px;'>Passed</span> &nbsp;|&nbsp; <span style='background-color: #FFFACD; padding:2px 5px;'>Currently Registered (CR)</span> &nbsp;|&nbsp; <span style='background-color: pink; padding:2px 5px;'>Not Completed/Failing</span></p>", unsafe_allow_html=True)

if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in the Upload Data page and set courses in the Customize Courses page.")
else:
    df = st.session_state["raw_df"]
    target_courses = st.session_state.get("target_courses")
    intensive_courses = st.session_state.get("intensive_courses")
    if target_courses is None or intensive_courses is None:
        st.warning("Courses not defined yet. Please set courses in the Customize Courses page.")
    else:
        per_student_assignments = load_assignments()
        eq_df = None
        if os.path.exists("equivalent_courses.csv"):
            eq_df = pd.read_csv("equivalent_courses.csv")
        equivalent_courses_mapping = read_equivalent_courses(eq_df) if eq_df is not None else {}

        # Process the report for a full detailed version.
        full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
            df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
        )
        # Append calculated credit columns.
        credits_df = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        full_req_df = pd.concat([full_req_df, credits_df], axis=1)
        intensive_credits_df = intensive_req_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
        intensive_req_df = pd.concat([intensive_req_df, intensive_credits_df], axis=1)

        # Precompute a simplified primary-grade version that preserves the credit info.
        primary_req_df = full_req_df.copy()
        for course in target_courses:
            primary_req_df[course] = primary_req_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))
        primary_int_df = intensive_req_df.copy()
        for course in intensive_courses:
            primary_int_df[course] = primary_int_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))

        # Toggle 1: Show All Grades toggle.
        show_all_toggle = st.checkbox("Show All Grades", value=True, help="Toggle to display full grade details with earned credits or just the primary grade with its credit.")
        if show_all_toggle:
            displayed_req_df = full_req_df.copy()
            displayed_int_df = intensive_req_df.copy()
        else:
            displayed_req_df = primary_req_df.copy()
            displayed_int_df = primary_int_df.copy()

        # Toggle 2: Show Completed/Not Completed Only.
        show_complete_toggle = st.checkbox("Show Completed/Not Completed Only", value=False, help="If enabled, display 'c' for passed courses and blank for courses that did not earn credit.")
        if show_complete_toggle:
            def collapse_pass_fail(val):
                if not isinstance(val, str):
                    return val
                parts = val.split("|")
                if len(parts) == 2:
                    credit_part = parts[1].strip()
                    try:
                        num = int(credit_part)
                        return "c" if num > 0 else ""
                    except ValueError:
                        return "c" if credit_part.upper() == "PASS" else ""
                return val
            for col in target_courses.keys():
                displayed_req_df[col] = displayed_req_df[col].apply(collapse_pass_fail)
            for col in intensive_courses.keys():
                displayed_int_df[col] = displayed_int_df[col].apply(collapse_pass_fail)

        from ui_components import display_dataframes
        display_dataframes(
            displayed_req_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(target_courses.keys())]),
            displayed_int_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(intensive_courses.keys())]),
            extra_courses_df, df
        )

        # ASSIGN COURSES SECTION
        st.subheader("Assign Courses")
        # Remove the previous instructional text.
        
        # Layout: First the search bar.
        search_student = st.text_input("Search by Student ID or Name", help="Filter assignments by student or course")
        # Then display the extra courses table.
        st.dataframe(extra_courses_df, use_container_width=True)
        # Then three buttons on one horizontal row.
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Save Assignments", help="Save updated assignments to Google Drive"):
                errors, updated_assignments = validate_assignments(extra_courses_df, per_student_assignments)
                if errors:
                    st.error("Please resolve assignment errors before saving:")
                    for error in errors:
                        st.write(f"- {error}")
                else:
                    save_assignments(updated_assignments)
                    st.success("Assignments saved.")
                    st.rerun()
        with col2:
            if st.button("Reset All Assignments", help="Clear all assignment data"):
                reset_assignments()
                st.success("All assignments have been reset.")
                st.experimental_rerun()
        with col3:
            if st.button("Download Processed Report", help="Download the final report", key="download_btn"):
                # Instead of an extra download button below, trigger the download here.
                # We use st.download_button below which can be styled.
                pass
        
        # Render the download button (styled differently) on the same horizontal line.
        st.markdown(
            """
            <div style="text-align: center; margin-top: 10px;">
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{data}" download="student_progress_report.xlsx" style="background-color: #007BFF; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">Download Processed Report</a>
            </div>
            """.format(data=st.session_state.get("output", "")), 
            unsafe_allow_html=True
        )

        # Remove the completed vs. remaining credits Plotly section.

        # At the very bottom, add a full-width horizontal bar with developer attribution.
        st.markdown("<hr style='border: none; height: 2px; background-color: #aaa;'/>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 14px;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)

        # Generate and store the output file if not already done.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = save_report_with_formatting(displayed_req_df, displayed_int_df, timestamp)
        st.session_state["output"] = output.getvalue()
        from logging_utils import log_action
        log_action(f"Report generated at {timestamp}")
