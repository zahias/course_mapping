import streamlit as st
import pandas as pd
import os
from google_drive_utils import (
<<<<<<< HEAD
    authenticate_google_drive,
    search_file,
    download_file,
    update_file,
    upload_file
=======
    authenticate_google_drive, 
    search_file, 
    update_file, 
    upload_file, 
    download_file
>>>>>>> parent of e37c21f (e)
)
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of abfac76 (3)
st.write("""\
Upload a custom CSV to define courses configuration. Required columns:

- Course  
- Credits  
- PassingGrades (comma-separated list)  
- Type (Required or Intensive)

Optional columns:

- Effective_From (e.g. SPRING‑2023)  
- Effective_To   (e.g. FALL‑2023)

If you omit Effective dates, the rule applies to all terms.
""")
<<<<<<< HEAD

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader("Upload Courses Configuration CSV", type="csv")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template CSV"):
            template_df = pd.DataFrame({
                'Course': ['MATH101', 'MATH102'],
                'Credits': [3, 3],
                'PassingGrades': ['A+,A,A-,B+,B,B-,C+,C,C-', 'A+,A,A-,B+,B,B-,C+,C,C-'],
                'Type': ['Required', 'Required'],
                'Effective_From': ['FALL-2016', 'FALL-2016'],
                'Effective_To': ['SPRING-2022', 'SPRING-2022']
=======
st.write(
<<<<<<< HEAD
<<<<<<< HEAD
    "Upload a custom CSV to define your courses. Required columns:\n\n"
    "- `Course`\n"
    "- `Credits`\n"
    "- `PassingGrades` (comma‑separated)\n"
    "- `Type` (`Required` or `Intensive`)\n\n"
    "Optional columns to handle time‑based rules:\n\n"
    "- `Effective_From` (e.g. `FALL-2016`)\n"
    "- `Effective_To`   (e.g. `SPRING-2022`)\n\n"
    "If you leave Effective dates blank, the rule applies for all semesters."
=======
    "Upload a custom CSV to define courses configuration. "
    "The CSV must contain: 'Course', 'Credits', 'PassingGrades', 'Type', "
    "and optionally 'EffectiveSemester' (e.g. Spring-2023)."
>>>>>>> parent of 02f20b1 (e)
=======
    "Upload a custom CSV to define courses configuration. The CSV should contain: "
    "'Course', 'Credits', 'PassingGrades', and 'Type'. "
    "The 'PassingGrades' column is a comma-separated list of all acceptable passing grades for that course."
>>>>>>> parent of e37c21f (e)
)
=======
>>>>>>> parent of abfac76 (3)

# --- Courses Configuration Section ---
with st.expander("Course Configuration Options", expanded=True):
<<<<<<< HEAD
<<<<<<< HEAD
    uploaded = st.file_uploader("Upload Courses Configuration CSV", type="csv")

    col1, col2 = st.columns(2)
    with col1:
<<<<<<< HEAD
        if st.button("Download Template"):
            tmpl = pd.DataFrame({
                'Course': ['ACCT201','ACCT201'],
                'Credits': [3,3],
                'PassingGrades': [
                    'A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T',
                    'A+,A,A-'
                ],
                'Type': ['Required','Required'],
                'Effective_From': ['FALL-2016','FALL-2023'],
                'Effective_To': ['SPRING-2022','']
>>>>>>> parent of 98d5b2a (3)
=======
        if st.button("Download Template CSV"):
            template_df = pd.DataFrame({
                'Course': ['MATH101', 'MATH102'],
                'Credits': [3, 3],
                'PassingGrades': ['A+,A,A-,B+,B,B-,C+,C,C-', 'A+,A,A-,B+,B,B-,C+,C,C-'],
                'Type': ['Required', 'Required'],
                'Effective_From': ['FALL-2016', 'FALL-2016'],
                'Effective_To': ['SPRING-2022', 'SPRING-2022']
>>>>>>> parent of abfac76 (3)
=======
    uploaded = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="Use the template below."
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Download Template"):
            tmpl = pd.DataFrame({
                'Course': ['ENGL201', 'CHEM201', 'ARAB201', 'MATH101'],
                'Credits': [3, 3, 3, 3],
                'PassingGrades': [
                    'A+,A,A-,B+,B,B-,C+,C,C-',
                    'A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-',
                    'A+,A,A-,B+,B,B-,C+,C,C-',
                    'A+,A,A-,B+,B,B-,C+,C,C-'
                ],
                'Type': ['Required', 'Required', 'Required', 'Intensive'],
                'EffectiveSemester': ['', '', 'Fall-2023', '']
>>>>>>> parent of 02f20b1 (e)
            })
            csv_bytes = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
<<<<<<< HEAD
                label="Download Courses Template",
                data=csv_bytes,
                file_name="courses_template.csv",
                mime="text/csv"
            )

    with col2:
<<<<<<< HEAD
<<<<<<< HEAD
        if st.button("Reload Courses Configuration from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    download_file(service, file_id, "courses_config.csv")
                    st.success("courses_config.csv reloaded from Google Drive.")
=======
        if st.button("Reload from Google Drive"):
=======
                "Download CSV Template",
                data=tmpl.to_csv(index=False).encode(),
                file_name="courses_template.csv",
                mime="text/csv"
            )
    with c2:
        if st.button("Reload Configuration from Drive"):
>>>>>>> parent of 02f20b1 (e)
            try:
                creds = authenticate_google_drive()
                srv = build('drive', 'v3', credentials=creds)
                fid = search_file(srv, "courses_config.csv")
                if fid:
<<<<<<< HEAD
                    download_file(service,fid,"courses_config.csv")
                    st.success("Reloaded courses_config.csv from Drive")
>>>>>>> parent of 98d5b2a (3)
                else:
                    st.error("courses_config.csv not found on Google Drive.")
            except Exception as e:
<<<<<<< HEAD
                st.error(f"Error reloading from Google Drive: {e}")

    # Load the DataFrame either from upload or local cache
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    update_file(service, file_id, "courses_config.csv")
                else:
                    upload_file(service, "courses_config.csv", "courses_config.csv")
                st.info("courses_config.csv synced to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing to Google Drive: {e}")
        except Exception as e:
            st.error(f"Error reading uploaded CSV: {e}")
=======
                st.error(f"Error: {e}")
=======
        if st.button("Reload Courses Configuration from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    download_file(service, file_id, "courses_config.csv")
                    st.success("courses_config.csv reloaded from Google Drive.")
                else:
                    st.error("courses_config.csv not found on Google Drive.")
            except Exception as e:
                st.error(f"Error reloading from Google Drive: {e}")
>>>>>>> parent of abfac76 (3)

    # Load the DataFrame either from upload or local cache
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    update_file(service, file_id, "courses_config.csv")
                else:
                    upload_file(service, "courses_config.csv", "courses_config.csv")
                st.info("courses_config.csv synced to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing to Google Drive: {e}")
        except Exception as e:
<<<<<<< HEAD
            st.error(f"Sync error: {e}")
>>>>>>> parent of 98d5b2a (3)
=======
            st.error(f"Error reading uploaded CSV: {e}")
>>>>>>> parent of abfac76 (3)

=======
                    download_file(srv, fid, "courses_config.csv")
                    st.success("Reloaded courses_config.csv from Google Drive")
=======
    uploaded_courses = st.file_uploader("Upload Courses Configuration (CSV)", type="csv", help="Use the template below.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template", help="Download the CSV template for courses configuration."):
            template_df = pd.DataFrame({
                'Course': ['ENGL201', 'CHEM201', 'ARAB201', 'MATH101'],
                'Credits': [3, 3, 3, 3],
                'PassingGrades': ['A+,A,A-', 'A+,A,A-', 'A+,A,A-,B+,B,B-,C+,C,C-', 'A+,A,A-,B+,B,B-,C+,C,C-'],
                'Type': ['Required', 'Required', 'Required', 'Required']
            })
            csv_data = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Courses Template", data=csv_data, file_name='courses_template.csv', mime='text/csv')
    with col2:
        if st.button("Reload Courses Configuration from Google Drive", help="Load courses configuration from Google Drive."):
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                file_id = search_file(service, "courses_config.csv")
                if file_id:
                    download_file(service, file_id, "courses_config.csv")
                    st.success("Courses configuration reloaded from Google Drive.")
>>>>>>> parent of e37c21f (e)
                else:
                    st.error("Courses configuration file not found on Google Drive.")
            except Exception as e:
                st.error(f"Error reloading courses configuration: {e}")
    
    # Load courses configuration from the uploaded file or from local if available.
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
            # Save locally
            courses_df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                service = build('drive', 'v3', credentials=creds)
                folder_id = None
                file_id = search_file(service, "courses_config.csv", folder_id=folder_id)
                if file_id:
                    update_file(service, file_id, "courses_config.csv")
                else:
                    upload_file(service, "courses_config.csv", "courses_config.csv", folder_id=folder_id)
                st.info("Courses configuration synced to Google Drive.")
            except Exception as e:
                st.error(f"Error syncing courses configuration: {e}")
        except Exception as e:
<<<<<<< HEAD
            st.error(f"Error reading uploaded CSV: {e}")
            courses_df = None
>>>>>>> parent of 02f20b1 (e)
=======
            st.error(f"Error reading the uploaded file: {e}")
>>>>>>> parent of e37c21f (e)
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    # Validate and store into session_state
    if df is not None:
        required_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not required_cols.issubset(df.columns):
            st.error(f"Missing columns in CSV: {required_cols - set(df.columns)}")
=======
    # Build session_state configs
=======
    # Validate and store into session_state
>>>>>>> parent of abfac76 (3)
    if df is not None:
        required_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not required_cols.issubset(df.columns):
<<<<<<< HEAD
            st.error(f"Missing columns: {required_cols - set(df.columns)}")
>>>>>>> parent of 98d5b2a (3)
=======
            st.error(f"Missing columns in CSV: {required_cols - set(df.columns)}")
>>>>>>> parent of abfac76 (3)
        else:
            # Helper to parse Effective_From/To into tuples
            def parse_eff(val):
                if pd.isna(val) or not str(val).strip():
                    return None
<<<<<<< HEAD
<<<<<<< HEAD
                sem, yr = val.split('-', 1)
                return (sem.title(), int(yr))
=======
                sem, year = val.split('-',1)
                sem = sem.strip().title()
                yr = int(year)
                idx = SEM_INDEX.get(sem, 0)
                return yr * 3 + idx
>>>>>>> parent of 98d5b2a (3)
=======
                sem, yr = val.split('-', 1)
                return (sem.title(), int(yr))
>>>>>>> parent of abfac76 (3)

            target_cfg = {}
            intensive_cfg = {}

            for _, row in df.iterrows():
                code = row['Course'].strip().upper()
                entry = {
                    'Credits': int(row['Credits']),
                    'PassingGrades': row['PassingGrades'].strip(),
                    'Type': row['Type'].strip().title(),
<<<<<<< HEAD
<<<<<<< HEAD
                    'Effective_From': parse_eff(row.get('Effective_From', '')),
                    'Effective_To':   parse_eff(row.get('Effective_To', ''))
=======
                    'Eff_From': parse_eff(row.get('Effective_From','')),
                    'Eff_To':   parse_eff(row.get('Effective_To',''))
>>>>>>> parent of 98d5b2a (3)
=======
                    'Effective_From': parse_eff(row.get('Effective_From', '')),
                    'Effective_To':   parse_eff(row.get('Effective_To', ''))
>>>>>>> parent of abfac76 (3)
                }
                if entry['Type'] == 'Required':
                    target_cfg.setdefault(code, []).append(entry)
                else:
                    intensive_cfg.setdefault(code, []).append(entry)

<<<<<<< HEAD
<<<<<<< HEAD
            st.session_state['target_courses_config'] = target_cfg
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Course configurations loaded into session_state.")
    else:
        st.info("No courses_config.csv found—please upload or reload from Drive.")
=======
            st.session_state['target_courses_config']  = target_cfg
=======
            st.session_state['target_courses_config'] = target_cfg
>>>>>>> parent of abfac76 (3)
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Course configurations loaded into session_state.")
    else:
<<<<<<< HEAD
        st.info("Please upload or reload a courses_config.csv.")

# (Put the "Equivalent Courses" and "Assignment Types" sections here as before.)
>>>>>>> parent of 98d5b2a (3)
=======
        st.info("No courses_config.csv found—please upload or reload from Drive.")
>>>>>>> parent of abfac76 (3)
=======
    if courses_df is not None:
        required_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if required_cols.issubset(courses_df.columns):
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            # Separate required (target) and intensive courses:
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
            st.error("CSV must contain columns: 'Course', 'Credits', 'PassingGrades', and 'Type'.")
    else:
        st.info("No courses configuration available. Please upload a file.")

# --- Equivalent Courses Section ---
with st.expander("Equivalent Courses", expanded=True):
    st.write("This section automatically loads the 'equivalent_courses.csv' file from Google Drive.")
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        file_id = search_file(service, "equivalent_courses.csv")
        if file_id:
            download_file(service, file_id, "equivalent_courses.csv")
            st.success("Equivalent courses file loaded from Google Drive.")
        else:
            # If not found, create an empty equivalent_courses.csv with header.
            empty_df = pd.DataFrame(columns=["Course", "Equivalent"])
            empty_df.to_csv("equivalent_courses.csv", index=False)
            upload_file(service, "equivalent_courses.csv", "equivalent_courses.csv")
            st.info("No equivalent courses file found on Google Drive. An empty file has been created and uploaded.")
    except Exception as e:
        st.error(f"Error processing equivalent courses file: {e}")

# --- Assignment Types Configuration Section ---
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types (e.g., S.C.E, F.E.C, ARAB201).")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
<<<<<<< HEAD
        new = [x.strip() for x in txt.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new
        st.success("Assignment types updated")
>>>>>>> parent of 02f20b1 (e)
=======
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
>>>>>>> parent of e37c21f (e)
