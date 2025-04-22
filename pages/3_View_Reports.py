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
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from datetime import datetime
import os
from config import get_allowed_assignment_types, extract_primary_grade_from_full_value, cell_color

st.title("View Reports")
st.markdown("---")

<<<<<<< HEAD
<<<<<<< HEAD
# 1) Ensure raw data & course lists
=======
>>>>>>> parent of 98d5b2a (3)
=======
# 1) Ensure raw data & course lists
>>>>>>> parent of abfac76 (3)
if "raw_df" not in st.session_state:
    st.warning("Upload data first.")
    st.stop()
<<<<<<< HEAD
<<<<<<< HEAD
df = st.session_state["raw_df"]
target = st.session_state.get("target_courses")
intensive = st.session_state.get("intensive_courses")
rules = st.session_state.get("course_rules", {})
if target is None or intensive is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

# 2) Load assignments
per_student = load_assignments()

# 3) Load equivalent courses safely
=======

# Load raw data and course configs
=======
>>>>>>> parent of abfac76 (3)
df = st.session_state["raw_df"]
target = st.session_state.get("target_courses")
intensive = st.session_state.get("intensive_courses")
rules = st.session_state.get("course_rules", {})
if target is None or intensive is None:
    st.warning("Define courses in Customize Courses.")
    st.stop()

# 2) Load assignments
per_student = load_assignments()

<<<<<<< HEAD
# Load equivalent-courses CSV, handle empty
>>>>>>> parent of 98d5b2a (3)
=======
# 3) Load equivalent courses safely
>>>>>>> parent of abfac76 (3)
eq_path = "equivalent_courses.csv"
if os.path.exists(eq_path):
    try:
        eq_df = pd.read_csv(eq_path)
    except pd.errors.EmptyDataError:
        eq_df = pd.DataFrame(columns=["Course","Equivalent"])
else:
    eq_df = pd.DataFrame(columns=["Course","Equivalent"])
eq_map = read_equivalent_courses(eq_df) if not eq_df.empty else {}

<<<<<<< HEAD
<<<<<<< HEAD
# 4) Process
full_req, full_int, extra_df, _ = process_progress_report(
    df,
    target,
    intensive,
    per_student_assignments=per_student,
    equivalent_courses_mapping=eq_map,
    course_rules=rules
)

# 5) Append credits summary
cred_req = full_req.apply(lambda r: calculate_credits(r, target), axis=1)
full_req = pd.concat([full_req, cred_req], axis=1)
cred_int = full_int.apply(lambda r: calculate_credits(r, intensive), axis=1)
full_int = pd.concat([full_int, cred_int], axis=1)

# 6) Simplified primary‐grade view (with credits)
prim_req = full_req.copy()
for c in target:
    prim_req[c] = prim_req[c].apply(lambda x: extract_primary_grade_from_full_value(x))
prim_int = full_int.copy()
for c in intensive:
    prim_int[c] = prim_int[c].apply(lambda x: extract_primary_grade_from_full_value(x))

# 7) Toggles
show_all = st.checkbox("Show All Grades", True)
if show_all:
    disp_req, disp_int = full_req.copy(), full_int.copy()
else:
    disp_req, disp_int = prim_req.copy(), prim_int.copy()

collapse = st.checkbox("Show Completed/Not Completed Only", False)
if collapse:
    def collapse_fn(v):
        if not isinstance(v, str): return v
        parts = v.split("|")
        if len(parts)==2:
            try:
                return "c" if int(parts[1].strip())>0 else ""
            except:
                return "c" if parts[1].strip().upper()=="PASS" else ""
        return v
    for col in target: disp_req[col] = disp_req[col].apply(collapse_fn)
    for col in intensive: disp_int[col] = disp_int[col].apply(collapse_fn)

# 8) Display
=======
# Process report with time‐aware passing rules
req_df, int_df, extra_df, _ = process_progress_report(
=======
# 4) Process
full_req, full_int, extra_df, _ = process_progress_report(
>>>>>>> parent of abfac76 (3)
    df,
    target,
    intensive,
    per_student_assignments=per_student,
    equivalent_courses_mapping=eq_map,
    course_rules=rules
)

# 5) Append credits summary
cred_req = full_req.apply(lambda r: calculate_credits(r, target), axis=1)
full_req = pd.concat([full_req, cred_req], axis=1)
cred_int = full_int.apply(lambda r: calculate_credits(r, intensive), axis=1)
full_int = pd.concat([full_int, cred_int], axis=1)

# 6) Simplified primary‐grade view (with credits)
prim_req = full_req.copy()
for c in target:
    prim_req[c] = prim_req[c].apply(lambda x: extract_primary_grade_from_full_value(x))
prim_int = full_int.copy()
for c in intensive:
    prim_int[c] = prim_int[c].apply(lambda x: extract_primary_grade_from_full_value(x))

# 7) Toggles
show_all = st.checkbox("Show All Grades", True)
if show_all:
    disp_req, disp_int = full_req.copy(), full_int.copy()
else:
    disp_req, disp_int = prim_req.copy(), prim_int.copy()

collapse = st.checkbox("Show Completed/Not Completed Only", False)
if collapse:
    def collapse_fn(v):
        if not isinstance(v, str): return v
        parts = v.split("|")
        if len(parts)==2:
            try:
                return "c" if int(parts[1].strip())>0 else ""
            except:
                return "c" if parts[1].strip().upper()=="PASS" else ""
        return v
    for col in target: disp_req[col] = disp_req[col].apply(collapse_fn)
    for col in intensive: disp_int[col] = disp_int[col].apply(collapse_fn)

<<<<<<< HEAD
def collapse(val):
    if not isinstance(val, str): return val
    parts = val.split("|")
    if len(parts)==2:
        p = parts[1].strip()
        try:
            return "c" if int(p)>0 else ""
        except:
            return "c" if p.upper()=="PASS" else ""
    return val

def prepare(df_full, df_prim):
    df = df_full if show_all else df_prim
    if show_only:
        for col in target_cfg:
            df[col] = df[col].apply(collapse)
        for col in intensive_cfg:
            df[col] = df[col].apply(collapse)
    return df

disp_req = prepare(req_df, prim_req)
disp_int = prepare(int_df, prim_int)

# Display
>>>>>>> parent of 98d5b2a (3)
display_dataframes(disp_req, disp_int, extra_df, df)

st.markdown(
<<<<<<< HEAD
=======
# 8) Display
display_dataframes(disp_req, disp_int, extra_df, df)

st.markdown(
>>>>>>> parent of abfac76 (3)
    "<p><strong>Legend:</strong> "
    "<span style='background-color:lightgreen;padding:3px;'>Passed</span> "
    "<span style='background-color:#FFFACD;padding:3px;'>CR</span> "
    "<span style='background-color:pink;padding:3px;'>Not Passed</span></p>",
<<<<<<< HEAD
=======
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding: 3px;'>Passed</span> "
    "<span style='background-color: #FFFACD; padding: 3px;'>CR</span> "
    "<span style='background-color: pink; padding: 3px;'>Not Passed</span></p>",
>>>>>>> parent of 98d5b2a (3)
=======
>>>>>>> parent of abfac76 (3)
    unsafe_allow_html=True
)

# 9) Assign Courses
st.subheader("Assign Courses")
search = st.text_input("Search by Student ID or Name")
edited = add_assignment_selection(extra_df)

c1,c2,c3 = st.columns(3)
<<<<<<< HEAD
<<<<<<< HEAD
save_btn = c1.button("Save Assignments")
reset_btn = c2.button("Reset All Assignments")
dl_btn    = c3.button("Download Processed Report")

if reset_btn:
    reset_assignments()
    st.success("Assignments reset.")
    st.experimental_rerun()

errs, updated = validate_assignments(edited, per_student)
if errs:
    st.error("Resolve errors:")
    for e in errs: st.write(f"- {e}")
=======
save_btn    = c1.button("Save Assignments")
reset_btn   = c2.button("Reset All Assignments")
download_btn= c3.button("Download Processed Report")
=======
save_btn = c1.button("Save Assignments")
reset_btn = c2.button("Reset All Assignments")
dl_btn    = c3.button("Download Processed Report")
>>>>>>> parent of abfac76 (3)

if reset_btn:
    reset_assignments()
    st.success("Assignments reset.")
    st.experimental_rerun()

<<<<<<< HEAD
errors, updated = validate_assignments(edited, per_student_assignments)
if errors:
    st.error("Resolve the following:")
    for e in errors:
        st.write(f"- {e}")
>>>>>>> parent of 98d5b2a (3)
=======
errs, updated = validate_assignments(edited, per_student)
if errs:
    st.error("Resolve errors:")
    for e in errs: st.write(f"- {e}")
>>>>>>> parent of abfac76 (3)
elif save_btn:
    save_assignments(updated)
    st.success("Assignments saved.")
    st.experimental_rerun()

<<<<<<< HEAD
<<<<<<< HEAD
if dl_btn:
=======
if download_btn:
>>>>>>> parent of 98d5b2a (3)
=======
if dl_btn:
>>>>>>> parent of abfac76 (3)
    out = save_report_with_formatting(disp_req, disp_int, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.download_button(
        "Download Excel",
        data=out.getvalue(),
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

<<<<<<< HEAD
<<<<<<< HEAD
# 10) Footer
=======
>>>>>>> parent of 98d5b2a (3)
=======
# 10) Footer
>>>>>>> parent of abfac76 (3)
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;'>Developed by Dr. Zahi Abdul Sater</div>", unsafe_allow_html=True)
