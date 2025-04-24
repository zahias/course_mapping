<<<<<<< HEAD
# customize_courses.py

import streamlit as st
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> parent of a8b67f1 (4)
from config import is_passing_grade_from_list, get_allowed_assignment_types
<<<<<<< HEAD
=======
from config import get_default_grading_system
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import PatternFill, Font, Alignment
import io

# Semester ordering for comparisons
SEM_ORDER = {'Fall': 1, 'Spring': 2, 'Summer': 3}


def read_progress_report(filepath):
    """
    Reads an uploaded Excel or CSV and returns a normalized DataFrame
    with columns: ID, NAME, Course, Grade, Year (int), Semester ('Spring','Summer','Fall').
=======
from config import get_allowed_assignment_types
=======
from config import is_passing_grade_from_list, get_allowed_assignment_types
>>>>>>> parent of abfac76 (3)
=======
from config import is_passing_grade_from_list, GRADE_ORDER, get_allowed_assignment_types
>>>>>>> parent of 2e22e23 (Update data_processing.py)
=======
from config import get_allowed_assignment_types
>>>>>>> parent of 02f20b1 (e)
=======
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
>>>>>>> parent of ee6adbc (Revert "Update data_processing.py")
=======
import pandas as pd
import streamlit as st
<<<<<<< HEAD
from config import get_allowed_assignment_types
>>>>>>> parent of 52afd51 (Revert "Update data_processing.py")

def read_progress_report(filepath):
    """
    Reads an uploaded Progress Report (Excel or CSV) and returns a normalized DataFrame
    with columns: ID, NAME, Course, Grade, Year, Semester.
    """
=======
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

def read_progress_report(filepath):
>>>>>>> parent of e37c21f (e)
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required_columns.issubset(df.columns):
                    st.error(f"Missing columns: {required_columns - set(df.columns)}")
                    return None
                return df
            else:
<<<<<<< HEAD
                st.info("No 'Progress Report' sheet found. Attempting wide-format transform.")
                df = pd.read_excel(xls)
                df = transform_wide_format(df)
                if df is None:
                    st.error("Wide-format transformation failed.")
                return df

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
def select_config(defs, record_code):
    """
    From a list of definitions, select the one whose [Eff_From, Eff_To]
    range includes record_code. If multiple, pick the one with the largest Eff_From.
>>>>>>> parent of 98d5b2a (3)
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required.issubset(df.columns):
                    st.error(f"Missing columns: {required - set(df.columns)}")
                    return None
                return df
            # fallback to wide
            df = pd.read_excel(xls)
            return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            return transform_wide_format(df)
        else:
            st.error("Unsupported file type.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def transform_wide_format(df):
    """
    Transforms a 'wide' student‑courses sheet (with COURSE1, COURSE2, ... columns)
    into the normalized long format.
    """
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Cannot parse wide format: missing 'STUDENT ID' or COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    melted = melted[melted['CourseData'].notna() & (melted['CourseData'] != '')]
    parts = melted['CourseData'].str.split('/', expand=True)
    if parts.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE in wide data.")
        return None

    melted['Course'] = parts[0].str.strip().str.upper()
    melted['Semester_Year'] = parts[1].str.strip()
    melted['Grade'] = parts[2].str.strip().str.upper()

    sy = melted['Semester_Year'].str.split('-', expand=True)
    if sy.shape[1] < 2:
        st.error("Expected SEMESTER-YEAR format like 'FALL-2016'.")
        return None
    melted['Semester'] = sy[0].str.strip().str.title()
    melted['Year'] = sy[1].str.strip()

    melted = melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})
    required = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required.issubset(melted.columns):
        st.error(f"Missing after transform: {required - set(melted.columns)}")
        return None

    melted['Year'] = melted['Year'].astype(int, errors='ignore')
    return melted[list(required)].drop_duplicates()


def read_equivalent_courses(equivalent_courses_df):
    """
    From a DataFrame with columns ['Course','Equivalent'], builds a mapping
    of each equivalent -> primary Course.
    """
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        eqs = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in eqs:
=======
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

def read_progress_report(filepath):
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required_columns.issubset(df.columns):
                    st.error(f"Missing columns: {required_columns - set(df.columns)}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet found – processing as wide format.")
                df = pd.read_excel(xls)
                df = transform_wide_format(df)
                if df is None:
                    st.error("Wide format transformation failed.")
                return df
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing expected columns – attempting wide format transformation.")
                df = transform_wide_format(df)
                return df
        else:
            st.error("Unsupported file format. Please upload an Excel or CSV file.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(col.startswith('COURSE') for col in df.columns):
        st.error("Wide format file missing 'STUDENT ID' or COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name="Course_Column", value_name="CourseData")
    df_melted = df_melted[df_melted["CourseData"].notnull() & (df_melted["CourseData"] != "")]
    split_cols = df_melted["CourseData"].str.split("/", expand=True)
    if split_cols.shape[1] < 3:
        st.error("Parsing error: Expected format COURSECODE/SEMESTER-YEAR/GRADE.")
        return None
    df_melted["Course"] = split_cols[0].str.strip().str.upper()
    df_melted["Semester_Year"] = split_cols[1].str.strip()
    df_melted["Grade"] = split_cols[2].str.strip().str.upper()
    sem_year_split = df_melted["Semester_Year"].str.split("-", expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized. Expected e.g. FALL-2016.")
        return None
    df_melted["Semester"] = sem_year_split[0].str.strip().str.title()
    df_melted["Year"] = sem_year_split[1].str.strip()
    df_melted = df_melted.rename(columns={"STUDENT ID": "ID", "NAME": "NAME"})
    req_cols = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
    if not req_cols.issubset(df_melted.columns):
        st.error(f"Missing columns after transformation: {req_cols - set(df_melted.columns)}")
        return None
    return df_melted[list(req_cols)].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for idx, row in equivalent_courses_df.iterrows():
        primary = row["Course"].strip().upper()
        equivalents = [x.strip().upper() for x in str(row["Equivalent"]).split(",")]
        for eq in equivalents:
>>>>>>> parent of e37c21f (e)
            mapping[eq] = primary
    return mapping
>>>>>>> parent of 5a48a63 (Update data_processing.py)
<<<<<<< HEAD
=======
from config import get_allowed_assignment_types
>>>>>>> parent of 98d5b2a (3)
=======
from config import is_passing_grade_from_list, get_allowed_assignment_types
>>>>>>> parent of abfac76 (3)

<<<<<<< HEAD
# Academic semester ordering: Fall → Spring → Summer
SEM_ORDER = {"Fall": 1, "Spring": 2, "Summer": 3}
=======
SEM_ORDER = {'Fall':1, 'Spring':2, 'Summer':3}
>>>>>>> parent of dd799ab (Revert "4")

=======
>>>>>>> parent of abfac76 (3)
def read_progress_report(filepath):
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                missing = required_columns - set(df.columns)
                if missing:
                    st.error(f"Missing columns: {missing}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet; attempting wide‑format transform.")
                df = pd.read_excel(xls)
                return transform_wide_format(df)
=======
>>>>>>> parent of 52afd51 (Revert "Update data_processing.py")
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
<<<<<<< HEAD
                st.info("CSV missing expected columns; attempting wide‑format transform.")
                return transform_wide_format(df)
        else:
            st.error("Unsupported file format. Upload Excel or CSV.")
            return None
    except Exception as e:
        st.error(f"Error reading progress report: {e}")
        return None
<<<<<<< HEAD

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format requires 'STUDENT ID' and COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notna() & (df_melted['CourseData'] != '')]
    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE format.")
        return None
    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()
    sem_year = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year.shape[1] < 2:
        st.error("Semester-Year not recognized (e.g. 'FALL-2016').")
        return None
    df_melted['Semester'] = sem_year[0].str.title().str.strip()
    df_melted['Year'] = sem_year[1].astype(int)
    df_melted = df_melted.rename(columns={'STUDENT ID':'ID', 'NAME':'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(df_melted.columns):
        st.error(f"After transform missing: {req - set(df_melted.columns)}")
        return None
    return df_melted[['ID','NAME','Course','Grade','Year','Semester']].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    if equivalent_courses_df is None:
        return mapping
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping

def _term_to_tuple(year: int, semester: str):
    """Convert (year,semester) to a tuple that respects Fall→Spring→Summer order."""
    return (int(year), SEM_ORDER.get(semester.title(), 0))

def select_course_definition(defs: list, year: int, semester: str) -> dict:
=======
def select_course_definition(defs, year, sem):
<<<<<<< HEAD
>>>>>>> parent of 2e22e23 (Update data_processing.py)
    """
    From a list of definitions (each with Effective_From/To),
    pick the one whose date‑range includes (year,sem). If multiple,
    choose the one with the latest Effective_From. If none match,
    fallback to the first definition.
    """
    candidates = []
    for d in defs:
<<<<<<< HEAD
<<<<<<< HEAD
        ef = d.get('Effective_From')
        if ef:
            ef_term = (ef[1], SEM_ORDER.get(ef[0], 0))
        else:
            ef_term = (0, 0)
        candidates.append((d, ef_term))
    # Definitions that have started by this term
    valid = [(d, t) for (d, t) in candidates if t <= term]
    if valid:
        # Choose the one whose start is most recent
        chosen = max(valid, key=lambda x: x[1])[0]
    else:
        # No definition started yet; use the earliest one
        chosen = min(candidates, key=lambda x: x[1])[0]
    return chosen

def determine_course_value(grade, course, courses_config, year, semester):
    """
    Time‐aware grade processing:
      - Null → 'NR'
      - Empty → 'CR | credits'
      - Otherwise split on ',', check passing via the selected definition's PassingGrades
    """
    defs = courses_config.get(course, [])
    if not defs:
        return 'NR'
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    pass_list = cfg['PassingGrades']
    if pd.isna(grade):
        return 'NR'
    if grade == '':
        return f'CR | {credits}'
    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, pass_list) for tok in tokens)
    token_str = ', '.join(tokens)
    if credits > 0:
        return f'{token_str} | {credits}' if passed else f'{token_str} | 0'
    else:
        return f'{token_str} | PASS' if passed else f'{token_str} | FAIL'
=======
        ef = d['Eff_From']
        et = d['Eff_To']
        ok_from = (ef is None) or (record_code >= ef)
        ok_to   = (et is None) or (record_code <= et)
=======

# Academic semester ordering for comparisons
SEM_ORDER = {'Fall': 1, 'Spring': 2, 'Summer': 3}

def select_course_definition(defs, year, sem):
    """
    From defs (a list of course‐config entries), pick the one whose
    Effective_From/To includes (year, sem). If none match, return defs[0].
    """
    candidates = []
    for d in defs:
        ef = d['Effective_From']
        et = d['Effective_To']
        ok_from = True
        if ef:
            e_sem, e_yr = ef
            if (year < e_yr) or (year == e_yr and SEM_ORDER[sem] < SEM_ORDER[e_sem]):
                ok_from = False
        ok_to = True
        if et:
            t_sem, t_yr = et
            if (year > t_yr) or (year == t_yr and SEM_ORDER[sem] > SEM_ORDER[t_sem]):
                ok_to = False
>>>>>>> parent of a8b67f1 (4)
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
        # Pick the one with the latest Effective_From
        def keyfn(d):
            ef = d['Effective_From']
            if not ef:
                return (0, 0)
            s, y = ef
            return (y, SEM_ORDER[s])
        return max(candidates, key=keyfn)
    return defs[0]
=======
>>>>>>> parent of abfac76 (3)

<<<<<<< HEAD
def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format requires 'STUDENT ID' and COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notna() & (df_melted['CourseData'] != '')]
    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Expected COURSECODE/SEMESTER-YEAR/GRADE format.")
        return None
    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()
    sem_year = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year.shape[1] < 2:
        st.error("Semester-Year not recognized (e.g. 'FALL-2016').")
        return None
    df_melted['Semester'] = sem_year[0].str.title().str.strip()
    df_melted['Year'] = sem_year[1].astype(int)
    df_melted = df_melted.rename(columns={'STUDENT ID':'ID', 'NAME':'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(df_melted.columns):
        st.error(f"After transform missing: {req - set(df_melted.columns)}")
        return None
    return df_melted[['ID','NAME','Course','Grade','Year','Semester']].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    if equivalent_courses_df is None:
        return mapping
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping
>>>>>>> parent of 98d5b2a (3)
=======
def determine_course_value(grade, course, courses_cfg, year, semester):
    """
    Time‐aware grading: pick the correct cfg entry for (year,semester),
    then test grade tokens against its PassingGrades; return "tokens | credits" or "tokens | 0"/PASS/FAIL.
    """
    defs = courses_cfg.get(course, [])
    if not defs:
        st.error(f"No configuration for course {course}")
        return "NR"
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    passing = cfg['PassingGrades']
    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}"
    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, passing) for tok in tokens)
    tokstr = ", ".join(tokens)
    if credits > 0:
        return f"{tokstr} | {credits}" if passed else f"{tokstr} | 0"
    else:
        return f"{tokstr} | PASS" if passed else f"{tokstr} | FAIL"
>>>>>>> parent of a8b67f1 (4)

<<<<<<< HEAD
def process_progress_report(
    df: pd.DataFrame,
    target_cfg: dict,
    intensive_cfg: dict,
    per_student_assignments: dict = None,
    equivalent_courses_mapping: dict = None
):
<<<<<<< HEAD
<<<<<<< HEAD
    # 1) Apply equivalent‐course mapping
=======
    # 1) Compute a record code per row
    df['RecordCode'] = df.apply(
        lambda r: int(r['Year']) * 3 + SEM_INDEX[r['Semester']],
        axis=1
    )

    # 2) Map equivalent courses
>>>>>>> parent of 98d5b2a (3)
=======
def _term_to_tuple(year: int, semester: str):
    """Convert (year,semester) to a tuple that respects Fall→Spring→Summer order."""
    return (int(year), SEM_ORDER.get(semester.title(), 0))

def select_course_definition(defs: list, year: int, semester: str) -> dict:
    """
    From a list of course‐definition dicts (each with an optional Effective_From),
    pick the one whose Effective_From is the latest date <= the student’s term.
    If none apply, fall back to the definition with the earliest Effective_From.
    """
    term = _term_to_tuple(year, semester)
    candidates = []
    for d in defs:
        ef = d.get('Effective_From')
=======
        ok_from = True
        ef = d['Effective_From']
>>>>>>> parent of 2e22e23 (Update data_processing.py)
        if ef:
            e_sem, e_year = ef
            if (year < e_year) or (year==e_year and SEM_ORDER[sem]<SEM_ORDER[e_sem]):
=======
    candidates = []
    for d in defs:
        ef, et = d['Effective_From'], d['Effective_To']
        ok_from = True
        if ef:
            e_sem, e_yr = ef
            if (year < e_yr) or (year==e_yr and SEM_ORDER[sem] < SEM_ORDER[e_sem]):
>>>>>>> parent of dd799ab (Revert "4")
                ok_from = False
        ok_to = True
        et = d['Effective_To']
        if et:
<<<<<<< HEAD
            t_sem, t_year = et
            if (year > t_year) or (year==t_year and SEM_ORDER[sem]>SEM_ORDER[t_sem]):
=======
            t_sem, t_yr = et
            if (year > t_yr) or (year==t_yr and SEM_ORDER[sem] > SEM_ORDER[t_sem]):
>>>>>>> parent of dd799ab (Revert "4")
                ok_to = False
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
<<<<<<< HEAD
        # pick with max Effective_From date
        def keyfn(d):
            ef = d['Effective_From']
            if not ef:
                return (0,0)
            s,y = ef
            return (y, SEM_ORDER[s])
        return max(candidates, key=keyfn)
    return defs[0]

def determine_course_value(grade, course, courses_config, year, semester):
    """
    Time‑aware determine value:
     - Pick appropriate course definition for this (year,semester).
     - Use its PassingGrades and Credits.
     - Then same logic: if grade missing→NR; if ""→CR; else test passing via is_passing_grade_from_list.
    """
    defs = courses_config.get(course)
=======
        # latest Effective_From
        def keyfn(d):
            ef = d['Effective_From']
            return (ef[1], SEM_ORDER[ef[0]]) if ef else (0,0)
        return max(candidates, key=keyfn)
    return defs[0]

def determine_course_value(grade, course, courses_cfg, year, semester):
    defs = courses_cfg.get(course, [])
>>>>>>> parent of dd799ab (Revert "4")
    if not defs:
        st.error(f"No config for course {course}")
        return "NR"
    cfg = select_course_definition(defs, year, semester)
<<<<<<< HEAD
    credits = cfg['Credits']
    pass_str = cfg['PassingGrades']
=======
    credits, passing = cfg['Credits'], cfg['PassingGrades']
>>>>>>> parent of dd799ab (Revert "4")
    if pd.isna(grade):
        return "NR"
    if grade=="":
        return f"CR | {credits}"
<<<<<<< HEAD
    tokens = [g.strip().upper() for g in grade.split(',')]
    passed = any(is_passing_grade_from_list(tok,pass_str) for tok in tokens)
    toklist = ", ".join(tokens)
    if credits>0:
        return f"{toklist} | {credits}" if passed else f"{toklist} | 0"
=======
    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, passing) for tok in tokens)
    tokstr = ", ".join(tokens)
    if credits>0:
        return f"{tokstr} | {credits}" if passed else f"{tokstr} | 0"
>>>>>>> parent of dd799ab (Revert "4")
    else:
        return f"{toklist} | PASS" if passed else f"{toklist} | FAIL"
=======
def read_equivalent_courses(equiv_df):
=======
                st.info("No 'Progress Report' sheet found – processing as wide format.")
                df = pd.read_excel(xls)
                df = transform_wide_format(df)
                if df is None:
                    st.error("Wide format transformation failed.")
                return df
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV missing expected columns – attempting wide format transformation.")
                df = transform_wide_format(df)
                return df
        else:
            st.error("Unsupported file format. Please upload an Excel or CSV file.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(col.startswith('COURSE') for col in df.columns):
        st.error("Wide format file missing 'STUDENT ID' or COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name="Course_Column", value_name="CourseData")
    df_melted = df_melted[df_melted["CourseData"].notnull() & (df_melted["CourseData"] != "")]
    split_cols = df_melted["CourseData"].str.split("/", expand=True)
    if split_cols.shape[1] < 3:
        st.error("Parsing error: Expected format COURSECODE/SEMESTER-YEAR/GRADE.")
        return None
    df_melted["Course"] = split_cols[0].str.strip().str.upper()
    df_melted["Semester_Year"] = split_cols[1].str.strip()
    df_melted["Grade"] = split_cols[2].str.strip().str.upper()
    sem_year_split = df_melted["Semester_Year"].str.split("-", expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized. Expected e.g. FALL-2016.")
        return None
    df_melted["Semester"] = sem_year_split[0].str.strip().str.title()
    df_melted["Year"] = sem_year_split[1].str.strip()
    df_melted = df_melted.rename(columns={"STUDENT ID": "ID", "NAME": "NAME"})
    req_cols = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
    if not req_cols.issubset(df_melted.columns):
        st.error(f"Missing columns after transformation: {req_cols - set(df_melted.columns)}")
        return None
    return df_melted[list(req_cols)].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
>>>>>>> parent of e37c21f (e)
    mapping = {}
    for idx, row in equivalent_courses_df.iterrows():
        primary = row["Course"].strip().upper()
        equivalents = [x.strip().upper() for x in str(row["Equivalent"]).split(",")]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping
>>>>>>> parent of 02f20b1 (e)

<<<<<<< HEAD
def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None,
    course_rules=None
):
<<<<<<< HEAD
<<<<<<< HEAD
    # 1) Apply equivalent‐course mapping
>>>>>>> parent of abfac76 (3)
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
<<<<<<< HEAD
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

<<<<<<< HEAD
<<<<<<< HEAD
    # 2) Apply S.C.E./F.E.C. assignments
=======
    # Map equivalents
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x,x))
    # Apply S.C.E/F.E.C...
>>>>>>> parent of 2e22e23 (Update data_processing.py)
=======
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}
=======
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
=======
                st.info("CSV missing expected columns. Attempting wide-format transform.")
                df = transform_wide_format(df)
                return df

        else:
            st.error("Unsupported file type. Please upload .xlsx, .xls, or .csv.")
            return None

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def transform_wide_format(df):
    """
    Converts a 'wide' style sheet into the long format with ID, NAME, Course, Grade, Year, Semester.
    Expects 'STUDENT ID', 'NAME', and columns named COURSE1, COURSE2, etc. containing 'CODE/SEM-YEAR/GRADE'.
    """
    if 'STUDENT ID' not in df.columns or not any(col.startswith('COURSE') for col in df.columns):
        st.error("Wide-format file missing 'STUDENT ID' or COURSE columns.")
        return None

    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]

    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notnull() & (df_melted['CourseData'] != '')]

    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Could not parse course data (expect CODE/SEMESTER-YEAR/GRADE).")
        return None

    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()

    sem_year_split = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized (expect FALL-2016).")
        return None

    df_melted['Semester'] = sem_year_split[0].str.strip().str.title()
    df_melted['Year'] = sem_year_split[1].str.strip()

    df_melted = df_melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})

    required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required_columns.issubset(df_melted.columns):
        st.error(f"Missing columns after transform: {required_columns - set(df_melted.columns)}")
        return None

    df_final = df_melted[['ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester']].drop_duplicates()
    return df_final


def read_equivalent_courses(equivalent_courses_df):
    """
    Given a DataFrame with columns ['Course','Equivalent'], returns a dict mapping
    each equivalent course code → primary course code.
    """
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping


<<<<<<< HEAD
def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None,
    course_rules=None
):
    """
    Processes the raw long‐format progress DataFrame into three outputs:
      1. Required courses pivot: ID, NAME, each target course → "grade tokens | credits" or "NR"
      2. Intensive courses pivot: same structure for intensive_courses
      3. extra_courses_df: flat DataFrame of courses not in target or intensive
      4. extra_courses_list: sorted list of those extra course codes

    Uses:
      - equivalent_courses_mapping to map course codes
      - per_student_assignments for S.C.E./F.E.C overrides
      - course_rules to decide passing based on semester
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # 1) numeric semester value
    sem_map = {'Spring': 1, 'Summer': 2, 'Fall': 3}
    df['SemValue'] = df['Year'].astype(int) * 10 + df['Semester'].map(sem_map)

    # 2) apply equivalent mapping
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) apply S.C.E./F.E.C. assignments
=======
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    # Map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # Apply assignments (S.C.E. / F.E.C. / etc.)
>>>>>>> parent of a8b67f1 (4)
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID'])
<<<<<<< HEAD
            orig = r['Course']
            mapped = r['Mapped Course']
            if sid in per_student_assignments:
                for atype in allowed:
                    if per_student_assignments[sid].get(atype) == orig:
                        return atype
            return mapped
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 4) determine pass/fail via effective rules
    def passed_flag(r):
        course = r['Mapped Course']
        grade = str(r['Grade']).strip().upper()
        sv = r['SemValue']
        rules = course_rules.get(course, [])
        # pick rule with highest eff <= sv
        appl = [rule for rule in rules if rule['eff'] <= sv]
        if appl:
            rule = max(appl, key=lambda x: x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return grade in rule['passing_grades']

    df['PassedFlag'] = df.apply(passed_flag, axis=1)

    # 5) split into extra / target / intensive
    extra_df = df[
        (~df['Mapped Course'].isin(target_courses)) &
        (~df['Mapped Course'].isin(intensive_courses))
    ]
    targ_df = df[df['Mapped Course'].isin(target_courses)]
    inten_df = df[df['Mapped Course'].isin(intensive_courses)]

    # 6) pivot grades & flags
    pivot_grades = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()

    pivot_passed = targ_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    ipg = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna, map(str,x)))
    ).reset_index()

    ipp = inten_df.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # 7) ensure all columns exist
    for course in target_courses:
        if course not in pivot_grades: pivot_grades[course] = None
        if course not in pivot_passed: pivot_passed[course] = False
    for course in intensive_courses:
        if course not in ipg: ipg[course] = None
        if course not in ipp: ipp[course] = False

    # 8) assemble final grade|credit strings
    def make_cells(gr_row, fl_row, course_dict):
        out = {}
        for course, cred in course_dict.items():
            gs = gr_row.get(course) or ''
            ok = bool(fl_row.get(course))
            if gs == '':
                out[course] = 'NR'
            else:
                out[course] = f"{gs} | {cred if ok else 0}"
        return out

    # required output
    req_out = pivot_grades[['ID','NAME']].copy()
    for i, row in pivot_grades.iterrows():
        cells = make_cells(row, pivot_passed.iloc[i], target_courses)
        for c,v in cells.items():
            req_out.at[i,c] = v

    # intensive output
    int_out = ipg[['ID','NAME']].copy()
    for i, row in ipg.iterrows():
        cells = make_cells(row, ipp.iloc[i], intensive_courses)
        for c,v in cells.items():
            int_out.at[i,c] = v

    extra_list = sorted(extra_df['Course'].unique())
    return req_out, int_out, extra_df, extra_list


def calculate_credits(row, courses_dict):
    """
    Given a row where each course column is "grade tokens | credit" or "NR"/"CR | X"/"CR | PASS",
    returns a Series [completed, registered, remaining, total].
    """
    completed, registered, remaining = 0, 0, 0
    total = 0

    for course, credit in courses_dict.items():
        total += credit
        val = row.get(course, "")
        if isinstance(val, str):
            up = val.upper()
            if up.startswith("CR"):
                registered += credit
            elif up.startswith("NR"):
                remaining += credit
            else:
                parts = val.split("|")
                if len(parts) == 2:
                    right = parts[1].strip()
                    try:
                        num = int(right)
                        if num > 0:
                            completed += credit
                        else:
                            remaining += credit
                    except ValueError:
                        if right.upper() == "PASS":
                            pass
                        else:
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit

    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
>>>>>>> parent of 52afd51 (Revert "Update data_processing.py")
    )
>>>>>>> parent of ee6adbc (Revert "Update data_processing.py")


<<<<<<< HEAD
<<<<<<< HEAD
    # 2) map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c, c))

    # 3) apply S.C.E/F.E.C assignments
>>>>>>> parent of 02f20b1 (e)
=======
def process_progress_report(df, target_courses, intensive_courses, per_student_assignments=None, equivalent_courses_mapping=None):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_courses_mapping.get(x, x))
>>>>>>> parent of e37c21f (e)
=======
def process_progress_report(df, target_courses, intensive_courses, per_student_assignments=None, equivalent_courses_mapping=None):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_courses_mapping.get(x, x))
>>>>>>> parent of e37c21f (e)
    if per_student_assignments:
        allowed_types = get_allowed_assignment_types()
        def map_assignment(row):
            sid = str(row["ID"])
            course = row["Course"]
            mapped = row["Mapped Course"]
            if sid in per_student_assignments:
<<<<<<< HEAD
<<<<<<< HEAD
                for t in allowed:
                    if per_student_assignments[sid].get(t)==c:
                        return t
<<<<<<< HEAD
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign,axis=1)
    # Split into required/intensive/extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) & ~df['Mapped Course'].isin(intensive_cfg)]
    # Pivot
    def pivot_and_process(group_df, cfg_dict):
        piv = group_df.pivot_table(
            index=['ID','NAME'], columns='Mapped Course', values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # Ensure all columns exist
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # Apply determine_course_value
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c], c, cfg_dict, int(r['Year']), r['Semester']
                ),
                axis=1
            )
<<<<<<< HEAD
        # drop Year & Semester before returning
        return piv.drop(columns=['Year','Semester'])
=======
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x,x))

    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid, crs = str(r['ID']), r['Course']
            if sid in per_student_assignments:
                for a in allowed:
                    if per_student_assignments[sid].get(a)==crs:
                        return a
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign,axis=1)

    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[
        ~df['Mapped Course'].isin(target_cfg) &
        ~df['Mapped Course'].isin(intensive_cfg)
    ]

    def pivot_proc(sub, cfg):
        piv = sub.pivot_table(
            index=['ID','NAME','Year','Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        for c in cfg:
            if c not in piv.columns:
                piv[c] = None
        for c in cfg:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c], c, cfg, int(r['Year']), r['Semester']
                ),
                axis=1
            )
        return piv[['ID','NAME'] + list(cfg.keys())]

    req_piv = pivot_proc(req_df, target_cfg)
    int_piv = pivot_proc(int_df, intensive_cfg)
>>>>>>> parent of dd799ab (Revert "4")

<<<<<<< HEAD
<<<<<<< HEAD
=======
            crs = r['Course']
            if sid in per_student_assignments:
                for a in allowed:
                    if per_student_assignments[sid].get(a) == crs:
                        return a
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # Partition
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[
        ~df['Mapped Course'].isin(target_cfg)
        & ~df['Mapped Course'].isin(intensive_cfg)
    ]

    # Pivot & process
    def pivot_process(subdf, cfg_dict):
        piv = subdf.pivot_table(
            index=['ID','NAME','Year','Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # Ensure all columns
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # Apply time‐aware grading
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c],
                    c,
                    cfg_dict,
                    int(r['Year']),
                    r['Semester']
                ),
                axis=1
            )
        # Drop Year,Semester for final
        return piv[['ID','NAME'] + list(cfg_dict.keys())]

    req_piv = pivot_process(req_df, target_cfg)
    int_piv = pivot_process(int_df, intensive_cfg)

>>>>>>> parent of a8b67f1 (4)
    return req_piv, int_piv, extra_df, sorted(extra_df['Course'].unique())

def calculate_credits(row, credits_dict):
    """
    row: a series containing course columns with values like "A | 3" or "F | 0"
    credits_dict: {course: credit}
    """
    completed = registered = remaining = 0
    total = sum(credits_dict.values())
    for course, cred in credits_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            u = val.upper()
            if u.startswith("CR"):
                registered += cred
            elif u.startswith("NR"):
                remaining += cred
            else:
                parts = val.split("|")
                if len(parts)==2:
                    rgh = parts[1].strip()
                    try:
                        num = int(rgh)
                        if num>0:
                            completed += cred
                        else:
                            remaining += cred
                    except ValueError:
                        if rgh.upper()=="PASS":
                            pass
                        else:
                            remaining += cred
                else:
                    remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed','# Registered','# Remaining','Total Credits']
    )
<<<<<<< HEAD
=======


def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    """
    Writes two sheets ('Required Courses', 'Intensive Courses') to an XLSX in memory,
    applying light-green fill for passed credits, pink for missing/failed, and yellow for CR.
    """
    output = io.BytesIO()
    wb = Workbook()

    # Prepare fills
    green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    yellow = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")

    def write_sheet(ws, df):
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    if isinstance(val, str):
                        u = val.upper()
                        if u.startswith("CR"):
                            cell.fill = yellow
                        else:
                            parts = val.split("|")
                            if len(parts) == 2:
                                right = parts[1].strip()
                                try:
                                    num = int(right)
                                    cell.fill = green if num > 0 else pink
                                except:
                                    cell.fill = green if right.upper() == "PASS" else pink
                            else:
                                cell.fill = pink
                    else:
                        cell.fill = pink

    ws1 = wb.active
    ws1.title = "Required Courses"
    write_sheet(ws1, displayed_df)

    ws2 = wb.create_sheet(title="Intensive Courses")
    write_sheet(ws2, intensive_displayed_df)

    wb.save(output)
    output.seek(0)
    return output
>>>>>>> parent of 5a48a63 (Update data_processing.py)
<<<<<<< HEAD
=======
    extra_list = sorted(extra_df['Course'].unique())
    return req_final, int_final, extra_df, extra_list
>>>>>>> parent of 98d5b2a (3)
=======
    req_pivot = pivot_and_apply(req_df, target_cfg)
    int_pivot = pivot_and_apply(int_df, intensive_cfg)
=======
        return piv[['ID','NAME'] + list(cfg_dict.keys())]
    req_piv = pivot_and_process(req_df, target_cfg)
    int_piv = pivot_and_process(int_df, intensive_cfg)
    # Build extra list
>>>>>>> parent of 2e22e23 (Update data_processing.py)
    extra_list = sorted(extra_df['Course'].unique())
    return req_piv, int_piv, extra_df, extra_list
=======
            return m
        df['Mapped Course'] = df.apply(map_assign, axis=1)
>>>>>>> parent of 02f20b1 (e)

    # 4) determine PassedFlag based on effective rules
    def passed(r):
        course = r['Mapped Course']
        g = str(r['Grade']).strip().upper()
        sv = r['SemValue']
        rules = course_rules.get(course, [])
        # find rule with max eff <= sv
        applicable = [rule for rule in rules if rule['eff']<=sv]
        if applicable:
            rule = max(applicable, key=lambda x:x['eff'])
        elif rules:
            rule = rules[0]
        else:
<<<<<<< HEAD
<<<<<<< HEAD
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed','# Registered','# Remaining','Total Credits']
    )

def save_report_with_formatting(displayed_df, intensive_df, timestamp):
=======
=======
>>>>>>> parent of e37c21f (e)
                assigns = per_student_assignments[sid]
                for atype in allowed_types:
                    if assigns.get(atype) == course:
                        return atype
            return mapped
        df["Mapped Course"] = df.apply(map_assignment, axis=1)
    extra_courses_df = df[
        (~df["Mapped Course"].isin(target_courses.keys())) &
        (~df["Mapped Course"].isin(intensive_courses.keys()))
    ]
    target_df = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]
    pivot_df = target_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="Grade",
        aggfunc=lambda x: ", ".join(map(str, filter(pd.notna, x)))
    ).reset_index()
    intensive_pivot_df = intensive_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="Grade",
        aggfunc=lambda x: ", ".join(map(str, filter(pd.notna, x)))
    ).reset_index()
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None
        pivot_df[course] = pivot_df[course].apply(lambda grade: determine_course_value(grade, course, target_courses))
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None
        intensive_pivot_df[course] = intensive_pivot_df[course].apply(lambda grade: determine_course_value(grade, course, intensive_courses))
    result_df = pivot_df[["ID", "NAME"] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[["ID", "NAME"] + list(intensive_courses.keys())]
    if per_student_assignments:
        assigned = []
        for sid, assigns in per_student_assignments.items():
            for atype, course in assigns.items():
                assigned.append((sid, course))
        extra_courses_df = extra_courses_df[~extra_courses_df.apply(lambda row: (str(row["ID"]), row["Course"]) in assigned, axis=1)]
    extra_courses_list = sorted(extra_courses_df["Course"].unique())
    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    """
    Processes a course grade.
    For courses with nonzero credits:
      - If any token in the student's grade (split by comma) is in the course’s PassingGrades list,
        returns "grade tokens | {credits}".
      - Otherwise, returns "grade tokens | 0".
    For 0-credit courses:
      - Returns "grade tokens | PASS" if passed, and "grade tokens | FAIL" if not.
    """
    info = courses_dict[course]
    credits = info["Credits"]
    passing_grades_str = info["PassingGrades"]
    if pd.isna(grade):
        return "NR"
    elif grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"
    else:
        tokens = [g.strip().upper() for g in grade.split(", ") if g.strip()]
        all_tokens = ", ".join(tokens)
        allowed = [x.strip().upper() for x in passing_grades_str.split(",")]
        passed = any(g in allowed for g in tokens)
        if credits > 0:
            return f"{all_tokens} | {credits}" if passed else f"{all_tokens} | 0"
        else:
            return f"{all_tokens} | PASS" if passed else f"{all_tokens} | FAIL"

def calculate_credits(row, courses_dict):
    completed, registered, remaining = 0, 0, 0
    total = 0
    for course, info in courses_dict.items():
        credit = info["Credits"]
        total += credit
        value = row.get(course, "")
        if isinstance(value, str):
            up_val = value.upper()
            if up_val.startswith("CR"):
                registered += credit
            elif up_val.startswith("NR"):
                remaining += credit
            else:
                parts = value.split("|")
                if len(parts) == 2:
                    right = parts[1].strip()
                    try:
                        num = int(right)
                        if num > 0:
                            completed += credit
                        else:
                            remaining += credit
                    except ValueError:
                        if right.upper() == "PASS":
                            # 0-credit passed; no credit to add, but considered passed
                            pass
                        else:
                            remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit
    return pd.Series([completed, registered, remaining, total],
                     index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"])

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
>>>>>>> parent of e37c21f (e)
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Required Courses"

    light_green = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    # Write Intensive sheet
    ws2 = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
>>>>>>> parent of abfac76 (3)
=======
    # 3) Apply S.C.E./F.E.C. assignments
=======
    # 2) Apply S.C.E./F.E.C. assignments
>>>>>>> parent of abfac76 (3)
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID'])
            course = r['Course']
            for atype in allowed:
                if per_student_assignments.get(sid, {}).get(atype) == course:
                    return atype
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 3) Split into required, intensive, extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) & ~df['Mapped Course'].isin(intensive_cfg)]

    def pivot_and_apply(subdf, cfg_dict):
        # include Year & Semester to pick definitions
        piv = subdf.pivot_table(
            index=['ID','NAME','Year','Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # ensure all course columns exist
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # apply time‐aware determine_course_value
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c], c, cfg_dict, int(r['Year']), r['Semester']
                ),
                axis=1
            )
        # drop Year & Semester before returning
        return piv.drop(columns=['Year','Semester'])

    req_pivot = pivot_and_apply(req_df, target_cfg)
    int_pivot = pivot_and_apply(int_df, intensive_cfg)
    extra_list = sorted(extra_df['Course'].unique())
<<<<<<< HEAD
    return req_final, int_final, extra_df, extra_list
>>>>>>> parent of 98d5b2a (3)
=======

    return req_pivot, int_pivot, extra_df, extra_list

def calculate_credits(row, courses_config, year, semester):
    """
    Recalculate completed/registered/remaining/total credits
    using the time‐aware definition for each course.
    """
    completed = registered = remaining = total = 0
    for course, defs in courses_config.items():
        cfg = select_course_definition(defs, year, semester)
        cred = cfg['Credits']
        total += cred
        val = row.get(course, '')
        if isinstance(val, str) and val.upper().startswith('CR'):
            registered += cred
        elif isinstance(val, str) and val.upper().startswith('NR'):
            remaining += cred
        elif isinstance(val, str):
            parts = val.split('|')
            if len(parts) == 2:
                right = parts[1].strip()
                try:
                    num = int(right)
                    if num > 0:
                        completed += cred
                    else:
                        remaining += cred
                except ValueError:
                    if right.upper() != 'PASS':
                        remaining += cred
            else:
                remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed','# Registered','# Remaining','Total Credits']
    )

def save_report_with_formatting(displayed_df, intensive_df, timestamp):
=======
            return False
        return g in rule['passing_grades']
=======
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
>>>>>>> parent of ee6adbc (Revert "Update data_processing.py")

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

<<<<<<< HEAD
def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
>>>>>>> parent of 02f20b1 (e)
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color
<<<<<<< HEAD

    output = io.BytesIO()
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "Required Courses"

    light_green = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    # Write Intensive sheet
    ws2 = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_df, index=False, header=True), start=1):
        for c_idx, val in enumerate(row, start=1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            else:
                style = cell_color(str(val))
                if 'lightgreen' in style:
                    cell.fill = light_green
                elif '#FFFACD' in style:
                    cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
>>>>>>> parent of abfac76 (3)
=======
            rem += cred
    return pd.Series([comp,reg,rem,tot],
                     index=['# of Credits Completed','# Registered','# Remaining','Total Credits'])
>>>>>>> parent of 2e22e23 (Update data_processing.py)
=======
    output = io.BytesIO()
    workbook = Workbook()
    ws_req = workbook.active
    ws_req.title = "Required Courses"
    light_green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_req.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                if value == "c":
                    cell.fill = light_green
                elif value == "":
                    cell.fill = pink
                else:
                    style = cell_color(str(value))
                    if "lightgreen" in style:
                        cell.fill = light_green
                    elif "#FFFACD" in style:
                        cell.fill = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")
                    else:
                        cell.fill = pink
    ws_int = workbook.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_int.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                if value == "c":
                    cell.fill = light_green
                elif value == "":
                    cell.fill = pink
                else:
                    style = cell_color(str(value))
                    if "lightgreen" in style:
                        cell.fill = light_green
                    elif "#FFFACD" in style:
                        cell.fill = PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")
                    else:
                        cell.fill = pink
    workbook.save(output)
    output.seek(0)
    return output
>>>>>>> parent of 02f20b1 (e)
=======
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
>>>>>>> parent of ee6adbc (Revert "Update data_processing.py")
=======
def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    """
    Exports the displayed DataFrames to a formatted Excel workbook with color
    coding: green for passed/CR, pink for failed/NR.
    """
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb = Workbook()
    ws_req = wb.active
    ws_req.title = "Required Courses"
    green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink  = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")
    yellow= PatternFill(start_color="FFFACD", end_color="FFFACD", fill_type="solid")

    # Write Required sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_req.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                style = cell_color(str(val))
                if "#FFFACD" in style:
                    cell.fill = yellow
                elif "lightgreen" in style:
                    cell.fill = green
                else:
                    cell.fill = pink

    # Write Intensive sheet
    ws_int = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws_int.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                style = cell_color(str(val))
                if "#FFFACD" in style:
                    cell.fill = yellow
                elif "lightgreen" in style:
                    cell.fill = green
                else:
                    cell.fill = pink

    wb.save(output)
    output.seek(0)
    return output
>>>>>>> parent of 52afd51 (Revert "Update data_processing.py")
=======
>>>>>>> parent of a8b67f1 (4)
