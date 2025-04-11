import streamlit as st
import pandas as pd

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define courses configuration. The CSV should contain the following columns: "
    "'Course', 'Credits', 'Type' (Required or Intensive), and 'PassingGrades'. "
    "The 'PassingGrades' column should list all grades that count as passing for that course, "
    "separated by commas. For example: A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T"
)

uploaded_courses = st.file_uploader("Upload Courses Configuration (CSV)", type="csv")

if uploaded_courses is not None:
    courses_df = pd.read_csv(uploaded_courses)
    required_cols = {'Course', 'Credits', 'Type', 'PassingGrades'}
    if required_cols.issubset(courses_df.columns):
        courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
        required_df = courses_df[courses_df['Type'].str.lower() == 'required']
        intensive_df = courses_df[courses_df['Type'].str.lower() == 'intensive']
        target_courses = {}
        for _, row in required_df.iterrows():
            target_courses[row['Course']] = {
                "Credits": row['Credits'],
                "PassingGrades": row['PassingGrades']
            }
        intensive_courses = {}
        for _, row in intensive_df.iterrows():
            intensive_courses[row['Course']] = {
                "Credits": row['Credits'],
                "PassingGrades": row['PassingGrades']
            }
        st.session_state['target_courses'] = target_courses
        st.session_state['intensive_courses'] = intensive_courses
        st.success("Courses configuration loaded successfully.")
    else:
        st.error("CSV must contain the columns: 'Course', 'Credits', 'Type', and 'PassingGrades'.")
else:
    st.info("Using previously loaded courses configuration (if available).")
