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
    "Upload a custom CSV to define courses configuration. The CSV should contain:\n\n"
    "- **Course** (e.g. PBHL201)\n"
    "- **Credits** (integer)\n"
    "- **PassingGrades** (comma-separated list, e.g. A+,A,A-,B)\n"
    "- **Type** (`Required` or `Intensive`)\n"
    "- **FromSemester** (e.g. FALL-2016) or leave blank for no lower bound\n"
    "- **ToSemester**   (e.g. SUMMER-9999) or leave blank for no upper bound\n\n"
    "Semesters use exactly the same `FALL-YYYY`, `SPRING-YYYY`, `SUMMER-YYYY` codes as your data."
)

with st.expander("Course Configuration Options", expanded=True):
    uploaded_courses = st.file_uploader(
        "Upload Courses Configuration (CSV)",
        type="csv",
        help="Use the template below."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template"):
            template_df = pd.DataFrame([
                {
                    "Course":        "PBHL201",
                    "Credits":       3,
                    "PassingGrades": "C-,C,C+",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2016",
                    "ToSemester":    "SPRING-2018"
                },
                {
                    "Course":        "PBHL201",
                    "Credits":       3,
                    "PassingGrades": "C+,C",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2018",
                    "ToSemester":    "SUMMER-9999"
                },
                {
                    "Course":        "MATH102",
                    "Credits":       3,
                    "PassingGrades": "D-,D",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2015",
                    "ToSemester":    "SUMMER-2019"
                },
                {
                    "Course":        "MATH102",
                    "Credits":       3,
                    "PassingGrades": "C-,C",
                    "Type":          "Required",
                    "FromSemester":  "FALL-2019",
                    "ToSemester":    "SUMMER-9999"
                },
                {
                    "Course":        "INEG200",
                    "Credits":       3,
                    "PassingGrades": "A+,A,A-",
                    "Type":          "Intensive",
                    "FromSemester":  "FALL-2015",
                    "ToSemester":    "SUMMER-9999"
                },
            ])
            st.download_button(
                "Download Courses Template",
                data=template_df.to_csv(index=False).encode("utf-8"),
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
                    st.success("Reloaded courses_config.csv from Google Drive.")
                else:
                    st.error("No courses_config.csv found on Google Drive.")
            except Exception as e:
                st.error(f"Error reloading from Drive: {e}")

    # -- Load the CSV (either uploaded or from disk) --
    if uploaded_courses is not None:
        try:
            courses_df = pd.read_csv(uploaded_courses)
            courses_df.to_csv("courses_config.csv", index=False)
            # Sync to Google Drive
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            file_id = search_file(service, "courses_config.csv")
            if file_id:
                update_file(service, file_id, "courses_config.csv")
            else:
                upload_file(service, "courses_config.csv", "courses_config.csv")
            st.success("Courses configuration synced to Google Drive.")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    elif os.path.exists("courses_config.csv"):
        courses_df = pd.read_csv("courses_config.csv")
    else:
        courses_df = None

    # -- Parse into in‐memory rule tables and separate credit maps --
    if courses_df is not None:
        required_cols = {
            "Course", "Credits", "PassingGrades",
            "Type", "FromSemester", "ToSemester"
        }
        if required_cols.issubset(courses_df.columns):
            # Helper: FALL-YYYY → ordinal; blank → open bound
            def sem_to_ord(s: str, lower: bool):
                if pd.isna(s) or str(s).strip() == "":
                    return float('-inf') if lower else float('inf')
                sem, yr = str(s).split("-")
                return int(yr) * 3 + {"FALL":0, "SPRING":1, "SUMMER":2}[sem.upper()]

            target_rules = {}
            intensive_rules = {}
            # We'll build two separate credit‐maps:
            required_credits = {}
            intensive_credits = {}

            for _, row in courses_df.iterrows():
                course = str(row["Course"]).strip().upper()
                creds  = int(row["Credits"])
                pg     = str(row["PassingGrades"]).strip()
                typ    = str(row["Type"]).strip().lower()
                fr     = sem_to_ord(row["FromSemester"], lower=True)
                to     = sem_to_ord(row["ToSemester"],   lower=False)
                rule   = {
                    "Credits":       creds,
                    "PassingGrades": pg,
                    "FromOrd":       fr,
                    "ToOrd":         to
                }

                if typ == "required":
                    required_credits[course] = creds
                    target_rules.setdefault(course, []).append(rule)
                else:
                    intensive_credits[course] = creds
                    intensive_rules.setdefault(course, []).append(rule)

            # Persist correct, separate maps into session
            st.session_state["target_course_rules"]    = target_rules
            st.session_state["intensive_course_rules"] = intensive_rules
            st.session_state["target_courses"]         = required_credits
            st.session_state["intensive_courses"]      = intensive_credits

            st.success("Courses configuration loaded.")
        else:
            st.error(
                "CSV must contain columns: " + ", ".join(sorted(required_cols))
            )
    else:
        st.info("No courses configuration available. Please upload a file.")
