import streamlit as st
import pandas as pd
import os
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    download_file,
    update_file,
    upload_file
)
from googleapiclient.discovery import build

# Semester mapping for code calculations
SEM_INDEX = {'Fall': 0, 'Spring': 1, 'Summer': 2}

st.title("Customize Courses")
st.markdown("---")

<<<<<<< HEAD
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
    "Upload a custom CSV to define your courses. Required columns:\n\n"
    "- `Course`\n"
    "- `Credits`\n"
    "- `PassingGrades` (comma‑separated)\n"
    "- `Type` (`Required` or `Intensive`)\n\n"
    "Optional columns to handle time‑based rules:\n\n"
    "- `Effective_From` (e.g. `FALL-2016`)\n"
    "- `Effective_To`   (e.g. `SPRING-2022`)\n\n"
    "If you leave Effective dates blank, the rule applies for all semesters."
)

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader("Upload Courses Configuration CSV", type="csv")
    col1, col2 = st.columns(2)

    with col1:
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
            })
            csv_bytes = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Courses Template",
                data=csv_bytes,
                file_name="courses_template.csv",
                mime="text/csv"
            )

    with col2:
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
            try:
                creds = authenticate_google_drive()
                service = build("drive","v3",credentials=creds)
                fid = search_file(service,"courses_config.csv")
                if fid:
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

    # Load into DataFrame
    if uploaded:
        df = pd.read_csv(uploaded)
        df.to_csv("courses_config.csv", index=False)
        # Sync to Drive
        try:
            creds = authenticate_google_drive()
            service = build("drive","v3",credentials=creds)
            fid = search_file(service,"courses_config.csv")
            if fid:
                update_file(service,fid,"courses_config.csv")
            else:
                upload_file(service,"courses_config.csv","courses_config.csv")
            st.info("Synced courses_config.csv to Drive")
        except Exception as e:
            st.error(f"Sync error: {e}")
>>>>>>> parent of 98d5b2a (3)

    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

<<<<<<< HEAD
    # Validate and store into session_state
    if df is not None:
        required_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not required_cols.issubset(df.columns):
            st.error(f"Missing columns in CSV: {required_cols - set(df.columns)}")
=======
    # Build session_state configs
    if df is not None:
        required_cols = {'Course','Credits','PassingGrades','Type'}
        if not required_cols.issubset(df.columns):
            st.error(f"Missing columns: {required_cols - set(df.columns)}")
>>>>>>> parent of 98d5b2a (3)
        else:
            # Helper to parse Effective_From/To into tuples
            def parse_eff(val):
                if pd.isna(val) or not str(val).strip():
                    return None
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

            target_cfg = {}
            intensive_cfg = {}

            for _, row in df.iterrows():
                code = row['Course'].strip().upper()
                entry = {
                    'Credits': int(row['Credits']),
                    'PassingGrades': row['PassingGrades'].strip(),
                    'Type': row['Type'].strip().title(),
<<<<<<< HEAD
                    'Effective_From': parse_eff(row.get('Effective_From', '')),
                    'Effective_To':   parse_eff(row.get('Effective_To', ''))
=======
                    'Eff_From': parse_eff(row.get('Effective_From','')),
                    'Eff_To':   parse_eff(row.get('Effective_To',''))
>>>>>>> parent of 98d5b2a (3)
                }
                if entry['Type']=='Required':
                    target_cfg.setdefault(code, []).append(entry)
                else:
                    intensive_cfg.setdefault(code, []).append(entry)

<<<<<<< HEAD
            st.session_state['target_courses_config'] = target_cfg
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Course configurations loaded into session_state.")
    else:
        st.info("No courses_config.csv found—please upload or reload from Drive.")
=======
            st.session_state['target_courses_config']  = target_cfg
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Loaded course configuration into session state.")
    else:
        st.info("Please upload or reload a courses_config.csv.")

# (Put the "Equivalent Courses" and "Assignment Types" sections here as before.)
>>>>>>> parent of 98d5b2a (3)
