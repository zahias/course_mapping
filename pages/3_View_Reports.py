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

# Ensure raw data exists
if "raw_df" not in st.session_state:
    st.warning("No data available. Please upload data in 'Upload Data' and configure in 'Customize Courses'.")
    st.stop()

raw_df = st.session_state["raw_df"].copy()
target_courses = st.session_state["target_courses"]
intensive_courses = st.session_state["intensive_courses"]
per_student_assignments = load_assignments()

# Sidebar: Advanced Filters & Saved Views
st.sidebar.header("Advanced Filters & Views")

# Load or Save named views
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

# Year & Semester filters from raw_df
years = sorted(raw_df["Year"].astype(int).unique())
year_min, year_max = st.sidebar.slider(
    "Year Range",
    min_value=int(min(years)), max_value=int(max(years)),
    value=(loaded.get("year_min", min(years)), loaded.get("year_max", max(years)))
)
semesters = ["Spring", "Summer", "Fall"]
semesters_sel = st.sidebar.multiselect(
    "Semesters",
    semesters,
    default=loaded.get("semesters", semesters)
)

# Credits‐remaining threshold will apply after pivot
max_rem = None  # placeholder

# Extra courses filter by assignment type
assign_types = get_allowed_assignment_types()
atype_sel = st.sidebar.multiselect(
    "Assignment Types (Extra Courses)",
    assign_types,
    default=loaded.get("atype_sel", assign_types)
)

# Column visibility & ordering
all_course_cols = list(target_courses.keys())
col_order = st.sidebar.multiselect(
    "Show & Order Required Course Columns",
    options=all_course_cols,
    default=loaded.get("col_order", all_course_cols)
)

# Save current view
view_name = st.sidebar.text_input("Save Current View As", key="view_name")
if st.sidebar.button("Save View"):
    st.session_state["saved_views"][view_name] = {
        "year_min": year_min,
        "year_max": year_max,
        "semesters": semesters_sel,
        "atype_sel": atype_sel,
        "col_order": col_order
    }
    st.sidebar.success(f"View '{view_name}' saved.")

# --- APPLY RAW FILTERS ---
filtered_df = raw_df[
    raw_df["Year"].astype(int).between(year_min, year_max) &
    raw_df["Semester"].isin(semesters_sel)
]

# Load equivalent courses mapping
eq_map = {}
try:
    creds = authenticate_google_drive()
    service = build("drive", "v3", credentials=creds)
    fid = search_file(service, "equivalent_courses.csv")
    if fid:
        download_file(service, fid, "equivalent_courses.csv")
        eq_df = pd.read_csv("equivalent_courses.csv")
        eq_map = read_equivalent_courses(eq_df)
except:
    pass

# Process with filtered raw data
full_req_df, full_int_df, extra_courses_df, _ = process_progress_report(
    filtered_df, target_courses, intensive_courses, per_student_assignments, eq_map
)

# Append credit summaries
credits_req = full_req_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
full_req_df = pd.concat([full_req_df, credits_req], axis=1)
credits_int = full_int_df.apply(lambda r: calculate_credits(r, intensive_courses), axis=1)
full_int_df = pd.concat([full_int_df, credits_int], axis=1)

# Now that # Remaining exists, define the rem filter
max_rem = int(full_req_df["# Remaining"].max())
rem_threshold = st.sidebar.slider(
    "Max Credits Remaining",
    min_value=0, max_value=max_rem,
    value=loaded.get("rem_threshold", max_rem)
)
# Apply remaining‐credits filter
full_req_df = full_req_df[full_req_df["# Remaining"] <= rem_threshold]
# Mirror filter on full_int_df by index
full_int_df = full_int_df.loc[full_req_df.index]

# Filter extra courses
extra_courses_df = extra_courses_df[
    extra_courses_df["assignment_type"].isin(atype_sel)
]

# --- MAIN TAB LAYOUT ---
tabs = st.tabs([
    "Required Courses",
    "Intensive Courses",
    "Extra Courses",
    "Trend Chart",
    "Heatmap Calendar",
    "What‑If Simulator"
])

with tabs[0]:
    st.subheader("Required Courses")
    # Toggles for Show All / Completed‐only can remain here if desired...
    display_df = full_req_df[["ID", "NAME"] + col_order + ["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]]
    display_dataframes(
        display_df.style.applymap(cell_color, subset=pd.IndexSlice[:, col_order]),
        None,
        None,
        filtered_df  # passing original filtered raw for context
    )

with tabs[1]:
    st.subheader("Intensive Courses")
    display_df = full_int_df[["ID", "NAME"] + list(intensive_courses.keys()) + ["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]]
    display_dataframes(
        None,
        display_df.style.applymap(cell_color, subset=pd.IndexSlice[:, list(intensive_courses.keys())]),
        None,
        filtered_df
    )

with tabs[2]:
    st.subheader("Extra Courses")
    st.dataframe(extra_courses_df, use_container_width=True)

with tabs[3]:
    st.subheader("Trend Chart")
    student = st.selectbox("Select Student", filtered_df["NAME"].unique())
    stud = filtered_df[filtered_df["NAME"] == student].copy()
    stud["Sem_Order"] = stud["Semester"].map({"Spring":1,"Summer":2,"Fall":3})
    stud = stud.sort_values(["Year","Sem_Order"])
    # Map grades to numeric for y-axis
    grade_map = {g:i for i,g in enumerate(
        ["F","D-","D","D+","C-","C","C+","B-","B","B+","A-","A","A+"], 1
    )}
    stud["Grade_Num"] = stud["Grade"].map(lambda g: grade_map.get(g, None))
    fig = px.line(
        stud,
        x=stud["Year"].astype(str) + " " + stud["Semester"],
        y="Grade_Num",
        markers=True,
        title=f"Grade Progression for {student}"
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=list(grade_map.values()),
        ticktext=list(grade_map.keys())
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.subheader("Heatmap Calendar")
    # Count passes per semester
    heat = filtered_df.copy()
    # Mark pass if grade is in a passing list for that course
    def is_pass(r):
        pg = target_courses.get(r["Course"], {}).get("PassingGrades","")
        return r["Grade"] in [g.strip() for g in pg.split(",")]
    heat["Passed"] = heat.apply(is_pass, axis=1)
    summary = heat.groupby(["Year","Semester"])["Passed"].sum().unstack().fillna(0)
    fig = px.imshow(
        summary,
        labels=dict(x="Semester", y="Year", color="Courses Passed"),
        title="Courses Passed Heatmap"
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("What‑If Simulator")
    student = st.selectbox("Student", filtered_df["NAME"].unique(), key="sim_stud")
    course = st.selectbox("Course to Add/Retake", list(target_courses.keys()), key="sim_course")
    grade = st.selectbox("Hypothetical Grade", list(grade_map.keys()), key="sim_grade")
    if st.button("Simulate"):
        sim_df = full_req_df.copy()
        sim_df.loc[sim_df["NAME"] == student, course] = f"{grade} | {target_courses[course]['Credits']}"
        sim_credits = sim_df.apply(lambda r: calculate_credits(r, target_courses), axis=1)
        sim_df = pd.concat([sim_df, sim_credits], axis=1)
        res = sim_df[sim_df["NAME"] == student].iloc[0]
        st.write(f"After simulation, {student} would have **{res['# of Credits Completed']}** completed and **{res['# Remaining']}** remaining.")

# (Assignment section and Download button preserved below tabs if needed...)

