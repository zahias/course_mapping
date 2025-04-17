# pages/3_View_Reports.py

import streamlit as st
import pandas as pd
import pandas.errors
import plotly.express as px
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from datetime import datetime
import os
from config import get_allowed_assignment_types, extract_primary_grade_from_full_value, cell_color

st.title("View Reports")
st.markdown("---")

if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' page and set courses in 'Customize Courses' page.")
    st.stop()

# Load the raw data and course lists
df = st.session_state["raw_df"]
target_courses = st.session_state.get("target_courses")
intensive_courses = st.session_state.get("intensive_courses")

if target_courses is None or intensive_courses is None:
    st.warning("Courses not defined yet. Go to 'Customize Courses'.")
    st.stop()

# Load assignments
per_student_assignments = load_assignments()

# Load equivalent courses from CSV, but handle empty file gracefully
eq_df_path = "equivalent_courses.csv"
if os.path.exists(eq_df_path):
    try:
        eq_df = pd.read_csv(eq_df_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=["Course", "Equivalent"])
else:
    eq_df = pd.DataFrame(columns=["Course", "Equivalent"])
equivalent_courses_mapping = read_equivalent_courses(eq_df) if not eq_df.empty else {}

# Process progress report
full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
    df, target_courses, intensive_courses, per_student_assignments, equivalent_courses_mapping
)

# Append calculated credits
credits_df = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, credits_df], axis=1)
int_credits_df = intensive_req_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
intensive_req_df = pd.concat([intensive_req_df, int_credits_df], axis=1)

# Precompute simplified primary-grade view (preserves credits columns)
primary_req_df = full_req_df.copy()
for course in target_courses:
    primary_req_df[course] = primary_req_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))
primary_int_df = intensive_req_df.copy()
for course in intensive_courses:
    primary_int_df[course] = primary_int_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))

# Toggle detailed vs. simplified
show_all = st.checkbox("Show All Grades", value=True, help="Toggle detailed vs. primary-grade views.")
if show_all:
    displayed_req_df = full_req_df.copy()
    displayed_int_df = intensive_req_df.copy()
else:
    displayed_req_df = primary_req_df.copy()
    displayed_int_df = primary_int_df.copy()

# Toggle completed/not‑completed only
show_collapse = st.checkbox("Show Completed/Not Completed Only", value=False, help="Show 'c' for passed courses only.")
if show_collapse:
    def collapse(val):
        if not isinstance(val, str):
            return val
        parts = val.split("|")
        if len(parts) == 2:
            credit = parts[1].strip()
            try:
                return "c" if int(credit) > 0 else ""
            except ValueError:
                return "c" if credit.upper() == "PASS" else ""
        return val
    for col in target_courses:
        displayed_req_df[col] = displayed_req_df[col].apply(collapse)
    for col in intensive_courses:
        displayed_int_df[col] = displayed_int_df[col].apply(collapse)

# Display tables (pass DataFrames, not Stylers)
display_dataframes(displayed_req_df, displayed_int_df, extra_courses_df, df)

# Color legend
st.markdown(
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> "
    "<span style='background-color: #FFFACD; padding: 3px 10px;'>CR</span> "
    "<span style='background-color: pink; padding: 3px 10px;'>Not Passed</span></p>",
    unsafe_allow_html=True
)

# Assign Courses Section
st.subheader("Assign Courses")
search = st.text_input("Search by Student ID or Name")
edited = add_assignment_selection(extra_courses_df)

# Buttons in one row
col1, col2, col3 = st.columns([1,1,1])
save_btn = col1.button("Save Assignments")
reset_btn = col2.button("Reset All Assignments")
download_btn = col3.button("Download Processed Report")

if reset_btn:
    reset_assignments()
    st.success("Assignments reset.")
    st.experimental_rerun()

errors, updated = validate_assignments(edited, per_student_assignments)
if errors:
    st.error("Resolve these errors:")
    for e in errors:
        st.write(f"- {e}")
elif save_btn:
    save_assignments(updated)
    st.success("Assignments saved.")
    st.experimental_rerun()

if download_btn:
    out = save_report_with_formatting(displayed_req_df, displayed_int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button(
        "Download Excel",
        data=out.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
