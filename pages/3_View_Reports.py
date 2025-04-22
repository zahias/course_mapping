import streamlit as st
import pandas as pd
import pandas.errors
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import (
    load_assignments,
    save_assignments,
    validate_assignments,
    reset_assignments
)
from datetime import datetime
import os

from config import (
    get_allowed_assignment_types,
    extract_primary_grade_from_full_value,
    cell_color
)

st.title("View Reports")
st.markdown("---")

if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data first.")
    st.stop()

df = st.session_state["raw_df"]
target_cfg = st.session_state.get("target_courses_config")
intensive_cfg = st.session_state.get("intensive_courses_config")

if not target_cfg or not intensive_cfg:
    st.warning("Define courses in 'Customize Courses'.")
    st.stop()

per_assign = load_assignments()

# Load equivalent courses safely
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try:
        eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=["Course","Equivalent"])
else:
    eq_df = pd.DataFrame(columns=["Course","Equivalent"])
equiv_map = read_equivalent_courses(eq_df) if not eq_df.empty else {}

# Process
req_df, int_df, extra_df, _ = process_progress_report(
    df, target_cfg, intensive_cfg, per_assign, equiv_map
)

# Static credits lookup (first definition’s credit)
credits_static = {c: defs[0]['Credits'] for c, defs in target_cfg.items()}

# Append credit summaries
credit_summ = req_df.apply(lambda r: calculate_credits(r, credits_static), axis=1)
req_df = pd.concat([req_df, credit_summ], axis=1)

# Primary‑grade precompute
primary_req = req_df.copy()
for c in target_cfg:
    primary_req[c] = primary_req[c].apply(lambda v: extract_primary_grade_from_full_value(v))

# Toggles
show_all = st.checkbox("Show All Grades", value=True)
show_comp = st.checkbox("Show Completed/Not Completed Only", value=False)

if show_all:
    disp_req = req_df.copy()
else:
    disp_req = primary_req.copy()

if show_comp:
    def collapse(v):
        if not isinstance(v, str):
            return v
        parts = v.split("|")
        if len(parts)==2:
            right = parts[1].strip()
            try:
                return "c" if int(right)>0 else ""
            except ValueError:
                return "c" if right.upper()=="PASS" else ""
        return v
    for c in target_cfg:
        disp_req[c] = disp_req[c].apply(collapse)

# Display tables
display_dataframes(disp_req, int_df, extra_df, df)

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
search = st.text_input("Search by Student ID or Name")
edited = add_assignment_selection(extra_df)

c1, c2, c3 = st.columns(3)
if c2.button("Reset All Assignments"):
    reset_assignments()
    st.success("All assignments reset.")
    st.experimental_rerun()
save = c1.button("Save Assignments")
dl   = c3.button("Download Processed Report")

errors, updated = validate_assignments(edited, per_assign)
if errors:
    st.error("Resolve these errors:")
    for e in errors:
        st.write(f"- {e}")
elif save:
    save_assignments(updated)
    st.success("Assignments saved.")
    st.experimental_rerun()

if dl:
    out = save_report_with_formatting(disp_req, int_df, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button(
        "Download Excel",
        data=out.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
