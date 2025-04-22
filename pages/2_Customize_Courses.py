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

def sem_to_ord(sem_year: str):
    """
    Convert 'FALL-2017', 'SPRING-2018', 'SUMMER-2019' into an integer:
      ordinal = year * 3 + {FALL→0, SPRING→1, SUMMER→2}
    """
    try:
        sem, yr = sem_year.split('-')
        idx = {"FALL": 0, "SPRING": 1, "SUMMER": 2}[sem.strip().upper()]
        return int(yr) * 3 + idx
    except Exception:
        return None

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader(
        "Upload Courses Config CSV",
        type="csv",
        help="Columns: Course,Credits,PassingGrades,Type,Optional FromSemester,ToSemester"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template"):
            tmpl = pd.DataFrame({
                "Course": ["ACCT201", "INEG200", "MATH102", "MATH102"],
                "Credits": [3, 3, 3, 3],
                "PassingGrades": [
                    "A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T",
                    "A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T",
                    "A+,A,A-,B+,B,B-,C+,C,C-,D+,D,D-,P,P*,WP,T",
                    "A+,A"
                ],
                "Type": ["Required", "Intensive", "Required", "Required"],
                "FromSemester": ["FALL-2016", "", "FALL-2016", "SPRING-2022"],
                "ToSemester":   ["FALL-2022", "", "FALL-2022", "SPRING-2025"]
            })
            st.download_button(
                "Download CSV Template",
                tmpl.to_csv(index=False).encode("utf-8"),
                "courses_template.csv",
                "text/csv"
            )
    with col2:
        if st.button("Reload from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive", "v3", credentials=creds)
                fid = search_file(service, "courses_config.csv")
                if fid:
                    download_file(service, fid, "courses_config.csv")
                    st.success("courses_config.csv reloaded from Google Drive")
                else:
                    st.error("No courses_config.csv found on Google Drive")
            except Exception as e:
                st.error(f"Error reloading: {e}")

    # Load or save the CSV
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            df.to_csv("courses_config.csv", index=False)
            # sync to Drive
            creds = authenticate_google_drive()
            service = build("drive", "v3", credentials=creds)
            fid = search_file(service, "courses_config.csv")
            if fid:
                update_file(service, fid, "courses_config.csv")
            else:
                upload_file(service, "courses_config.csv", "courses_config.csv")
            st.info("courses_config.csv synced to Google Drive")
        except Exception as e:
            st.error(f"Error saving uploaded file: {e}")
    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

    if df is not None:
        required_cols = {"Course", "Credits", "PassingGrades", "Type"}
        if required_cols.issubset(df.columns):
            target_rules = {}
            intensive_rules = {}

            for _, row in df.iterrows():
                course = row["Course"].strip().upper()
                credits = int(row["Credits"])
                passing = row["PassingGrades"]
                ctype = row["Type"].strip().lower()

                from_ord = sem_to_ord(str(row.get("FromSemester", "") or ""))
                to_ord   = sem_to_ord(str(row.get("ToSemester", "") or ""))

                # default to unbounded if missing
                if from_ord is None:
                    from_ord = float("-inf")
                if to_ord is None:
                    to_ord = float("inf")

                rule = {
                    "Credits": credits,
                    "PassingGrades": passing,
                    "FromOrd": from_ord,
                    "ToOrd": to_ord
                }

                if ctype == "intensive":
                    intensive_rules.setdefault(course, []).append(rule)
                else:
                    target_rules.setdefault(course, []).append(rule)

            st.session_state["target_course_rules"] = target_rules
            st.session_state["intensive_course_rules"] = intensive_rules
            st.success("Loaded course rules successfully.")
        else:
            st.error("courses_config.csv must contain: Course,Credits,PassingGrades,Type")
    else:
        st.info("No course configuration found. Please upload one.")
