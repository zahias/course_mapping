import streamlit as st
import pandas as pd
import os
from config import get_default_target_courses, get_intensive_courses

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define courses configuration. The CSV should contain the following columns: "
    "'Course', 'Credits', 'Type' (Required or Intensive), and 'PassingGrade'. "
    "The 'PassingGrade' column defines the acceptable passing grade(s) for the course (e.g., 'B' or 'A+,A,A-')."
)

with st.expander("Course Customization Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)", type="csv", help="Use the template below.")
    
    if st.button("Download Template", help="Download a CSV template for courses configuration."):
        template_df = pd.DataFrame({
            'Course': ['ENGL201', 'CHEM201', 'INEG200', 'MATH101'],
            'Credits': [3, 3, 3, 3],
            'Type': ['Required', 'Required', 'Intensive', 'Required'],
            'PassingGrade': ['D-', 'D-', 'A+', 'D-']
        })
        csv_data = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download Courses Template", data=csv_data, file_name='courses_template.csv', mime='text/csv')
    
    # Try loading the configuration from the uploaded file or from a local copy
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
        except Exception as e:
            st.error(f"Error reading the uploaded file: {e}")
            courses_df = None
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    if courses_df is not None:
        required_cols = {'Course', 'Credits', 'Type', 'PassingGrade'}
        if required_cols.issubset(courses_df.columns):
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            # Separate required (target) and intensive courses:
            required_df = courses_df[courses_df['Type'].str.lower() == 'required']
            intensive_df = courses_df[courses_df['Type'].str.lower() == 'intensive']
            target_courses = {}
            for _, row in required_df.iterrows():
                target_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrade": row['PassingGrade'].strip().upper()
                }
            intensive_courses = {}
            for _, row in intensive_df.iterrows():
                intensive_courses[row['Course']] = {
                    "Credits": row['Credits'],
                    "PassingGrade": row['PassingGrade'].strip().upper()
                }
            st.session_state['target_courses'] = target_courses
            st.session_state['intensive_courses'] = intensive_courses
            st.success("Courses configuration loaded successfully.")
        else:
            st.error("CSV must contain the columns: 'Course', 'Credits', 'Type', and 'PassingGrade'.")
    else:
        st.info("No courses configuration available. Please upload a CSV file for courses configuration.")

with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types that can be assigned to courses. For example, enter S.C.E, F.E.C, ARAB201 to allow assignments for those courses.")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
