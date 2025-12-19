import streamlit as st
import pandas as pd
from io import BytesIO
from gpa_utils import calculate_gpa, get_gpa_summary
from chart_utils import create_progress_timeline, create_grade_distribution_chart, create_completion_heatmap

# NOTE:
# - This page reads the parsed progress DataFrame directly from session_state,
#   which is populated in `main.py` when you upload or reload the progress report.
# - No additional upload is needed here.


# ---------- Helpers ----------

def _require_major_and_data():
    """Ensure a major is selected and raw df is present in session_state."""
    if "selected_major" not in st.session_state or not st.session_state["selected_major"]:
        st.warning("Please go to the **main page** and select a Major.")
        st.stop()

    major = st.session_state["selected_major"]
    key = f"{major}_raw_df"
    if key not in st.session_state:
        st.info("No progress report found in memory. "
                "Please upload or reload the progress file from the **main page**.")
        st.stop()

    df = st.session_state[key]
    if df is None or df.empty:
        st.info("The loaded progress report appears to be empty. "
                "Please upload or reload the progress file from the **main page**.")
        st.stop()
    return major, df


@st.cache_data(show_spinner=False)
def _prepare_student_progress_df(df: pd.DataFrame):
    """
    Clean and prepare the long-format progress df:
    Ensures consistent casing and a sortable term order column.
    Expected input columns: ['ID','NAME','Course','Grade','Year','Semester']
    """
    work = df.copy()

    # Clean common columns
    for col in ["Course", "Grade"]:
        if col in work.columns:
            work[col] = work[col].astype(str).str.strip()

    # Normalize Semester and Year text
    if "Semester" in work.columns:
        work["Semester"] = work["Semester"].astype(str).str.strip().str.title()
    if "Year" in work.columns:
        work["Year"] = work["Year"].astype(str).str.strip()

    # Map a term sort order (Spring < Summer < Fall by default)
    term_order_map = {"Spring": 1, "Summer": 2, "Fall": 3}
    work["TermOrder"] = work["Semester"].map(lambda s: term_order_map.get(str(s).title(), 99))

    # Make a combined term label like "Fall-2024"
    work["Term"] = work["Semester"].fillna("") + "-" + work["Year"].fillna("")

    # Sort by (Year asc, TermOrder asc), then Course
    # Convert Year to numeric where possible for proper sorting
    def _to_int(x):
        try:
            return int(str(x))
        except Exception:
            return 0
    work["_YearInt"] = work["Year"].apply(_to_int)
    work = work.sort_values(by=["_YearInt", "TermOrder", "Course"], ascending=[True, True, True]).reset_index(drop=True)

    # Columns for display
    display_cols = ["ID", "NAME", "Year", "Semester", "Course", "Grade"]
    display_df = work[display_cols].copy()

    return display_df


def _download_student_progress_excel(student_df: pd.DataFrame, student_name: str, student_id: str) -> BytesIO:
    """Create an Excel file for a single student's progress (sorted by term)."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Order columns nicely
        cols = ["Year", "Semester", "Course", "Grade"]
        to_write = student_df[cols].copy().reset_index(drop=True)
        to_write.to_excel(writer, sheet_name="Progress", index=False)

        # Add a front sheet with student info
        info_df = pd.DataFrame({
            "Field": ["Student Name", "Student ID", "Total Courses"],
            "Value": [student_name, student_id, len(to_write)]
        })
        info_df.to_excel(writer, sheet_name="Info", index=False)

    output.seek(0)
    return output


def _download_all_progress_excel(filtered_df: pd.DataFrame) -> BytesIO:
    """Create an Excel with one sheet per student based on filtered view."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sid, g in filtered_df.groupby("ID"):
            sname = g["NAME"].iloc[0]
            # sanitize sheet name
            sheet_name = f"{str(sname)[:28]}"
            # Order columns
            cols = ["Year", "Semester", "Course", "Grade"]
            g[cols].to_excel(writer, sheet_name=sheet_name or "Student", index=False)
    output.seek(0)
    return output


# ---------- UI ----------

st.title("Student Progress")

# Ensure we have a major and data in memory
major, long_df = _require_major_and_data()

# Prepare standardized student progress dataframe (cached)
progress_df = _prepare_student_progress_df(long_df)

# Sidebar filters (keep the page clean & responsive)
with st.sidebar:
    st.header("Filters")

    # Student selector
    student_options = (progress_df["ID"].astype(str) + " - " + progress_df["NAME"]).unique().tolist()
    student_options = sorted(student_options, key=lambda x: x.split(" - ")[-1])  # sort by name
    selected_student_option = st.selectbox("Select Student", ["— All Students —"] + student_options, index=0)

    # Year filter (multi)
    years = sorted(progress_df["Year"].unique(), key=lambda x: (str(x)))
    selected_years = st.multiselect("Filter by Year", options=years, default=years)

    # Course name search
    course_search = st.text_input("Search Course Code/Name", value="")

    # Grade filter (multi)
    grades = sorted(progress_df["Grade"].astype(str).unique())
    selected_grades = st.multiselect("Filter by Grade", options=grades, default=grades)

    st.caption("Tip: Use the main page to upload or reload the progress report at any time; this page updates automatically.")
    
    # Chart toggle
    show_charts = st.checkbox("Show Charts", value=False, help="Display visualizations of student progress")

# Apply filters
filtered = progress_df.copy()

# Student filter
if selected_student_option != "— All Students —":
    selected_id = selected_student_option.split(" - ")[0]
    filtered = filtered[filtered["ID"].astype(str) == selected_id]

# Year filter
if selected_years:
    filtered = filtered[filtered["Year"].isin(selected_years)]

# Course search
if course_search.strip():
    q = course_search.strip().lower()
    filtered = filtered[filtered["Course"].str.lower().str.contains(q)]

# Grade filter
if selected_grades:
    filtered = filtered[filtered["Grade"].astype(str).isin(selected_grades)]

# Layout: top KPIs (only for a single student selection)
if selected_student_option != "— All Students —" and not filtered.empty:
    sid = filtered["ID"].iloc[0]
    sname = filtered["NAME"].iloc[0]
    st.subheader(f"Progress for: {sname} (ID: {sid})")

    # Try to get course credits from target courses if available
    course_credits_dict = None
    major = st.session_state.get("selected_major")
    if major:
        target_key = f"{major}_target_courses"
        intensive_key = f"{major}_intensive_courses"
        if target_key in st.session_state:
            course_credits_dict = st.session_state[target_key].copy()
        if intensive_key in st.session_state and course_credits_dict:
            course_credits_dict.update(st.session_state[intensive_key])
    
    # Calculate GPA for this student
    student_gpa = None
    if course_credits_dict:
        try:
            gpa_series = calculate_gpa(filtered, grade_col="Grade", course_credits_dict=course_credits_dict)
            if sid in gpa_series.index and gpa_series[sid] is not None:
                student_gpa = gpa_series[sid]
        except Exception:
            pass  # Silently fail if GPA calculation fails
    
    # Simple KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(filtered))
    col2.metric("Unique Courses", filtered["Course"].nunique())
    col3.metric("Years Covered", filtered["Year"].nunique())
    if student_gpa is not None:
        col4.metric("GPA", f"{student_gpa:.2f}", help="Calculated based on completed courses with credit hours")
    else:
        col4.metric("GPA", "N/A", help="GPA calculation requires course credit information. Configure courses first.")

# Calculate and display GPA summary if viewing all students
if selected_student_option == "— All Students —" and not filtered.empty:
    # Try to get course credits
    course_credits_dict = None
    major = st.session_state.get("selected_major")
    if major:
        target_key = f"{major}_target_courses"
        intensive_key = f"{major}_intensive_courses"
        if target_key in st.session_state:
            course_credits_dict = st.session_state[target_key].copy()
        if intensive_key in st.session_state and course_credits_dict:
            course_credits_dict.update(st.session_state[intensive_key])
    
    # Calculate GPAs for all students
    if course_credits_dict:
        try:
            gpa_series = calculate_gpa(filtered, grade_col="Grade", course_credits_dict=course_credits_dict)
            gpa_summary = get_gpa_summary(pd.DataFrame({"GPA": gpa_series}))
            
            if gpa_summary:
                st.markdown("### GPA Summary")
                gpa_col1, gpa_col2, gpa_col3, gpa_col4, gpa_col5 = st.columns(5)
                gpa_col1.metric("Average GPA", f"{gpa_summary.get('mean', 'N/A'):.2f}" if gpa_summary.get('mean') else "N/A")
                gpa_col2.metric("Median GPA", f"{gpa_summary.get('median', 'N/A'):.2f}" if gpa_summary.get('median') else "N/A")
                gpa_col3.metric("Highest GPA", f"{gpa_summary.get('max', 'N/A'):.2f}" if gpa_summary.get('max') else "N/A")
                gpa_col4.metric("Lowest GPA", f"{gpa_summary.get('min', 'N/A'):.2f}" if gpa_summary.get('min') else "N/A")
                gpa_col5.metric("Students", gpa_summary.get('count', 0))
        except Exception:
            pass  # Silently fail if GPA calculation fails

# Display charts if enabled
if show_charts and not filtered.empty:
    st.markdown("### Visualizations")
    
    if selected_student_option != "— All Students —":
        # Single student charts
        sid = filtered["ID"].iloc[0]
        sname = filtered["NAME"].iloc[0]
        
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            timeline_fig = create_progress_timeline(filtered, student_id=str(sid), student_name=sname)
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        with chart_col2:
            grade_fig = create_grade_distribution_chart(filtered, student_id=str(sid))
            st.plotly_chart(grade_fig, use_container_width=True)
        
        # Completion heatmap
        all_courses = sorted(filtered["Course"].unique().tolist())
        if all_courses:
            heatmap_fig = create_completion_heatmap(filtered, all_courses, student_id=str(sid))
            st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        # All students - show grade distribution
        grade_fig = create_grade_distribution_chart(filtered)
        st.plotly_chart(grade_fig, use_container_width=True)

# Display table
st.markdown("### Progress Table")
# Reorder columns for readability
display_cols = ["ID", "NAME", "Year", "Semester", "Course", "Grade"]
st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    height=500
)

# Grouped view toggle (by Semester-Year and Course list)
with st.expander("Grouped View (Semester-Year → Courses)"):
    if filtered.empty:
        st.info("No data for the selected filters.")
    else:
        grouped = (
            filtered
            .assign(Semester_Year=filtered["Semester"] + "-" + filtered["Year"])
            .groupby(["ID", "NAME", "Semester_Year"], as_index=False)
            .agg({
                "Course": lambda x: ", ".join(sorted(x.unique())),
                "Grade": lambda x: ", ".join(x.astype(str))
            })
            .sort_values(by=["NAME", "Semester_Year"])
        )
        st.dataframe(grouped, use_container_width=True)

# Downloads
st.markdown("### Download")
c1, c2 = st.columns(2)
with c1:
    if selected_student_option != "— All Students —" and not filtered.empty:
        sid = filtered["ID"].iloc[0]
        sname = filtered["NAME"].iloc[0]
        # Student-only Excel
        student_xlsx = _download_student_progress_excel(filtered, sname, str(sid))
        st.download_button(
            "Download Selected Student (Excel)",
            data=student_xlsx.getvalue(),
            file_name=f"{sname.replace(' ','_')}_Progress.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.caption("Select an individual student to enable the single-student Excel export.")

with c2:
    if not filtered.empty:
        all_xlsx = _download_all_progress_excel(filtered)
        st.download_button(
            "Download Filtered View (All Students, Excel)",
            data=all_xlsx.getvalue(),
            file_name="Filtered_Student_Progress.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.caption("Adjust filters to enable the multi-student Excel export.")
