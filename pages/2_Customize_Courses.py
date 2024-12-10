import streamlit as st
import pandas as pd
import os
from config import get_default_target_courses, get_intensive_courses

st.title("Customize Courses")
st.markdown("---")

st.write("Upload a custom CSV to define your required and intensive courses. The CSV should contain 'Course', 'Credits', and optionally 'Type' (Required or Intensive). If 'Type' is not provided, all courses are considered Required and default intensive courses are used.")

with st.expander("Course Customization Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)",
                                        type="csv",
                                        help="Use the template below.")
    # Add a download button for the template
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
    # Process custom courses if provided
    if uploaded_courses is not None:
        custom_df = pd.read_csv(uploaded_courses)
        if 'Course' in custom_df.columns and 'Credits' in custom_df.columns:
            if 'Type' in custom_df.columns:
                required_df = custom_df[custom_df['Type'].str.lower() == 'required']
                intensive_df = custom_df[custom_df['Type'].str.lower() == 'intensive']
                st.session_state['target_courses'] = dict(zip(required_df['Course'].str.upper(), required_df['Credits']))
                st.session_state['intensive_courses'] = dict(zip(intensive_df['Course'].str.upper(), intensive_df['Credits']))
                st.success("Custom required and intensive courses loaded from CSV.")
            else:
                st.session_state['target_courses'] = dict(zip(custom_df['Course'].str.upper(), custom_df['Credits']))
                st.session_state['intensive_courses'] = get_intensive_courses()
                st.info("No 'Type' column found. Using default intensive courses and custom required courses.")
        else:
            st.error("CSV must contain 'Course' and 'Credits' columns.")
    else:
        # No custom upload, use defaults
        st.session_state['target_courses'] = get_default_target_courses()
        st.session_state['intensive_courses'] = get_intensive_courses()
        st.info("Using default required and intensive courses.")

    st.success("Courses are now set. Proceed to 'View Reports' to see the processed data.")
