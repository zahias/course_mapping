# main.py  (UPDATED)

import streamlit as st
import pandas as pd
from pathlib import Path

# ---- your existing imports remain ----
# from data_processing import read_progress_report, process_progress_report, ...
# from ui_components import ... (whatever you already had)
# from config import ... (whatever you already had)

# ------------------------------------------------------------
# NEW: bridge helpers to feed the Advising pages seamlessly
# ------------------------------------------------------------

def _normalize_course_code(x: str) -> str:
    try:
        return str(x).strip().upper()
    except Exception:
        return str(x)

def _build_advising_progress_wide(long_df: pd.DataFrame, courses_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a wide progress dataframe for Advising:
      - Columns: ID, NAME, one column per Course Code found in courses_df
      - Cell values per course: 'c' (completed), 'NR' (currently registered), '' (not completed / not registered)
      - Adds '# of Credits Completed' and '# Registered' columns based on courses_df['Credits'].
    Assumptions:
      - long_df has columns ['ID','NAME','Course','Grade','Year','Semester']
      - Grade 'c' (any case) means completed; 'NR' means currently registered; otherwise blank/other means not completed.
    """
    if long_df is None or long_df.empty:
        return pd.DataFrame()

    # Normalize
    df = long_df.copy()
    req_cols = {'ID', 'NAME', 'Course', 'Grade'}
    missing = req_cols - set(df.columns)
    if missing:
        # Try to soft-fix some common casing issues
        cols_map = {}
        for c in list(df.columns):
            cu = c.strip().upper()
            if cu == 'STUDENT ID' and 'ID' not in df.columns: cols_map[c] = 'ID'
            if cu == 'NAME' and 'NAME' not in df.columns: cols_map[c] = 'NAME'
            if cu == 'COURSE' and 'Course' not in df.columns: cols_map[c] = 'Course'
            if cu == 'GRADE' and 'Grade' not in df.columns: cols_map[c] = 'Grade'
        if cols_map:
            df = df.rename(columns=cols_map)
        missing = req_cols - set(df.columns)
        if missing:
            st.warning(f"Progress data missing required columns for advising: {missing}")
            return pd.DataFrame()

    df['Course'] = df['Course'].apply(_normalize_course_code)
    df['Grade']  = df['Grade'].astype(str).str.strip()

    # Derive status per attempt
    # 'c' (any case) => completed, 'NR' => currently registered, else ''
    df['__status__'] = df['Grade'].apply(lambda g: 'c' if str(g).lower() == 'c'
                                         else ('NR' if str(g).upper() == 'NR' else ''))

    # Choose the "best" status per (ID, Course) if multiple attempts exist:
    # completed beats NR beats blank
    def _pick_status(series):
        vals = set(series.dropna().astype(str))
        if 'c' in vals or 'C' in vals:
            return 'c'
        if 'NR' in vals:
            return 'NR'
        return ''

    # Limit courses to those present in the (merged) courses table if provided
    if courses_df is not None and not courses_df.empty and 'Course Code' in courses_df.columns:
        valid_courses = courses_df['Course Code'].apply(_normalize_course_code).tolist()
        df = df[df['Course'].isin(valid_courses)]
    else:
        valid_courses = sorted(df['Course'].unique())

    # Pivot to wide
    wide = (
        df.pivot_table(index=['ID', 'NAME'],
                       columns='Course',
                       values='__status__',
                       aggfunc=_pick_status)
        .reset_index()
        .rename_axis(None, axis=1)
    )

    # Ensure all valid course columns exist
    for c in valid_courses:
        if c not in wide.columns:
            wide[c] = ''

    # Reorder: ID, NAME, then sorted course codes by courses_df order if available
    if courses_df is not None and 'Course Code' in courses_df.columns:
        order = ['ID', 'NAME'] + list(courses_df['Course Code'].apply(_normalize_course_code))
        wide = wide[[col for col in order if col in wide.columns]]
    else:
        other = sorted([c for c in wide.columns if c not in ('ID','NAME')])
        wide = wide[['ID','NAME'] + other]

    # Compute # Completed and # Registered from Credits
    completed = []
    registered = []
    credit_map = {}
    if courses_df is not None and 'Course Code' in courses_df.columns and 'Credits' in courses_df.columns:
        ctmp = courses_df.copy()
        ctmp['Course Code'] = ctmp['Course Code'].apply(_normalize_course_code)
        credit_map = dict(zip(ctmp['Course Code'], ctmp['Credits']))

    for _, row in wide.iterrows():
        comp = reg = 0
        for col in wide.columns:
            if col in ('ID','NAME'): 
                continue
            status = str(row[col]).strip()
            cr = credit_map.get(col, 0)
            if status.lower() == 'c':
                comp += (cr if pd.notna(cr) else 0)
            elif status.upper() == 'NR':
                reg += (cr if pd.notna(cr) else 0)
        completed.append(comp)
        registered.append(reg)

    wide['# of Credits Completed'] = completed
    wide['# Registered'] = registered

    return wide

def ensure_advising_session_state():
    """
    Populate the exact session keys the Advising pages expect:
      - st.session_state.courses_df: unified courses table (must include Course Code, Credits, Offered, Prerequisite, Concurrent, Corequisite, Type)
      - st.session_state.progress_df: WIDE student progress (ID, NAME, each course col, # of Credits Completed, # Registered)
      - st.session_state.advising_selections: dict per student
    This function is SAFE to call multiple times.
    """
    # 1) courses_df: try to locate your existing unified/merged courses config
    #    We don't force a specific filename here — assume your app already loaded it to session_state earlier.
    if 'courses_df' not in st.session_state or st.session_state.courses_df is None or st.session_state.courses_df.empty:
        # Try common fallback: if you store per-major courses in session already, set it here.
        # Otherwise, leave a non-blocking warning.
        st.session_state.setdefault('courses_df', pd.DataFrame())
        st.info("Courses table not loaded into session_state.courses_df yet. Advising pages will remain disabled until you load it on the main page.")

    # 2) progress_df (WIDE): build from your long-form in memory if present
    #    Your Course Mapping app likely stored a long df as f"{major}_raw_df". If you store a single global, set it to 'raw_progress_df'.
    raw_candidates = []
    for k in list(st.session_state.keys()):
        if k.endswith('_raw_df') and isinstance(st.session_state[k], pd.DataFrame):
            raw_candidates.append(k)
    if 'raw_progress_df' in st.session_state and isinstance(st.session_state['raw_progress_df'], pd.DataFrame):
        raw_candidates.append('raw_progress_df')

    if raw_candidates:
        # Choose the most recently set key (last one)
        raw_key = raw_candidates[-1]
        long_df = st.session_state[raw_key]
        st.session_state['progress_df'] = _build_advising_progress_wide(long_df, st.session_state.get('courses_df', pd.DataFrame()))
    else:
        # If your app already produced a WIDE progress matrix that matches the advising format, reuse it:
        if 'progress_df' not in st.session_state:
            st.session_state['progress_df'] = pd.DataFrame()

    # 3) advising selections holder
    if 'advising_selections' not in st.session_state or not isinstance(st.session_state.advising_selections, dict):
        st.session_state['advising_selections'] = {}

# ------------------------------------------------------------
# END bridge helpers
# ------------------------------------------------------------

# ----------------------------------------------------------------------------
# Your existing main() or page layout code...
# ----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Course Mapping & Advising", layout="wide")
    st.title("Course Mapping App")

    # ... your current main workflow goes here (uploads, parsing, reports, etc.)

    # >>> At the end of your upload/parse pipeline (or after each successful load):
    ensure_advising_session_state()

    st.success("Advising data initialized — open the '5_Advising' page to start advising.")

if __name__ == "__main__":
    main()
