import streamlit as st
import pandas as pd
from config import get_default_target_courses, get_intensive_courses

st.title("Customize Courses")
st.markdown("---")

st.write("Upload a custom CSV to define required and intensive courses. The CSV should contain 'Course', 'Credits', and optionally 'Type' (Required or Intensive) and 'Passing Grades' (comma separated). If 'Type' is not provided, all courses are considered Required and default intensive courses are used.")

with st.expander("Course Customization Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)", type="csv", help="Use the template below.")
    if st.button("Download Template", help="Download a CSV template"):
        template_df = pd.DataFrame({
            'Course': ['ENGL201', 'CHEM201', 'INEG200', 'MATH101'],
            'Credits': [3, 3, 3, 3],
            'Type': ['Required', 'Required', 'Intensive', 'Required'],
            'Passing Grades': ['A,A-,B+,B', '', 'A,A-,B+,B', 'A,A-,B+,B,C+']  # example: leave empty to use default
        })
        csv_data = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV Template", data=csv_data, file_name='course_template.csv', mime='text/csv')

if 'raw_df' not in st.session_state:
    st.warning("No data uploaded yet. Please upload data first in 'Upload Data' page.")
else:
    if uploaded_courses is not None:
        custom_df = pd.read_csv(uploaded_courses)
        if 'Course' in custom_df.columns and 'Credits' in custom_df.columns:
            # Store the mapping for target and intensive courses as before
            if 'Type' in custom_df.columns:
                required_df = custom_df[custom_df['Type'].str.lower() == 'required']
                intensive_df = custom_df[custom_df['Type'].str.lower() == 'intensive']
                st.session_state['target_courses'] = dict(zip(required_df['Course'].str.upper(), required_df['Credits']))
                st.session_state['intensive_courses'] = dict(zip(intensive_df['Course'].str.upper(), intensive_df['Credits']))
            else:
                st.session_state['target_courses'] = dict(zip(custom_df['Course'].str.upper(), custom_df['Credits']))
                st.session_state['intensive_courses'] = get_intensive_courses()
            
            # New: Build a mapping of custom passing grades per course.
            custom_passing = {}
            if 'Passing Grades' in custom_df.columns:
                for _, row in custom_df.iterrows():
                    course = row['Course'].strip().upper()
                    passing = row.get('Passing Grades', '')
                    if pd.notna(passing) and passing != '':
                        custom_passing[course] = [grade.strip() for grade in passing.split(',') if grade.strip()]
            st.session_state['custom_passing_grades'] = custom_passing
            
            st.success("Custom courses (and passing grades) loaded from CSV.")
        else:
            st.error("CSV must contain 'Course' and 'Credits' columns.")
    else:
        st.session_state['target_courses'] = get_default_target_courses()
        st.session_state['intensive_courses'] = get_intensive_courses()
        st.info("Using default required and intensive courses.")

    st.success("Courses are now set. Proceed to 'View Reports' to see the processed data.")
