import streamlit as st
import pandas as pd
from config import get_default_target_courses, get_intensive_courses

st.title("Customize Courses")
st.markdown("---")

st.write("Upload a custom CSV to define required and intensive courses. The CSV should contain 'Course', 'Credits', and optionally 'Type' (Required or Intensive). If 'Type' is not provided, all courses are considered Required and default intensive courses are used.")

with st.expander("Course Customization Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)",
                                        type="csv",
                                        help="Use the template below.")
    if st.button("Download Template", help="Download a CSV template to define required and intensive courses."):
        template_df = pd.DataFrame({
            'Course': ['ENGL201', 'CHEM201', 'INEG200', 'MATH101'],
            'Credits': [3, 3, 3, 3],
            'Type': ['Required', 'Required', 'Intensive', 'Required']
        })
        csv_data = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV Template",
            data=csv_data,
            file_name='course_template.csv',
            mime='text/csv'
        )

if 'raw_df' not in st.session_state:
    st.warning("No data uploaded yet. Please upload data first in 'Upload Data' page.")
else:
    target_courses = st.session_state.get('target_courses', get_default_target_courses())
    intensive_courses = st.session_state.get('intensive_courses', get_intensive_courses())

    st.markdown("### Intensive Courses")
    intensive_courses_df = pd.DataFrame(
        list(intensive_courses.items()), columns=["Course", "Credits"]
    )
    st.dataframe(intensive_courses_df.drop(columns=["Credits"]), use_container_width=True)
