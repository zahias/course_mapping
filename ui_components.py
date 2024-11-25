# ui_components.py

import streamlit as st
import pandas as pd

def display_sidebar(default_grading_system):
    st.sidebar.subheader("Customize Target Courses")
    uploaded_courses = st.sidebar.file_uploader("Upload Target Courses (CSV)", type="csv", key='courses')
    if uploaded_courses is not None:
        target_courses_df = pd.read_csv(uploaded_courses)
        if 'Course' in target_courses_df.columns and 'Credits' in target_courses_df.columns:
            target_courses = dict(zip(target_courses_df['Course'].str.upper(), target_courses_df['Credits']))
            st.sidebar.success("Custom target courses loaded.")
        else:
            st.sidebar.error("CSV must contain 'Course' and 'Credits' columns.")
            target_courses = None
    else:
        target_courses = None

    st.sidebar.subheader("Customize Grading System")
    all_possible_grades = default_grading_system['Counted'] + default_grading_system['Not Counted']
    counted_grades = st.sidebar.multiselect(
        "Select Counted Grades",
        options=all_possible_grades,
        default=default_grading_system['Counted'],
        key='grades'
    )
    not_counted_grades = [grade for grade in all_possible_grades if grade not in counted_grades]
    grading_system = {'Counted': counted_grades, 'Not Counted': not_counted_grades}

    st.sidebar.write("**Current Grading System:**")
    st.sidebar.write(f"Counted Grades: {', '.join(grading_system['Counted'])}")
    st.sidebar.write(f"Not Counted Grades: {', '.join(grading_system['Not Counted'])}")

    st.sidebar.subheader("View Options")
    grade_toggle = st.sidebar.checkbox("Show All Grades", value=False, key='grade_toggle')
    completed_toggle = st.sidebar.checkbox("Show Completed/Not Completed Only", value=False, key='completed_toggle')

    return target_courses, grading_system, grade_toggle, completed_toggle

def display_main_interface():
    st.title("Student Progress Report Generator")
    st.write("Upload the student progress report to generate insights.")

def add_sce_fec_selection(extra_courses_df):
    # Ensure 'ID', 'NAME', 'Course', 'Grade' columns are strings
    extra_courses_df['ID'] = extra_courses_df['ID'].astype(str)
    extra_courses_df['NAME'] = extra_courses_df['NAME'].astype(str)
    extra_courses_df['Course'] = extra_courses_df['Course'].astype(str)
    extra_courses_df['Grade'] = extra_courses_df['Grade'].astype(str)

    # Select only relevant columns
    assignment_columns = ['ID', 'NAME', 'Course', 'Grade', 'S.C.E.', 'F.E.C.']
    extra_courses_assignment_df = extra_courses_df[assignment_columns]

    # Use st.data_editor to allow interactive selection
    edited_df = st.data_editor(
        extra_courses_assignment_df,
        num_rows="dynamic",
        use_container_width=True,
        key='extra_courses_editor'
    )

    return edited_df

def display_dataframes(styled_df, intensive_styled_df, extra_courses_df, df):
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])
    with tab1:
        st.subheader("Required Courses Progress Report")
        st.dataframe(styled_df)
        st.markdown("*Note: Courses assigned as S.C.E. or F.E.C. are included in the required courses.*")

    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.dataframe(intensive_styled_df)
        st.markdown("*Note: Intensive courses are displayed here separately.*")

    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.write("These are the extra courses that can be assigned as S.C.E. or F.E.C.:")
        st.dataframe(extra_courses_df)
