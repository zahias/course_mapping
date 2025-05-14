import streamlit as st
import pandas as pd
import pandas.errors
from datetime import datetime
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
import os
from config import (
    get_allowed_assignment_types,
    extract_primary_grade_from_full_value,
    cell_color
)

st.title("View Reports")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("Upload data first.")
    st.stop()

# Load raw data and course definitions
df = st.session_state['raw_df']
target_courses = st.session_state.get('target_courses')
intensive_courses = st.session_state.get('intensive_courses')
if target_courses is None or intensive_courses is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

per_student_assignments = load_assignments()

# Load equivalent courses (handle empty file)
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try:
        eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=['Course', 'Equivalent'])
else:
    eq_df = pd.DataFrame(columns=['Course', 'Equivalent'])
equivalent_courses_mapping = (
    read_equivalent_courses(eq_df) if not eq_df.empty else {}
)

# Process the report
req_df, intensive_df, extra_courses_df, _ = process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments,
    equivalent_courses_mapping
)

# Append credit summaries
credits_df = req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
req_df = pd.concat([req_df, credits_df], axis=1)
int_credits_df = intensive_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
intensive_df = pd.concat([intensive_df, int_credits_df], axis=1)

# Show / hide all‐grades vs. primary‐grade view dynamically
show_all = st.checkbox(
    "Show All Grades",
    value=True,
    help="Toggle detailed vs. primary-grade views."
)

if show_all:
    displayed_req_df = req_df.copy()
    displayed_int_df = intensive_df.copy()
else:
    displayed_req_df = req_df.copy()
    for course in target_courses:
        displayed_req_df[course] = displayed_req_df[course].apply(
            extract_primary_grade_from_full_value
        )
    displayed_int_df = intensive_df.copy()
    for course in intensive_courses:
        displayed_int_df[course] = displayed_int_df[course].apply(
            extract_primary_grade_from_full_value
        )

# Show completed/not‐completed only toggle
show_complete = st.checkbox(
    "Show Completed/Not Completed Only",
    value=False,
    help="If enabled, displays 'c' for passed courses and blank for failed courses."
)
if show_complete:
    def collapse(val):
        if not isinstance(val, str):
            return val
        parts = val.split("|")
        if len(parts) == 2:
            n = parts[1].strip()
            try:
                return "c" if int(n) > 0 else ""
            except:
                return "c" if n.upper() == "PASS" else ""
        return val

    for course in target_courses:
        displayed_req_df[course] = displayed_req_df[course].apply(collapse)
    for course in intensive_courses:
        displayed_int_df[course] = displayed_int_df[course].apply(collapse)

# Render the tables
display_dataframes(
    displayed_req_df, displayed_int_df, extra_courses_df, df
)

# Single‐line color legend
st.markdown(
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding:3px 8px;'>Passed</span> "
    "<span style='background-color:#FFFACD; padding:3px 8px;'>CR</span> "
    "<span style='background-color:pink; padding:3px 8px;'>Not Passed</span></p>",
    unsafe_allow_html=True
)

# Assign Courses section
st.subheader("Assign Courses")
_ = st.text_input("Search by Student ID or Name")
edited_extra_courses_df = add_assignment_selection(extra_courses_df)

col1, col2, col3 = st.columns([1, 1, 1])
save_btn     = col1.button("Save Assignments")
reset_btn    = col2.button("Reset All Assignments")
download_btn = col3.button("Download Processed Report")

if reset_btn:
    reset_assignments()
    st.success("Assignments have been reset.")
    st.experimental_rerun()

errors, updated_per_student = validate_assignments(
    edited_extra_courses_df,
    per_student_assignments
)
if errors:
    st.error("Please resolve the following issues before saving assignments:")
    for err in errors:
        st.write(f"- {err}")
elif save_btn:
    save_assignments(updated_per_student)
    st.success("Assignments saved.")
    st.experimental_rerun()

if download_btn:
    output = save_report_with_formatting(
        displayed_req_df, displayed_int_df,
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    st.download_button(
        label="Download Processed Report",
        data=output.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>",
    unsafe_allow_html=True
)
