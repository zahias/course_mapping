# 3_View_Reports.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from data_processing import (
    process_progress_report,
    calculate_credits,
    read_equivalent_courses
)
from utilities import save_uploaded_file
from assignment_utils import load_assignments, save_assignments, validate_assignments, reset_assignments
from config import (
    get_allowed_assignment_types,
    extract_primary_grade_from_full_value,
    cell_color
)
from ui_components import display_dataframes, add_assignment_selection
from google_drive_utils import authenticate_google_drive, search_file, download_file
from googleapiclient.discovery import build

st.title("View Reports")
st.markdown("---")

# Load raw data and course config
if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload in 'Upload Data' and configure in 'Customize Courses'.")
    st.stop()

df = st.session_state["raw_df"]
target_courses = st.session_state["target_courses"]
intensive_courses = st.session_state["intensive_courses"]
per_student_assignments = load_assignments()

# Load equivalent courses from Drive (if exists)
eq_map = {}
try:
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)
    fid = search_file(service, "equivalent_courses.csv")
    if fid:
        download_file(service, fid, "equivalent_courses.csv")
        eq_df = pd.read_csv("equivalent_courses.csv")
        from data_processing import read_equivalent_courses
        eq_map = read_equivalent_courses(eq_df)
except:
    pass  # no file or error: proceed with empty mapping

# Process the full pivot
full_req_df, full_int_df, extra_courses_df, _ = process_progress_report(
    df, target_courses, intensive_courses, per_student_assignments, eq_map
)

# Append credit summary columns
credits_req = full_req_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, credits_req], axis=1)
credits_int = full_int_df.apply(lambda r: calculate_credits(r, intensive_courses), axis=1)
full_int_df = pd.concat([full_int_df, credits_int], axis=1)

# --- SIDEBAR: Advanced Filters & Saved Views ---
st.sidebar.header("Advanced Filters & Views")

# 1. Load or Save a named view
if "saved_views" not in st.session_state:
    st.session_state["saved_views"] = {}

view_to_load = st.sidebar.selectbox(
    "Load Saved View",
    options=["(none)"] + list(st.session_state["saved_views"].keys())
)
if view_to_load != "(none)":
    loaded = st.session_state["saved_views"][view_to_load]
else:
    loaded = {}

# 2. Semester & Year filters
years = sorted(full_req_df["Year"].unique())
year_min, year_max = st.sidebar.slider(
    "Year Range",
    min_value=int(min(years)), max_value=int(max(years)),
    value=(loaded.get("year_min", min(years)), loaded.get("year_max", max(years)))
)
semesters = ["Spring", "Summer", "Fall"]
semesters_sel = st.sidebar.multiselect(
    "Semesters", semesters,
    default=loaded.get("semesters", semesters)
)

# 3. Credits-remaining threshold
max_rem = int(full_req_df["# Remaining"].max())
rem_threshold = st.sidebar.slider(
    "Max Credits Remaining",
    min_value=0, max_value=max_rem,
    value=loaded.get("rem_threshold", max_rem)
)

# 4. Extra courses filter by assignment type
assign_types = get_allowed_assignment_types()
atype_sel = st.sidebar.multiselect(
    "Assignment Types (extra courses)",
    assign_types,
    default=loaded.get("atype_sel", assign_types)
)

# 5. Column visibility & ordering
all_course_cols = list(target_courses.keys())
col_order = st.sidebar.multiselect(
    "Show & Order Course Columns",
    options=all_course_cols,
    default=loaded.get("col_order", all_course_cols)
)

# 6. Save current view
view_name = st.sidebar.text_input("Save Current View As", key="view_name")
if st.sidebar.button("Save View"):
    st.session_state["saved_views"][view_name] = {
        "year_min": year_min,
        "year_max": year_max,
        "semesters": semesters_sel,
        "rem_threshold": rem_threshold,
        "atype_sel": atype_sel,
        "col_order": col_order
    }
    st.sidebar.success(f"View '{view_name}' saved.")

# --- APPLY FILTERS ---
# Filter required df by year & semester & remaining credits
mask = (
    (full_req_df["Year"].between(year_min, year_max)) &
    (full_req_df["# Remaining"] <= rem_threshold)
)
full_req_df = full_req_df[mask]
full_int_df = full_int_df[full_req_df.index]

# Filter extra courses by assignment type
extra_courses_df = extra_courses_df[
    extra_courses_df["assignment_type"].isin(atype_sel)
]

# --- Main Tabs ---
tabs = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses", "Trend Chart", "Heatmap", "What‑If"])

with tabs[0]:
    st.subheader("Required Courses")
    # Select toggles and completed/not completed as before...
    # Then display only columns in col_order:
    display_df = full_req_df[["ID", "NAME"] + col_order + ["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]]
    display_dataframes(
        display_df.style.applymap(cell_color, subset=pd.IndexSlice[:, col_order]),
        None, None, df
    )

with tabs[1]:
    st.subheader("Intensive Courses")
    display_df = full_int_df[["ID", "NAME"] + col_order]  # reuse col_order for simplicity
    display_dataframes(None,
        display_df.style.applymap(cell_color, subset=pd.IndexSlice[:, col_order]),
        None, df
    )

with tabs[2]:
    st.subheader("Extra Courses")
    st.dataframe(extra_courses_df, use_container_width=True)

with tabs[3]:
    st.subheader("Trend Chart")
    student = st.selectbox("Select Student", full_req_df["NAME"].unique())
    stud_df = df[df["NAME"] == student].copy()
    stud_df["Sem_Order"] = stud_df["Semester"].map({"Spring":1,"Summer":2,"Fall":3})
    stud_df = stud_df.sort_values(["Year","Sem_Order"])
    fig = px.line(
        stud_df,
        x=stud_df["Year"].astype(str) + " " + stud_df["Semester"],
        y=stud_df["Grade"].replace({g:i for i,g in enumerate(["F","D-","D","D+","C-",...,"A+"],1)}),
        markers=True,
        title=f"Grade Progression: {student}"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("Heatmap Calendar")
    # Count completions per semester
    comp = df.copy()
    comp["Passed"] = comp["Grade"].apply(lambda g: any([x in str(g) for x in target_courses.keys()]))
    summary = comp.groupby(["Year","Semester"]).size().unstack(fill_value=0)
    fig = px.imshow(summary, labels=dict(x="Semester", y="Year", color="Courses"))
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("What‑If Simulator")
    student = st.selectbox("Student", full_req_df["NAME"].unique(), key="sim_student")
    course = st.selectbox("Course to Add/Retake", all_course_cols, key="sim_course")
    grade = st.selectbox("Hypothetical Grade", ["A+","A","A-","B+","B","B-",...,"F"], key="sim_grade")
    if st.button("Simulate"):
        sim_df = full_req_df.copy()
        # naive: find that student row and set sim_course cell to f"{grade} | {target_courses[course]}"
        sim_df.loc[sim_df["NAME"]==student, course] = f"{grade} | {target_courses[course]}"
        credits = sim_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
        sim_df = pd.concat([sim_df, credits], axis=1)
        result = sim_df[sim_df["NAME"]==student][["# of Credits Completed","# Remaining"]].iloc[0]
        st.write(f"After simulation, {student} would have {result['# of Credits Completed']} completed and {result['# Remaining']} remaining.")

# --- End of tabs ---
