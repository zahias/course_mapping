import streamlit as st
import pandas as pd
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import save_assignments, validate_assignments, reset_assignments
from google_drive_utils import authenticate_google_drive, search_file, download_file
from googleapiclient.discovery import build
from datetime import datetime
import os
from config import (
    get_allowed_assignment_types,
    GRADE_ORDER,
    extract_primary_grade_from_full_value,
    cell_color
)

st.title("View Reports")
st.markdown("---")

if "raw_df" not in st.session_state:
    st.warning("No data available. Upload in 'Upload Data' first.")
    st.stop()

df = st.session_state["raw_df"]
target_courses = st.session_state.get("target_courses")
intensive_courses = st.session_state.get("intensive_courses")

if target_courses is None or intensive_courses is None:
    st.warning("Courses not defined. Go to 'Customize Courses'.")
    st.stop()

# --- Sync assignments from Google Drive before loading ---
try:
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)
    fid = search_file(service, "sce_fec_assignments.csv")
    if fid:
        download_file(service, fid, "sce_fec_assignments.csv")
        st.info("Loaded assignments from Google Drive.")
except Exception:
    # silently ignore
    pass

# --- Load assignments from local DB (populated by previous runs) ---
from assignment_utils import load_assignments
per_student_assignments = load_assignments()

# --- Read equivalent courses CSV (unchanged) ---
eq_df = None
if os.path.exists("equivalent_courses.csv"):
    eq_df = pd.read_csv("equivalent_courses.csv")
equivalent_courses_mapping = (
    read_equivalent_courses(eq_df) if eq_df is not None else {}
)

# --- Process the progress report ---
full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments,
    equivalent_courses_mapping
)

# --- Calculate credits (unchanged) ---
credits_df = full_req_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, credits_df], axis=1)
int_credits = intensive_req_df.apply(lambda r: calculate_credits(r, intensive_courses), axis=1)
intensive_req_df = pd.concat([intensive_req_df, int_credits], axis=1)

# --- Primary grade view setup (unchanged) ---
primary_req_df = full_req_df.copy()
for c in target_courses:
    primary_req_df[c] = primary_req_df[c].apply(extract_primary_grade_from_full_value)
primary_int_df = intensive_req_df.copy()
for c in intensive_courses:
    primary_int_df[c] = primary_int_df[c].apply(extract_primary_grade_from_full_value)

# --- Toggles (unchanged) ---
show_all = st.checkbox("Show All Grades", value=True)
if show_all:
    disp_req = full_req_df.copy()
    disp_int = intensive_req_df.copy()
else:
    disp_req = primary_req_df.copy()
    disp_int = primary_int_df.copy()

show_comp = st.checkbox("Show Completed/Not Completed Only", value=False)
if show_comp:
    def collapse(val):
        if not isinstance(val, str): return val
        parts = val.split("|")
        if len(parts)==2:
            cs = parts[1].strip()
            try:
                return "c" if int(cs)>0 else ""
            except:
                return "c" if cs.upper()=="PASS" else ""
        return val

    for c in target_courses: disp_req[c] = disp_req[c].apply(collapse)
    for c in intensive_courses: disp_int[c] = disp_int[c].apply(collapse)

# --- Search box for the progress tables ----------------
search_prog = st.text_input(
    "Search Progress (ID or Name)",
    help="Filter the Required and Intensive tables"
)
if search_prog:
    mask_r = disp_req["ID"].astype(str).str.contains(search_prog, case=False, na=False) | \
             disp_req["NAME"].str.contains(search_prog, case=False, na=False)
    mask_i = disp_int["ID"].astype(str).str.contains(search_prog, case=False, na=False) | \
             disp_int["NAME"].str.contains(search_prog, case=False, na=False)
    disp_req = disp_req[mask_r]
    disp_int = disp_int[mask_i]

# --- Style and display (unchanged) ---------------------
styled_req = disp_req.style.applymap(cell_color, subset=pd.IndexSlice[:, list(target_courses.keys())])
styled_int = disp_int.style.applymap(cell_color, subset=pd.IndexSlice[:, list(intensive_courses.keys())])
display_dataframes(styled_req, styled_int, extra_courses_df, df)

st.markdown(
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding:4px;'>Passed</span> | "
    "<span style='background-color: #FFFACD; padding:4px;'>CR</span> | "
    "<span style='background-color: pink; padding:4px;'>Not Completed</span></p>",
    unsafe_allow_html=True
)

# --- Assign Courses section (unchanged) ----------------
st.subheader("Assign Courses")
search_asg = st.text_input("Search by ID, Name or Course")
if search_asg:
    extra_courses_df = extra_courses_df[
        extra_courses_df["ID"].astype(str).str.contains(search_asg, na=False, case=False) |
        extra_courses_df["NAME"].str.contains(search_asg, na=False, case=False) |
        extra_courses_df["Course"].str.contains(search_asg, na=False, case=False)
    ]

edited = add_assignment_selection(extra_courses_df)
col1, col2, col3 = st.columns(3)
with col1:
    btn_save = st.button("Save Assignments")
with col2:
    btn_reset = st.button("Reset All Assignments")
with col3:
    btn_dl = st.button("Download Processed Report")

if btn_reset:
    reset_assignments()
    st.success("Assignments reset.")
    st.rerun()

errs, updated = validate_assignments(edited, per_student_assignments)
if errs:
    st.error("Resolve before saving:")
    for e in errs: st.write(f"- {e}")
elif btn_save:
    save_assignments(updated)
    st.success("Assignments saved.")
    st.rerun()

if btn_dl:
    out = save_report_with_formatting(disp_req, disp_int, datetime.now().strftime("%Y%m%d_%H%M%S"))
    st.session_state["output"] = out.getvalue()
    st.download_button(
        "Download Processed Report",
        data=st.session_state["output"],
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Footer ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:14px;'>"
    "Developed by Dr. Zahi Abdul Sater"
    "</div>",
    unsafe_allow_html=True
)
