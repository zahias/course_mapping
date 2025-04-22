import streamlit as st
import pandas as pd
import os
from google_drive_utils import authenticate_google_drive, search_file, update_file, upload_file, download_file
from googleapiclient.discovery import build

st.title("Customize Courses")
st.markdown("---")

def sem_to_ord(sem_year: str):
    # e.g. "FALL-2017" → ordinal
    try:
        sem, yr = sem_year.split('-')
        yr = int(yr)
        mapping = {"FALL": 0, "SPRING": 1, "SUMMER": 2}
        idx = mapping.get(sem.strip().upper(), 0)
        return yr * 3 + idx
    except:
        return None

with st.expander("Course Configuration Options", expanded=True):
    uploaded = st.file_uploader("Upload Courses Config CSV", type="csv",
                                help="Must have: Course,Credits,PassingGrades,Type. Optional: FromSemester,ToSemester.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Download Template"):
            tmpl = pd.DataFrame({
                'Course': ['ENGL201','CHEM201','MATH101'],
                'Credits': [3,3,3],
                'PassingGrades': ['A+,A,A-','A+,A,A-','A+,A,A-,B+,B'],
                'Type': ['Required','Required','Intensive'],
                'FromSemester': ['','FALL-2017',''],
                'ToSemester': ['', 'FALL-2018','']
            })
            st.download_button("Download CSV Template", tmpl.to_csv(index=False).encode(),
                               "courses_template.csv","text/csv")
    with col2:
        if st.button("Reload from Google Drive"):
            try:
                creds = authenticate_google_drive()
                srv = build('drive','v3',credentials=creds)
                fid = search_file(srv,"courses_config.csv")
                if fid:
                    download_file(srv,fid,"courses_config.csv")
                    st.success("Reloaded courses_config.csv")
                else:
                    st.error("No courses_config.csv on Drive.")
            except Exception as e:
                st.error(f"{e}")

    # Load
    if uploaded:
        df = pd.read_csv(uploaded)
        df.to_csv("courses_config.csv",index=False)
        # Sync up
        try:
            creds=authenticate_google_drive(); srv=build('drive','v3',credentials=creds)
            fid=search_file(srv,"courses_config.csv")
            if fid: update_file(srv,fid,"courses_config.csv")
            else:   upload_file(srv,"courses_config.csv","courses_config.csv")
            st.info("Synced to Drive")
        except Exception as e:
            st.error(e)
    elif os.path.exists("courses_config.csv"):
        df = pd.read_csv("courses_config.csv")
    else:
        df = None

    if df is not None:
        req = {'Course','Credits','PassingGrades','Type'}
        if req.issubset(df.columns):
            # build rules
            target_rules = {}
            intensive_rules = {}
            for _,r in df.iterrows():
                c = r['Course'].strip().upper()
                credits = int(r['Credits'])
                passing = str(r['PassingGrades'])
                ctype = r['Type'].strip().lower()
                fs = sem_to_ord(str(r.get('FromSemester','')) ) or float('-inf')
                ts = sem_to_ord(str(r.get('ToSemester','')) ) or float('inf')
                rule = {'Credits':credits,'PassingGrades':passing,'FromOrd':fs,'ToOrd':ts}
                if ctype=='intensive':
                    intensive_rules.setdefault(c,[]).append(rule)
                else:
                    target_rules.setdefault(c,[]).append(rule)
            st.session_state['target_course_rules'] = target_rules
            st.session_state['intensive_course_rules'] = intensive_rules
            st.success("Loaded course rules.")
        else:
            st.error("CSV must contain Course,Credits,PassingGrades,Type.")
    else:
        st.info("No course configuration found. Please upload.")
