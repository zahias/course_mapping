import streamlit as st
import pandas as pd
import plotly.express as px
from data_processing import process_progress_report, calculate_credits, read_equivalent_courses
from datetime import datetime
import os

st.title("Analysis Report")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("No progress report data available. Please upload data in the Upload Data page.")
else:
    df = st.session_state['raw_df']
    target_courses = st.session_state.get('target_courses', {})
    intensive_courses = st.session_state.get('intensive_courses', {})

    st.header("Grade Distribution by Course")
    if target_courses:
        for course in target_courses:
            course_df = df[df["Course"].str.upper() == course.upper()]
            if course_df.empty:
                continue
            grade_counts = course_df["Grade"].value_counts().reset_index()
            grade_counts.columns = ["Grade", "Count"]
            fig = px.bar(grade_counts, x="Grade", y="Count", title=f"Grade Distribution for {course}")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No target courses configuration available.")

    st.header("Trend Analysis Over Time")
    trend_df = df.groupby(["Year", "Semester"]).size().reset_index(name="Count")
    trend_df["YearSemester"] = trend_df["Year"].astype(str) + " " + trend_df["Semester"]
    fig2 = px.line(trend_df, x="YearSemester", y="Count", markers=True, title="Course Records Over Time")
    st.plotly_chart(fig2, use_container_width=True)

    st.header("Cohort Comparison by Year")
    df["Cohort"] = df["ID"].astype(str).str[:4]
    cohort_df = df.groupby("Cohort").size().reset_index(name="Student Count")
    fig3 = px.bar(cohort_df, x="Cohort", y="Student Count", title="Number of Students by Cohort")
    st.plotly_chart(fig3, use_container_width=True)

    st.header("At-Risk Student Identification")
    if target_courses:
        req_df, _, _, _ = process_progress_report(df, target_courses, intensive_courses)
        credits_df = req_df.apply(lambda row: calculate_credits(row, target_courses), axis=1)
        req_df = pd.concat([req_df, credits_df], axis=1)
        if "Total Credits" in req_df.columns and "Total Credits" in req_df.columns:
            req_df["Completion Ratio"] = req_df["# of Credits Completed"] / req_df["Total Credits"]
            at_risk_df = req_df[req_df["Completion Ratio"] < 0.5]
            st.write("At-Risk Students (Completion Ratio < 50%):")
            st.dataframe(at_risk_df[["ID", "NAME", "# of Credits Completed", "Total Credits", "Completion Ratio"]])
            fig4 = px.histogram(at_risk_df, x="Completion Ratio", nbins=10, title="Completion Ratio Distribution (At-Risk Students)")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Insufficient credit data to identify at-risk students.")
    else:
        st.info("No target courses configuration available.")

    st.header("Correlation Analysis")
    if target_courses:
        req_df, _, _, _ = process_progress_report(df, target_courses, intensive_courses)
        if "Total Credits" in req_df.columns:
            corr_df = req_df[["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]]
            fig5 = px.imshow(corr_df.corr(), text_auto=True, title="Correlation Heatmap of Credit Metrics")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Insufficient credit data for correlation analysis.")
    else:
        st.info("No target courses configuration available.")
