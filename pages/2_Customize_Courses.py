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
)
=======
>>>>>>> parent of abfac76 (3)

with st.expander("Course Configuration Options", expanded=True):
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
                else:
                    st.error("No courses_config.csv found on Drive")
            except Exception as e:
                st.error(f"Error reloading: {e}")

    # Load courses_df from uploaded or local
    if uploaded is not None:
        try:
            courses_df = pd.read_csv(uploaded)
            courses_df.to_csv("courses_config.csv", index=False)
            # Sync up to Drive
            creds = authenticate_google_drive()
            srv = build('drive', 'v3', credentials=creds)
            fid = search_file(srv, "courses_config.csv")
            if fid:
                update_file(srv, fid, "courses_config.csv")
            else:
                upload_file(srv, "courses_config.csv", "courses_config.csv")
            st.success("Configuration uploaded & synced to Drive")
        except Exception as e:
            st.error(f"Error reading uploaded CSV: {e}")
            courses_df = None
>>>>>>> parent of 02f20b1 (e)
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
        # Ensure core columns exist
        req_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not req_cols.issubset(courses_df.columns):
            st.error(f"Missing columns: {req_cols - set(courses_df.columns)}")
        else:
            # Normalize
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            # Add EffectiveSemester if missing
            if 'EffectiveSemester' not in courses_df.columns:
                courses_df['EffectiveSemester'] = ''

            # Map semesters into numeric eff-values
            sem_map = {'Spring':1, 'Summer':2, 'Fall':3}
            def sem_to_val(es):
                if not es or pd.isna(es):
                    return 0
                try:
                    sem, yr = es.split('-')
                    return int(yr)*10 + sem_map.get(sem.title(),0)
                except:
                    return 0
            courses_df['EffValue'] = courses_df['EffectiveSemester'].apply(sem_to_val)

            # Build course_rules: course → sorted list of {eff, passing_grades, credits}
            course_rules = {}
            for course, grp in courses_df.groupby('Course'):
                rules = []
                for _, r in grp.iterrows():
                    rules.append({
                        'eff': int(r['EffValue']),
                        'passing_grades': [g.strip().upper() for g in str(r['PassingGrades']).split(',')],
                        'credits': int(r['Credits'])
                    })
                rules.sort(key=lambda x: x['eff'])
                course_rules[course] = rules

            # Separate target vs intensive dictionaries (credits only)
            target = {
                r['Course']: int(r['Credits'])
                for _, r in courses_df[courses_df['Type'].str.lower()=='required'].iterrows()
            }
            intensive = {
                r['Course']: int(r['Credits'])
                for _, r in courses_df[courses_df['Type'].str.lower()=='intensive'].iterrows()
            }

            # Store in session
            st.session_state['target_courses'] = target
            st.session_state['intensive_courses'] = intensive
            st.session_state['course_rules'] = course_rules

            st.success("Courses configuration loaded with effective‐semester rules")

# Equivalent Courses Section
with st.expander("Equivalent Courses", expanded=True):
    st.write("This section automatically loads the ‘equivalent_courses.csv’ file from Google Drive.")
    try:
        creds = authenticate_google_drive()
        srv = build('drive','v3',credentials=creds)
        fid = search_file(srv, "equivalent_courses.csv")
        if fid:
            download_file(srv, fid, "equivalent_courses.csv")
            st.success("Loaded equivalent_courses.csv from Drive")
        else:
            # create an empty file
            pd.DataFrame(columns=["Course","Equivalent"])\
              .to_csv("equivalent_courses.csv",index=False)
            upload_file(srv, "equivalent_courses.csv", "equivalent_courses.csv")
            st.info("No file found. Created empty equivalent_courses.csv on Drive")
    except Exception as e:
        st.error(f"Error with equivalent courses: {e}")

# Assignment Types Section
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types (e.g. S.C.E, F.E.C, ARAB201).")
    default = st.session_state.get("allowed_assignment_types", ["S.C.E","F.E.C"])
    txt = st.text_input("Assignment types (comma‑separated)", value=", ".join(default))
    if st.button("Save Assignment Types"):
        new = [x.strip() for x in txt.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new
        st.success("Assignment types updated")
>>>>>>> parent of 02f20b1 (e)
