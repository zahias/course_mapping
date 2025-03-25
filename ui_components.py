import streamlit as st
import pandas as pd
from config import get_allowed_assignment_types

def display_dataframes(styled_df, intensive_styled_df, extra_courses_df, raw_df):
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])
    with tab1:
        st.subheader("Required Courses Progress Report")
        st.markdown("Courses needed to fulfill the curriculum requirements.")
        st.dataframe(styled_df, use_container_width=True)
        st.markdown("*Courses assigned as special or elective assignments are included here once selected.*")
    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.markdown("These are intensive courses required for the curriculum.")
        st.dataframe(intensive_styled_df, use_container_width=True)
        st.markdown("*Intensive courses are displayed separately.*")
    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.markdown("Courses that are not part of the main or intensive list. They may be assigned as special or elective assignments.")
        st.dataframe(extra_courses_df, use_container_width=True)

def add_assignment_selection(extra_courses_df):
    """
    Displays an inline-editable table for extra courses assignments.
    Uses st.data_editor for real-time editing and validation.
    """
    allowed_assignment_types = get_allowed_assignment_types()
    # Create a DataFrame with columns: ID, NAME, Course, Grade, plus one column per assignment type.
    assignment_columns = ['ID', 'NAME', 'Course', 'Grade'] + allowed_assignment_types
    # Filter extra_courses_df to these columns.
    # (If any column is missing, create it with default False for assignment types.)
    for col in allowed_assignment_types:
        if col not in extra_courses_df.columns:
            extra_courses_df[col] = False

    # Use Streamlit's data_editor which supports inline editing.
    edited_df = st.data_editor(extra_courses_df[assignment_columns],
                               num_rows="dynamic",
                               use_container_width=True,
                               key='extra_courses_editor')
    return edited_df
