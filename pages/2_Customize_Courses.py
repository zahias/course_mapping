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
            })
            csv_bytes = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Courses Template",
                data=csv_bytes,
                file_name="courses_template.csv",
                mime="text/csv"
            )

    with col2:
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

    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

    # Validate and store into session_state
    if df is not None:
        required_cols = {'Course', 'Credits', 'PassingGrades', 'Type'}
        if not required_cols.issubset(df.columns):
            st.error(f"Missing columns in CSV: {required_cols - set(df.columns)}")
        else:
            # Helper to parse Effective_From/To into tuples
            def parse_eff(val):
                if pd.isna(val) or not str(val).strip():
                    return None
                sem, yr = val.split('-', 1)
                return (sem.title(), int(yr))

            target_cfg = {}
            intensive_cfg = {}

            for _, row in df.iterrows():
                code = row['Course'].strip().upper()
                entry = {
                    'Credits': int(row['Credits']),
                    'PassingGrades': row['PassingGrades'].strip(),
                    'Type': row['Type'].strip().title(),
                    'Effective_From': parse_eff(row.get('Effective_From', '')),
                    'Effective_To':   parse_eff(row.get('Effective_To', ''))
                }
                if entry['Type'] == 'Required':
                    target_cfg.setdefault(code, []).append(entry)
                else:
                    intensive_cfg.setdefault(code, []).append(entry)

            st.session_state['target_courses_config'] = target_cfg
            st.session_state['intensive_courses_config'] = intensive_cfg
            st.success("Course configurations loaded into session_state.")
    else:
        st.info("No courses_config.csv found—please upload or reload from Drive.")
