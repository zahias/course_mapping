import streamlit as st
import pandas as pd
import os
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
    "Upload a custom CSV to define courses configuration. Required columns:\n\n"
    "- `Course`\n"
    "- `Credits`\n"
    "- `PassingGrades` (comma‑separated)\n"
    "- `Type` (`Required` or `Intensive`)\n\n"
    "**Optional** columns:\n\n"
    "- `Effective_From` (e.g. `FALL-2016`)\n"
    "- `Effective_To`   (e.g. `SPRING-2022`)\n\n"
    "If you omit Effective dates, the rule applies for all semesters."
)

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader("Upload Courses Configuration CSV", type="csv")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Download Template"):
            tmpl = pd.DataFrame({
                'Course': ['ACCT201', 'ACCT201'],
                'Credits': [3, 3],
                'PassingGrades': [
                    'A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T',
                    'A+,A,A-'
                ],
                'Type': ['Required', 'Required'],
                'Effective_From': ['FALL-2016', 'FALL-2023'],
                'Effective_To': ['SPRING-2022', '']
            })
            st.download_button(
                "Download Template CSV",
                data=tmpl.to_csv(index=False).encode(),
                file_name="courses_template.csv",
                mime="text/csv"
            )
    with c2:
        if st.button("Reload from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                fid = search_file(service, "courses_config.csv")
                if fid:
                    download_file(service, fid, "courses_config.csv")
                    st.success("Downloaded latest courses_config.csv from Drive.")
                else:
                    st.error("No courses_config.csv found on Drive.")
            except Exception as e:
                st.error(f"Error reloading from Drive: {e}")

    # Load DataFrame
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        df.to_csv("courses_config.csv", index=False)
        try:
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            fid = search_file(service, "courses_config.csv")
            if fid:
                update_file(service, fid, "courses_config.csv")
            else:
                upload_file(service, "courses_config.csv", "courses_config.csv")
            st.info("Synced courses_config.csv to Google Drive.")
        except Exception as e:
            st.error(f"Error syncing to Drive: {e}")
    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

    if df is not None:
        required = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not required.issubset(df.columns):
            st.error(f"Missing columns: {required - set(df.columns)}")
        else:
            def parse_eff(val):
                if pd.isna(val) or not str(val).strip():
                    return None
                sem, yr = val.split('-', 1)
                return (sem.strip().title(), int(yr))
            target_cfg = {}
            intensive_cfg = {}
            for _, row in df.iterrows():
                code = row['Course'].strip().upper()
                entry = {
                    'Credits': int(row['Credits']),
                    'PassingGrades': row['PassingGrades'],
                    'Type': row['Type'].strip().title(),
                    'Effective_From': parse_eff(row.get('Effective_From','')),
                    'Effective_To':   parse_eff(row.get('Effective_To',''))
                }
                if entry['Type'] == 'Required':
                    target_cfg.setdefault(code, []).append(entry)
                else:
                    intensive_cfg.setdefault(code, []).append(entry)
            st.session_state['target_courses_config'] = target_cfg
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Loaded course configurations.")
    else:
        st.info("Please upload or reload a courses_config.csv.")
