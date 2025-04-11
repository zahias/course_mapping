import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade_from_list, CourseResult, get_allowed_assignment_types

def read_progress_report(filepath):
    """
    Reads the student progress report file (Excel or CSV) and returns a pandas DataFrame.
    It first looks for a "Progress Report" sheet (Excel); if not found, it attempts a wide-format transformation.
    """
    try:
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                if not required_columns.issubset(df.columns):
                    st.error(f"Missing required columns: {required_columns - set(df.columns)}")
                    return None
                return df
            else:
                st.info("No 'Progress Report' sheet found. Processing as wide format.")
                df = pd.read_excel(xls)
                return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course', 'Grade', 'Year', 'Semester'}.issubset(df.columns):
                return df
            else:
                st.info("CSV does not have expected columns. Attempting wide-format transformation.")
                return transform_wide_format(df)
        else:
            st.error("Unrecognized file format.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    """
    Transforms a wide-format file into the standard long-format.
    Expects columns like 'STUDENT ID' and one or more columns starting with 'COURSE'.
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
        st.error("Unable to parse wide format. Expected format: COURSECODE/SEMESTER-YEAR/GRADE.")
        return None
    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()
    sem_year_split = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Unrecognized Semester-Year format (expected e.g., FALL-2016).")
        return None
    df_melted['Semester'] = sem_year_split[0].str.strip().str.title()
    df_melted['Year'] = sem_year_split[1].str.strip()
    df_melted = df_melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})
    required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required_columns.issubset(df_melted.columns):
        st.error(f"Missing columns after transformation: {required_columns - set(df_melted.columns)}")
        return None
    return df_melted[['ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester']].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    """
    Processes the equivalent courses CSV (as a DataFrame) and returns a mapping dictionary.
    """
    mapping = {}
    for idx, row in equivalent_courses_df.iterrows():
        primary_course = row['Course'].strip().upper()
        equivalents = [c.strip().upper() for c in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary_course
    return mapping

def process_progress_report(df, target_courses, intensive_courses, per_student_assignments=None, equivalent_courses_mapping=None):
    """
    Processes the raw progress DataFrame and returns pivot tables.
    Each course cell is processed to yield a CourseResult object.
    - target_courses: dict mapping course code to its configuration for required courses.
    - intensive_courses: similar dict for intensive courses.
    - per_student_assignments: dict of dynamic course assignments.
    - equivalent_courses_mapping: mapping for equivalent courses.
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))
    if per_student_assignments:
        allowed_assignment_types = get_allowed_assignment_types()
        def map_assignment(row):
            student_id = str(row['ID'])
            course = row['Course']
            mapped = row['Mapped Course']
            if student_id in per_student_assignments:
                assignments = per_student_assignments[student_id]
                for a in allowed_assignment_types:
                    if assignments.get(a) == course:
                        return a
            return mapped
        df['Mapped Course'] = df.apply(map_assignment, axis=1)

    # Create pivot table for required courses.
    pivot_df = df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(x.dropna().astype(str))
    ).reset_index()
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None
        pivot_df[course] = pivot_df[course].apply(lambda grade: determine_course_value(grade, course, target_courses))
    
    # Create pivot table for intensive courses.
    intensive_df = df[df['Mapped Course'].isin(intensive_courses.keys())]
    intensive_pivot_df = intensive_df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(x.dropna().astype(str))
    ).reset_index()
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None
        intensive_pivot_df[course] = intensive_pivot_df[course].apply(lambda grade: determine_course_value(grade, course, intensive_courses))
    
    # Extra courses for assignment editing.
    extra_courses_df = df[~df['Mapped Course'].isin(list(target_courses.keys()) + list(intensive_courses.keys()))]
    extra_courses_list = sorted(extra_courses_df['Course'].unique())
    return pivot_df, intensive_pivot_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    """
    Processes a student's grade for a course and returns a CourseResult object.
    
    The course configuration includes:
      - Credits: int (course credit value)
      - PassingGrades: str (a comma-separated list of accepted passing grade tokens)
    
    Output:
      - For courses with credits > 0:
          * If passed, returns: "grade tokens | credits", passed = True.
          * If failed, returns: "grade tokens | 0", passed = False.
      - For 0-credit courses:
          * If passed, returns: "grade tokens | PASS", passed = True.
          * If failed, returns: "grade tokens | FAIL", passed = False.
      - If the grade is missing, returns "NR" and passed = False.
      - If the grade is empty (currently registered), returns "CR | credits" with passed = None.
    """
    config = courses_dict[course]
    credits = config["Credits"]
    passing_grades = [p.strip().upper() for p in config["PassingGrades"].split(',')]
    
    if pd.isna(grade):
        return CourseResult(display="NR", passed=False, credit=0)
    elif grade == '':
        return CourseResult(display=f"CR | {credits}", passed=None, credit=credits)
    else:
        tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
        display_tokens = ', '.join(tokens)
        passed = any(g in passing_grades for g in tokens)
        if credits > 0:
            if passed:
                return CourseResult(display=f"{display_tokens} | {credits}", passed=True, credit=credits)
            else:
                return CourseResult(display=f"{display_tokens} | 0", passed=False, credit=0)
        else:
            if passed:
                return CourseResult(display=f"{display_tokens} | PASS", passed=True, credit=0)
            else:
                return CourseResult(display=f"{display_tokens} | FAIL", passed=False, credit=0)

def calculate_credits(row, courses_dict):
    """
    Calculates for a given student (row) the following:
      - Total credits completed (only courses where passed is True)
      - Registered credits (courses with "CR")
      - Remaining credits (courses failed or not registered)
      - Total potential credits.
      
    Works by examining each course cell (a CourseResult object).
    """
    completed, registered, remaining = 0, 0, 0
    total_credits = 0
    for course, config in courses_dict.items():
        credit = config["Credits"]
        total_credits += credit
        cell_val = row.get(course, None)
        if isinstance(cell_val, CourseResult):
            if cell_val.display.upper().startswith("CR"):
                registered += credit
            elif cell_val.passed is True:
                completed += credit
            else:
                remaining += credit
        else:
            remaining += credit
    return pd.Series([completed, registered, remaining, total_credits],
                     index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits'])
