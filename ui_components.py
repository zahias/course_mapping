import streamlit as st
import pandas as pd
from config import get_allowed_assignment_types

def display_dataframes(styled_df, intensive_styled_df, extra_courses_df, raw_df):
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])
    with tab1:
        st.subheader("Required Courses Progress Report")
        st.dataframe(styled_df, use_container_width=True)
    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.dataframe(styled_intensive_df, use_container_width=True)
    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.dataframe(extra_courses_df, use_container_width=True)

def add_assignment_selection(extra_courses_df):
    """
    Displays an inline-editable table for extra courses assignments using st.data_editor.
    Uses a unique key to avoid duplicate element key errors.
    """
    allowed_assignment_types = get_allowed_assignment_types()
    assignment_columns = ['ID', 'NAME', 'Course', 'Grade'] + allowed_assignment_types
    for col in allowed_assignment_types:
        if col not in extra_courses_df.columns:
            extra_courses_df[col] = False
    edited_df = st.data_editor(extra_courses_df[assignment_columns],
                               num_rows="dynamic",
                               use_container_width=True,
                               key='assignment_editor')
    return edited_df
