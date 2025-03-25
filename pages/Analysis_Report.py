import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.title("Analysis Report")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("No progress report data available. Please upload data in the Upload Data page.")
else:
    df = st.session_state['raw_df']

    st.header("Grade Distribution by Course")
    courses = sorted(df["Course"].str.upper().unique())
    selected_course = st.selectbox("Select a Course", courses)
    course_df = df[df["Course"].str.upper() == selected_course]
    if not course_df.empty:
        # Create a histogram showing frequency of each grade
        grade_counts = course_df["Grade"].value_counts().reset_index()
        grade_counts.columns = ["Grade", "Count"]
        fig = px.bar(grade_counts, x="Grade", y="Count", title=f"Grade Distribution for {selected_course}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected course.")

    st.header("Cohort Comparison by Year")
    # Extract cohort as first 4 digits of ID, then count unique IDs.
    df["Cohort"] = df["ID"].astype(str).str[:4]
    unique_ids = df.drop_duplicates(subset=["ID"])
    cohort_df = unique_ids.groupby("Cohort").size().reset_index(name="Student Count")
    fig2 = px.bar(cohort_df, x="Cohort", y="Student Count", title="Unique Student Count by Cohort")
    st.plotly_chart(fig2, use_container_width=True)

    st.header("Overall Course Enrollment by Semester")
    # Count unique student IDs per semester.
    enroll_df = df.groupby(["Year", "Semester"])["ID"].nunique().reset_index(name="Unique Students")
    enroll_df["Year-Semester"] = enroll_df["Year"].astype(str) + " " + enroll_df["Semester"]
    fig3 = px.line(enroll_df, x="Year-Semester", y="Unique Students", markers=True, title="Unique Student Enrollment by Semester")
    st.plotly_chart(fig3, use_container_width=True)

    st.header("Average Grade Frequency (by Grade)")
    # Let user choose a course for which to see average grade frequencies across all students.
    selected_course2 = st.selectbox("Select a Course for Average Grade Frequency", courses, key="avg_course")
    course_df2 = df[df["Course"].str.upper() == selected_course2]
    if not course_df2.empty:
        # Count grade occurrences
        grade_freq = course_df2["Grade"].value_counts().reset_index()
        grade_freq.columns = ["Grade", "Frequency"]
        fig4 = px.pie(grade_freq, names="Grade", values="Frequency", title=f"Grade Frequency for {selected_course2}")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No data available for the selected course.")
