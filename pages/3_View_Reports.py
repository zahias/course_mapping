# pages/3_View_Reports.py

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
from config import get_allowed_assignment_types, extract_primary_grade_from_full_value, cell_color

st.title("View Reports")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("Upload data first.")
    st.stop()

df = st.session_state['raw_df']
target_courses = st.session_state.get('target_courses')
intensive_courses = st.session_state.get('intensive_courses')
if target_courses is None or intensive_courses is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

# Load assignments
per_student_assignments = load_assignments()

# Load equivalent courses safely
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try:
        eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=['Course','Equivalent'])
else:
    eq_df = pd.DataFrame(columns=['Course','Equivalent'])
equivalent_courses_mapping = read_equivalent_courses(eq_df) if not eq_df.empty else {}

# Process the report
full_req_df, full_int_df, extra_courses_df, _ = process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments,
    equivalent_courses_mapping
)

# Append credit summaries
req_cred = full_req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, req_cred], axis=1)
int_cred = full_int_df.apply(lambda row: calculate_credits(row, intensive_courses), axis=1)
full_int_df = pd.concat([full_int_df, int_cred], axis=1)

# Prepare primary‐grade view
primary_req_df = full_req_df.copy()
for course in target_courses:
    primary_req_df[course] = primary_req_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))
primary_int_df = full_int_df.copy()
for course in intensive_courses:
    primary_int_df[course] = primary_int_df[course].apply(lambda x: extract_primary_grade_from_full_value(x))

# Toggles
show_all = st.checkbox("Show All Grades", value=True,
                       help="Toggle between detailed (all grades+credits) and primary‐only views.")
if show_all:
    displayed_req_df = full_req_df.copy()
    displayed_int_df = full_int_df.copy()
else:
    displayed_req_df = primary_req_df.copy()
    displayed_int_df = primary_int_df.copy()

# CR‐override: if full_req_df cell contains "CR", force that entry
for course in target_courses:
    # mask of rows where full has CR
    cr_mask = full_req_df[course].astype(str).str.contains(r"\bCR\b", na=False)
    # extract the "CR | X" substring from the full cell
    cr_values = full_req_df[course].astype(str).str.extract(r"(CR\s*\|\s*\d+)", expand=False)
    displayed_req_df.loc[cr_mask, course] = cr_values[cr_mask]

for course in intensive_courses:
    cr_mask = full_int_df[course].astype(str).str.contains(r"\bCR\b", na=False)
    cr_values = full_int_df[course].astype(str).str.extract(r"(CR\s*\|\s*\d+)", expand=False)
    displayed_int_df.loc[cr_mask, course] = cr_values[cr_mask]

# Completed/not‐completed toggle
show_comp = st.checkbox("Show Completed/Not Completed Only", value=False,
                       help="Show 'c' for any passed or CR, blank for others.")
if show_comp:
    def collapse_pass(val):
        if not isinstance(val, str):
            return val
        if val.strip().upper().startswith("CR"):
            return "c"
        parts = val.split("|")
        if len(parts) == 2:
            right = parts[1].strip()
            try:
                return "c" if int(right) > 0 else ""
            except:
                return "c" if right.upper() == "PASS" else ""
        return ""
    for course in target_courses:
        displayed_req_df[course] = displayed_req_df[course].apply(collapse_pass)
    for course in intensive_courses:
        displayed_int_df[course] = displayed_int_df[course].apply(collapse_pass)

# Display
display_dataframes(displayed_req_df, displayed_int_df, extra_courses_df, df)

# Color legend
st.markdown(
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding:3px;'>Passed</span> "
    "<span style='background-color: #FFFACD; padding:3px;'>CR</span> "
    "<span style='background-color: pink; padding:3px;'>Not Passed</span></p>",
    unsafe_allow_html=True
)

# Assign Courses
st.subheader("Assign Courses")
_ = st.text_input("Search by Student ID or Name")
edited = add_assignment_selection(extra_courses_df)

c1, c2, c3 = st.columns([1,1,1])
save_btn = c1.button("Save Assignments")
reset_btn = c2.button("Reset All Assignments")
download_btn = c3.button("Download Processed Report")

if reset_btn:
    reset_assignments()
    st.success("Assignments have been reset.")
    st.experimental_rerun()

errors, updated = validate_assignments(edited, per_student_assignments)
if errors:
    st.error("Please resolve the following issues:")
    for err in errors:
        st.write(f"- {err}")
elif save_btn:
    save_assignments(updated)
    st.success("Assignments saved.")
    st.experimental_rerun()

if download_btn:
    out = save_report_with_formatting(displayed_req_df, displayed_int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button(
        "Download Processed Report",
        data=out.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
