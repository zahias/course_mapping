import streamlit as st
import pandas as pd
from google_drive_utils import authenticate_google_drive, search_file, download_file, update_file, upload_file
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define your courses configuration. The CSV must contain the following columns: "
    "'Course', 'Credits', 'CountedGrades' and optionally 'Type' (e.g., Required or Intensive). "
    "The 'CountedGrades' column should list, separated by commas, the grades that count as passing for that course."
)

# Place the Equivalent Courses expander at the top level (not nested)
with st.expander("Equivalent Courses", expanded=True):
    if st.button("Reload Equivalent Courses", help="Reload equivalent courses mapping from Google Drive"):
        try:
            creds = authenticate_google_drive()
            service = build('drive', 'v3', credentials=creds)
            file_id = search_file(service, "equivalent_courses.csv")
            if file_id:
                download_file(service, file_id, "equivalent_courses.csv")
                st.success("Equivalent courses reloaded successfully from Google Drive.")
            else:
                st.error("Equivalent courses file not found on Google Drive.")
        except Exception as e:
            st.error(f"Error reloading equivalent courses: {e}")

with st.expander("Course Customization Options", expanded=True):
    uploaded_courses = st.file_uploader("Upload Custom Courses (CSV)", type="csv", help="Use the template below.")
    
    if st.button("Download Template", help="Download a CSV template for courses configuration."):
        template_df = pd.DataFrame({
            'Course': ['ENGL201', 'CHEM201', 'ARAB201', 'MATH101'],
            'Credits': [3, 3, 3, 3],
            'CountedGrades': [
                'A, A-, B+, B, B-, C+',
                'A, A-, B+, B, B-',
                'A, A-',
                'A, A-, B+, B, B-, C+'
            ],
            'Type': ['Required', 'Required', 'Required', 'Required']  # or 'Intensive'
        })
        csv_data = template_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV Template", data=csv_data, file_name='courses_template.csv', mime='text/csv')
    
    # Process uploaded file or load from local if available.
    if uploaded_courses is not None:
        try:
            custom_df = pd.read_csv(uploaded_courses)
            # Save locally
            custom_df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                folder_id = None
                file_id = search_file(service, "courses_config.csv", folder_id=folder_id)
                if file_id:
                    update_file(service, file_id, "courses_config.csv")
                    st.info("Courses configuration updated on Google Drive.")
                else:
                    upload_file(service, "courses_config.csv", "courses_config.csv", folder_id=folder_id)
                    st.info("Courses configuration uploaded to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing courses configuration to Google Drive: {e}")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
            custom_df = None
    else:
        try:
            custom_df = pd.read_csv("courses_config.csv")
            st.info("Loaded courses configuration from local file (courses_config.csv).")
        except Exception as e:
            st.error("No courses configuration file found. Please upload a custom courses file.")
            custom_df = None
    
    if custom_df is not None:
        if {'Course', 'Credits', 'CountedGrades'}.issubset(custom_df.columns):
            if 'Type' in custom_df.columns:
                required_df = custom_df[custom_df['Type'].str.lower() == 'required']
                intensive_df = custom_df[custom_df['Type'].str.lower() == 'intensive']
            else:
                required_df = custom_df
                intensive_df = pd.DataFrame()
            target_courses = {}
            for _, row in required_df.iterrows():
                course = row['Course'].strip().upper()
                credits = row['Credits']
                counted = [g.strip() for g in str(row['CountedGrades']).split(',')]
                target_courses[course] = {"credits": credits, "counted_grades": counted}
            st.session_state['target_courses'] = target_courses
            intensive_courses = {}
            if not intensive_df.empty:
                for _, row in intensive_df.iterrows():
                    course = row['Course'].strip().upper()
                    credits = row['Credits']
                    counted = [g.strip() for g in str(row['CountedGrades']).split(',')]
                    intensive_courses[course] = {"credits": credits, "counted_grades": counted}
            st.session_state['intensive_courses'] = intensive_courses
            st.success("Courses configuration loaded successfully.")
        else:
            st.error("CSV must contain 'Course', 'Credits', and 'CountedGrades' columns.")

st.success("Courses are now set. Proceed to 'View Reports' to see the processed data.")

# Assignment Types Configuration remains as before.
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types that can be assigned to courses. For example, enter S.C.E, F.E.C, ARAB201 to allow assignments for those courses.")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
