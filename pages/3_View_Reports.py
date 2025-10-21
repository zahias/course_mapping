import streamlit as st
import pandas as pd
from data_processing import (
    process_progress_report,
    calculate_credits,
    save_report_with_formatting,
    read_equivalent_courses
)
from ui_components import display_dataframes, add_assignment_selection
from assignment_utils import save_assignments, validate_assignments, reset_assignments, load_assignments
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

# === 0) Major Selection ===
if "selected_major" not in st.session_state or st.session_state["selected_major"] is None:
    st.warning("No Major selected. Upload data on the Upload Data page first.")
    st.stop()

major = st.session_state["selected_major"]
local_folder = os.path.join("configs", major)
os.makedirs(local_folder, exist_ok=True)

def _active_assignment_types_for_major(mj: str):
    """Resolve the assignment types currently active for this Major."""
    override = st.session_state.get(f"{mj}_allowed_assignment_types")
    if isinstance(override, (list, tuple)) and len(override) > 0:
        return [str(x) for x in override if str(x).strip()]
    return [str(x) for x in get_allowed_assignment_types()]

# === 1) Ensure raw DataFrame is loaded for this Major ===
raw_key = f"{major}_raw_df"
if raw_key not in st.session_state:
    st.warning("No progress data available for this Major. Upload it on the Upload Data page.")
    st.stop()

df = st.session_state[raw_key]

# === 2) Retrieve this Major’s rules from session_state ===
target_key       = f"{major}_target_courses"
intensive_key    = f"{major}_intensive_courses"
target_rules_key = f"{major}_target_course_rules"
intensive_rules_key = f"{major}_intensive_course_rules"

if (
    target_key not in st.session_state
    or intensive_key not in st.session_state
    or target_rules_key not in st.session_state
    or intensive_rules_key not in st.session_state
):
    st.warning("Courses have not been configured yet for this Major. Customize them first.")
    st.stop()

target_courses    = st.session_state[target_key]
intensive_courses = st.session_state[intensive_key]
target_rules      = st.session_state[target_rules_key]
intensive_rules   = st.session_state[intensive_rules_key]

# === 3) Sync & load assignments from Google Drive for this Major ===
csv_path_for_major = os.path.join(local_folder, "sce_fec_assignments.csv")
try:
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)
    drive_name = f"configs/{major}/sce_fec_assignments.csv"
    fid = search_file(service, drive_name)
    if fid:
        download_file(service, fid, csv_path_for_major)
        st.info("Loaded assignments from Google Drive.")
except Exception:
    pass

per_student_assignments = load_assignments(
    db_path="assignments.db",
    csv_path=csv_path_for_major
)

# === 4) Load equivalent courses for this Major ===
eq_path_for_major = os.path.join(local_folder, "equivalent_courses.csv")
if os.path.exists(eq_path_for_major):
    eq_df = pd.read_csv(eq_path_for_major)
    equivalent_courses_mapping = read_equivalent_courses(eq_df)
else:
    equivalent_courses_mapping = {}

# === 5) Process the progress report using explicitly passed rules ===
full_req_df, intensive_req_df, extra_courses_df, _ = process_progress_report(
    df,
    target_courses,
    intensive_courses,
    target_rules,
    intensive_rules,
    per_student_assignments,
    equivalent_courses_mapping
)

# === 6) Calculate credits for both Required & Intensive ===
credits_df = full_req_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, credits_df], axis=1)

int_credits_df = intensive_req_df.apply(lambda r: calculate_credits(r, intensive_courses), axis=1)
intensive_req_df = pd.concat([intensive_req_df, int_credits_df], axis=1)

# === 7) Build Primary‐Grade view (for toggling) ===
primary_req_df = full_req_df.copy()
for c in target_courses:
    primary_req_df[c] = primary_req_df[c].apply(extract_primary_grade_from_full_value)

primary_int_df = intensive_req_df.copy()
for c in intensive_courses:
    primary_int_df[c] = primary_int_df[c].apply(extract_primary_grade_from_full_value)

# === 8) Toggles: All Grades vs. Primary‐Only ===
show_all_toggle = st.checkbox(
    "Show All Grades",
    value=True,
    help="Toggle between detailed (all grades + credits) vs. simplified (primary grade + credit) view."
)

if show_all_toggle:
    displayed_req_df = full_req_df.copy()
    displayed_int_df = intensive_req_df.copy()
else:
    displayed_req_df = primary_req_df.copy()
    displayed_int_df = primary_int_df.copy()

# === 9) Toggle: Show Completed/Not Completed Only ===
show_complete_toggle = st.checkbox(
    "Show Completed/Not Completed Only",
    value=False,
    help="If enabled, displays 'c' for passed courses and blank for not passed."
)
if show_complete_toggle:
    def collapse_pass_fail(val):
        if not isinstance(val, str):
            return val
        parts = val.split("|")
        if len(parts) == 2:
            credit_str = parts[1].strip()
            try:
                return "c" if int(credit_str) > 0 else ""
            except ValueError:
                return "c" if credit_str.upper() == "PASS" else ""
        return val

    for course in target_courses:
        displayed_req_df[course] = displayed_req_df[course].apply(collapse_pass_fail)
    for course in intensive_courses:
        displayed_int_df[course] = displayed_int_df[course].apply(collapse_pass_fail)

# === 10) Search box for Progress Tables ===
search_progress = st.text_input(
    "Search Progress (Student ID or Name)",
    help="Filter the Required and Intensive tables by ID or Name"
)
if search_progress:
    mask_req = (
        displayed_req_df["ID"].astype(str).str.contains(search_progress, case=False, na=False)
        | displayed_req_df["NAME"].str.contains(search_progress, case=False, na=False)
    )
    mask_int = (
        displayed_int_df["ID"].astype(str).str.contains(search_progress, case=False, na=False)
        | displayed_int_df["NAME"].str.contains(search_progress, case=False, na=False)
    )
    displayed_req_df = displayed_req_df[mask_req]
    displayed_int_df = displayed_int_df[mask_int]

# === 11) Style and Display the DataFrames ===
styled_req = displayed_req_df.style.applymap(
    cell_color,
    subset=pd.IndexSlice[:, list(target_courses.keys())]
)
styled_int = displayed_int_df.style.applymap(
    cell_color,
    subset=pd.IndexSlice[:, list(intensive_courses.keys())]
)

display_dataframes(styled_req, styled_int, extra_courses_df, df)

# === 12) Color Legend ===
st.markdown(
    "<p><strong>Color Legend:</strong> "
    "<span style='background-color: lightgreen; padding: 3px 10px;'>Passed</span> | "
    "<span style='background-color: #FFFACD; padding: 3px 10px;'>Currently Registered (CR)</span> | "
    "<span style='background-color: pink; padding: 3px 10px;'>Not Completed/Failing</span></p>",
    unsafe_allow_html=True
)

# === 13) Assign Courses Section ===
st.subheader("Assign Courses")

# Show which assignment types are currently active for this Major
active_types = _active_assignment_types_for_major(major)
st.caption(f"Active assignment types for **{major}**: {', '.join(active_types) if active_types else '(none)'}")

# Build a UI DataFrame that *includes* already-assigned rows and pre-checks them,
# so selections don't disappear and can be un-checked/changed.
ui_extras = extra_courses_df.copy()

# Gather assigned (student_id, course) pairs
assigned_pairs = set()
for sid, mapping in per_student_assignments.items():
    for atype, crs in mapping.items():
        if atype == "_note":
            continue
        assigned_pairs.add((str(sid), str(crs)))

if assigned_pairs:
    # Re-add assigned rows from the raw df (ID, NAME, Course, Grade, Year, Semester)
    add_back = df[df.apply(lambda r: (str(r.get("ID")), str(r.get("Course"))) in assigned_pairs, axis=1)]
    cols = [c for c in ["ID", "NAME", "Course", "Grade", "Year", "Semester"] if c in add_back.columns]
    add_back = add_back[cols].drop_duplicates(subset=["ID", "Course"])
    if not add_back.empty:
        ui_extras = pd.concat([ui_extras, add_back], ignore_index=True)
        ui_extras = ui_extras.drop_duplicates(subset=["ID", "Course"])

# Add boolean columns for each active assignment type and pre-check if already assigned
for at in active_types:
    if at not in ui_extras.columns:
        ui_extras[at] = False

for sid, mapping in per_student_assignments.items():
    for at, crs in mapping.items():
        if at == "_note":
            continue
        if at in ui_extras.columns:
            mask = (ui_extras["ID"].astype(str) == str(sid)) & (ui_extras["Course"].astype(str) == str(crs))
            ui_extras.loc[mask, at] = True

# Search within the Assign Courses table
search_assign = st.text_input(
    "Search by Student ID, Name, or Course",
    help="Filter extra courses by text"
)
filtered_extras = ui_extras.copy()
if search_assign:
    filtered_extras = filtered_extras[
        filtered_extras["ID"].astype(str).str.contains(search_assign, case=False, na=False)
        | filtered_extras["NAME"].str.contains(search_assign, case=False, na=False)
        | filtered_extras["Course"].str.contains(search_assign, case=False, na=False)
    ]

# Editor (ui_components reads active types dynamically too)
edited_extra_courses_df = add_assignment_selection(filtered_extras)

col1, col2, col3 = st.columns(3)
with col1:
    save_btn = st.button("Save Assignments", help="Save assignments to Google Drive")
with col2:
    reset_btn = st.button("Reset All Assignments", help="Clear all assignments")
with col3:
    download_btn = st.button("Download Processed Report", help="Download Excel report")

if reset_btn:
    reset_assignments(csv_path=csv_path_for_major)
    st.success("All assignments have been reset for this Major.")
    st.rerun()

# Validate new selections; now supports *removal* of assignments too.
errors, updated_assignments = validate_assignments(edited_extra_courses_df, per_student_assignments)
if errors:
    st.error("Please resolve the following issues before saving:")
    for err in errors:
        st.write(f"- {err}")
elif save_btn:
    save_assignments(updated_assignments, csv_path=csv_path_for_major)
    st.success("Assignments saved for this Major.")
    st.rerun()

if download_btn:
    output = save_report_with_formatting(
        displayed_req_df,
        displayed_int_df,
        datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    st.session_state["output"] = output.getvalue()
    st.download_button(
        label="Download Processed Report",
        data=st.session_state["output"],
        file_name="student_progress_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# === 14) Footer ===
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center; font-size:14px;'>"
    "Developed by Dr. Zahi Abdul Sater"
    "</div>",
    unsafe_allow_html=True
)
