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

def customize_courses_page():
    st.image("pu_logo.png", width=120)
    st.title("Customize Courses")

    st.markdown("Use the uploader below to define your course configuration (Course, Credits, PassingGrades, Type).")

    uploaded_courses = st.file_uploader("Upload Courses Configuration (CSV)", type="csv", help="Use the template if needed.")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Download Template"):
            template = pd.DataFrame({
                'Course': ['ENGL201','CHEM201','ARAB201','MATH101'],
                'Credits': [3,3,3,3],
                'PassingGrades': ['A+,A,A-','A+,A,A-','A+,A,A-,B+,B,B-,C+,C,C-','A+,A,A-,B+,B,B-,C+,C,C-'],
                'Type': ['Required','Required','Required','Required']
            })
            st.download_button("Download CSV Template",
                data=template.to_csv(index=False).encode(),
                file_name="courses_template.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("Reload from Google Drive"):
            try:
                creds = authenticate_google_drive()
                service = build("drive","v3",credentials=creds)
                fid = search_file(service, "courses_config.csv")
                if fid:
                    download_file(service, fid, "courses_config.csv")
                    st.success("Reloaded courses_config.csv from Google Drive.")
                else:
                    st.error("No courses_config.csv found on Google Drive.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Load or save uploaded config
    if uploaded_courses:
        try:
            df = pd.read_csv(uploaded_courses)
            df.to_csv("courses_config.csv", index=False)
            # Sync to Drive
            creds = authenticate_google_drive()
            service = build("drive","v3",credentials=creds)
            fid = search_file(service, "courses_config.csv")
            if fid:
                update_file(service, fid, "courses_config.csv")
            else:
                upload_file(service, "courses_config.csv", "courses_config.csv")
            st.success("Courses configuration synced to Google Drive.")
        except Exception as e:
            st.error(f"Upload error: {e}")
    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

    if df is not None:
        st.dataframe(df)
        # (Session state logic unchanged…)

    # Equivalent Courses section
    st.markdown("### Equivalent Courses")
    st.write("Auto‑loads `equivalent_courses.csv` from Drive; creates an empty one if missing.")
    try:
        creds = authenticate_google_drive()
        service = build("drive","v3",credentials=creds)
        fid = search_file(service, "equivalent_courses.csv")
        if fid:
            download_file(service, fid, "equivalent_courses.csv")
            st.success("Loaded equivalent_courses.csv from Google Drive.")
        else:
            empty = pd.DataFrame(columns=["Course","Equivalent"])
            empty.to_csv("equivalent_courses.csv", index=False)
            upload_file(service, "equivalent_courses.csv", "equivalent_courses.csv")
            st.info("Created empty equivalent_courses.csv on Google Drive.")
        eq_df = pd.read_csv("equivalent_courses.csv")
        st.dataframe(eq_df)
    except Exception as e:
        st.error(f"Error: {e}")

    # Assignment Types (unchanged)…


# --- Assignment Types Configuration Section ---
with st.expander("Assignment Types Configuration", expanded=True):
    st.write("Edit the list of assignment types (e.g., S.C.E, F.E.C, ARAB201).")
    default_types = st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])
    assignment_types_str = st.text_input("Enter assignment types (comma separated)", value=", ".join(default_types))
    if st.button("Save Assignment Types"):
        new_types = [x.strip() for x in assignment_types_str.split(",") if x.strip()]
        st.session_state["allowed_assignment_types"] = new_types
        st.success("Assignment types updated.")
