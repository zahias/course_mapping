# customize_courses.py

import streamlit as st
import pandas as pd
import os
import io
import csv
from google_drive_utils import (
    authenticate_google_drive,
    search_file,
    update_file,
    upload_file,
    download_file
)
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

st.write(
    "Upload a custom CSV to define courses configuration. "
    "The CSV must contain: 'Course', 'Credits', 'PassingGrades', 'Type', "
    "and optionally 'EffectiveSemester' (e.g. Spring-2023)."
)

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="If your PassingGrades list has commas, you can omit quoting—this parser will stitch it back together."
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
            })
            st.download_button(
                "Download CSV Template",
                data=tmpl.to_csv(index=False).encode(),
                file_name="courses_template.csv",
                mime="text/csv"
            )
    with c2:
        if st.button("Reload Configuration from Drive"):
            try:
                creds = authenticate_google_drive()
                srv = build('drive', 'v3', credentials=creds)
                fid = search_file(srv, "courses_config.csv")
                if fid:
                    download_file(srv, fid, "courses_config.csv")
                    st.success("Reloaded courses_config.csv from Google Drive")
                else:
                    st.error("No courses_config.csv found on Drive")
            except Exception as e:
                st.error(f"Error reloading: {e}")

    # === Load or parse the courses_df ===
    if uploaded is not None:
        # Read raw text and parse with csv.reader
        text = uploaded.getvalue().decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(text))
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        if not rows:
            st.error("Uploaded file is empty or invalid.")
            courses_df = None
        else:
            # The header:
            header = rows[0]
            # Expecting at least 5 columns: Course, Credits, PassingGrades, Type, EffectiveSemester
            # If we have more, we assume the extra fields belong to PassingGrades.
            def normalize_row(row):
                if len(row) < 5:
                    # Too few columns
                    return None
                if len(row) == 5:
                    return row
                # More than 5: stitch row[2:-2] into one field
                course = row[0].strip()
                credits = row[1].strip()
                passing = ",".join(cell.strip() for cell in row[2:-2])
                typ = row[-2].strip()
                eff = row[-1].strip()
                return [course, credits, passing, typ, eff]

            normalized = list(filter(None, (normalize_row(r) for r in rows[1:])))
            courses_df = pd.DataFrame(normalized, columns=['Course','Credits','PassingGrades','Type','EffectiveSemester'])
            # Save locally
            courses_df.to_csv("courses_config.csv", index=False)

            # Sync to Google Drive
            try:
                creds = authenticate_google_drive()
                srv = build('drive', 'v3', credentials=creds)
                fid = search_file(srv, "courses_config.csv")
                if fid:
                    update_file(srv, fid, "courses_config.csv")
                else:
                    upload_file(srv, "courses_config.csv", "courses_config.csv")
                st.success("Configuration parsed, saved & synced to Drive")
            except Exception as e:
                st.error(f"Error syncing to Drive: {e}")

    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    # === Build rules from courses_df ===
    if courses_df is not None:
        required_cols = {'Course','Credits','PassingGrades','Type'}
        if not required_cols.issubset(courses_df.columns):
            st.error(f"Missing columns: {required_cols - set(courses_df.columns)}")
        else:
            # Normalize Course codes
            courses_df['Course'] = courses_df['Course'].str.upper().str.strip()
            # Ensure EffectiveSemester exists
            if 'EffectiveSemester' not in courses_df.columns:
                courses_df['EffectiveSemester'] = ''

            # Map semesters to numeric EffValue
            sem_map = {'Spring':1,'Summer':2,'Fall':3}
            def sem_to_val(es):
                if not es or pd.isna(es):
                    return 0
                try:
                    sem, yr = es.split('-')
                    return int(yr)*10 + sem_map.get(sem.title(),0)
                except:
                    return 0
            courses_df['EffValue'] = courses_df['EffectiveSemester'].apply(sem_to_val)

            # Build course_rules: course → list of {eff, passing_grades, credits}
            course_rules = {}
            for course, grp in courses_df.groupby('Course'):
                rules = []
                for _, r in grp.iterrows():
                    rules.append({
                        'eff': int(r['EffValue']),
                        'passing_grades': [g.strip().upper() for g in r['PassingGrades'].split(',')],
                        'credits': int(r['Credits'])
                    })
                rules.sort(key=lambda x: x['eff'])
                course_rules[course] = rules

            # Build target/intensive credit dicts
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

# === Equivalent Courses Section ===
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
            # create an empty file if missing
            pd.DataFrame(columns=["Course","Equivalent"])\
              .to_csv("equivalent_courses.csv",index=False)
            upload_file(srv, "equivalent_courses.csv", "equivalent_courses.csv")
            st.info("No file found. Created empty equivalent_courses.csv on Drive")
    except Exception as e:
        st.error(f"Error with equivalent courses: {e}")

# === Assignment Types Configuration ===
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types (e.g. S.C.E, F.E.C, ARAB201).")
    default = st.session_state.get("allowed_assignment_types", ["S.C.E","F.E.C"])
    txt = st.text_input("Assignment types (comma‑separated)", value=", ".join(default))
    if st.button("Save Assignment Types"):
        new = [x.strip() for x in txt.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new
        st.success("Assignment types updated")
