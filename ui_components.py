import streamlit as st
import pandas as pd

def display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df):
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])
    with tab1:
        st.subheader("Required Courses Progress Report")
        st.markdown("Courses needed to fulfill the curriculum requirements.")
        st.dataframe(styled_df, use_container_width=True)
        st.markdown("*Courses assigned as S.C.E. or F.E.C. are included here once selected.*")

    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.markdown("These are intensive courses required for the curriculum.")
        st.dataframe(intensive_styled_df, use_container_width=True)
        st.markdown("*Intensive courses are displayed separately.*")

    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.markdown("Courses that are not part of the main or intensive list. They may be assigned as S.C.E. or F.E.C.")
        st.dataframe(extra_courses_df, use_container_width=True)

def add_sce_fec_selection(extra_courses_df):
    assignment_columns = ['ID', 'NAME', 'Course', 'Grade', 'S.C.E.', 'F.E.C.']
    extra_courses_assignment_df = extra_courses_df[assignment_columns]

    st.write("Below are extra courses. Check the boxes for S.C.E. or F.E.C. as needed:")
    edited_df = st.data_editor(
        extra_courses_assignment_df,
        num_rows="dynamic",
        use_container_width=True,
        key='extra_courses_editor'
    )
    return edited_df
