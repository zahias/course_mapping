import streamlit as st
import pandas as pd

st.title("Student Profiles")
st.markdown("---")

if 'raw_df' not in st.session_state:
    st.warning("No data available. Please upload and process data first.")
else:
    df = st.session_state['raw_df'].copy()

    if 'ID' not in df.columns or 'NAME' not in df.columns:
        st.error("Data does not contain 'ID' or 'NAME' columns.")
        st.stop()

    df['ID'] = df['ID'].astype(str)
    df['NAME'] = df['NAME'].astype(str).str.strip()

    if 'Year' not in df.columns or 'Semester' not in df.columns:
        st.error("Data does not contain Year or Semester columns.")
        st.stop()

    df = df.dropna(subset=['Year', 'Semester'])
    if df.empty:
        st.warning("No valid records after dropping missing Year/Semester.")
        st.stop()

    if df['Year'].notnull().all():
        df['Year'] = df['Year'].astype(float).astype(int, errors='ignore')
    else:
        df = df[df['Year'].notnull()]
        if df.empty:
            st.warning("No valid year data available.")
            st.stop()
        df['Year'] = df['Year'].astype(float).astype(int, errors='ignore')

    semester_order = {"Spring": 1, "Summer": 2, "Fall": 3}
    df['Sem_Order'] = df['Semester'].map(semester_order)
    df = df.sort_values(by=['ID', 'Year', 'Sem_Order'])

    students = df[['ID', 'NAME']].drop_duplicates()
    if students.empty:
        st.error("No student data found after processing.")
        st.stop()

    selected_student = st.selectbox(
        "Select a Student by Name", 
        students['NAME'].unique(),
        help="Select a student to view their academic journey."
    )

    matching_students = students[students['NAME'] == selected_student]
    if matching_students.empty:
        st.warning(f"No ID found for the selected student '{selected_student}'.")
        st.stop()

    student_id = matching_students['ID'].iloc[0]
    student_data = df[df['ID'] == student_id].copy()

    if student_data.empty:
        st.warning(f"No data found for student: {selected_student} (ID: {student_id}).")
        st.write("Check the raw data to ensure this student has entries.")
        st.stop()

    st.markdown(f"**Academic Journey for {selected_student} (ID: {student_id}):**")

    def highlight_nulls(val):
        if pd.isna(val):
            return 'background-color: pink'
        return ''

    semesters = st.multiselect(
        "Filter by Semester",
        options=["Spring", "Summer", "Fall"],
        default=["Spring", "Summer", "Fall"],
        help="Select which semesters to display."
    )

    min_year_overall = int(student_data['Year'].min())
    max_year_overall = int(student_data['Year'].max())
    year_range = st.slider(
        "Select Year Range",
        min_value=min_year_overall,
        max_value=max_year_overall,
        value=(min_year_overall, max_year_overall),
        help="Drag the sliders to limit the displayed years."
    )

    search_course = st.text_input(
        "Search by Course",
        help="Type to filter courses by name. Leave blank to show all."
    )

    filtered_data = student_data[
        (student_data['Semester'].isin(semesters)) &
        (student_data['Year'].between(year_range[0], year_range[1]))
    ]

    if search_course:
        filtered_data = filtered_data[filtered_data['Course'].str.contains(search_course, case=False, na=False)]

    st.markdown("**Filtered Academic Journey:**")
    st.markdown("_Below is the filtered set of courses based on your criteria._")

    st.dataframe(
        filtered_data[['Year', 'Semester', 'Course', 'Grade']].style.applymap(highlight_nulls),
        use_container_width=True
    )

    if filtered_data.empty:
        st.info("No data matches your filters.")
