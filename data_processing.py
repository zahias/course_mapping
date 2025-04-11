import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade_from_list, get_allowed_assignment_types

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
                st.info("CSV missing expected columns – attempting wide format.")
                df = transform_wide_format(df)
                return df
        else:
            st.error("Unrecognized file format.")
            return None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format file missing 'STUDENT ID' or COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melted = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    df_melted = df_melted[df_melted['CourseData'].notnull() & (df_melted['CourseData'] != '')]
    split_cols = df_melted['CourseData'].str.split('/', expand=True)
    if split_cols.shape[1] < 3:
        st.error("Course data parsing failed. Expected: COURSECODE/SEMESTER-YEAR/GRADE.")
        return None
    df_melted['Course'] = split_cols[0].str.strip().str.upper()
    df_melted['Semester_Year'] = split_cols[1].str.strip()
    df_melted['Grade'] = split_cols[2].str.strip().str.upper()
    sem_year = df_melted['Semester_Year'].str.split('-', expand=True)
    if sem_year.shape[1] < 2:
        st.error("Semester-Year format unrecognized.")
        return None
    df_melted['Semester'] = sem_year[0].str.strip().str.title()
    df_melted['Year'] = sem_year[1].str.strip()
    df_melted = df_melted.rename(columns={'STUDENT ID': 'ID', 'NAME': 'NAME'})
    required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
    if not required_columns.issubset(df_melted.columns):
        st.error(f"Transformed data missing columns: {required_columns - set(df_melted.columns)}")
        return None
    return df_melted[['ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester']].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for idx, row in equivalent_courses_df.iterrows():
        primary = row['Course'].strip().upper()
        equivalents = [x.strip().upper() for x in str(row['Equivalent']).split(',')]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping

def process_progress_report(df, target_courses, intensive_courses, per_student_assignments=None, equivalent_courses_mapping=None):
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
                for atype in allowed_assignment_types:
                    if assignments.get(atype) == course:
                        return atype
            return mapped
        df['Mapped Course'] = df.apply(map_assignment, axis=1)
    extra_courses_df = df[
        (~df['Mapped Course'].isin(target_courses.keys())) &
        (~df['Mapped Course'].isin(intensive_courses.keys()))
    ]
    target_df = df[df['Mapped Course'].isin(target_courses.keys())]
    intensive_df = df[df['Mapped Course'].isin(intensive_courses.keys())]
    pivot_df = target_df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(map(str, filter(pd.notna, x)))
    ).reset_index()
    intensive_pivot_df = intensive_df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(map(str, filter(pd.notna, x)))
    ).reset_index()
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None
        pivot_df[course] = pivot_df[course].apply(lambda grade: determine_course_value(grade, course, target_courses))
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None
        intensive_pivot_df[course] = intensive_pivot_df[course].apply(lambda grade: determine_course_value(grade, course, intensive_courses))
    result_df = pivot_df[['ID', 'NAME'] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[['ID', 'NAME'] + list(intensive_courses.keys())]
    if per_student_assignments:
        assigned_courses = []
        for sid, assignments in per_student_assignments.items():
            for atype, course in assignments.items():
                assigned_courses.append((sid, course))
        extra_courses_df = extra_courses_df[~extra_courses_df.apply(lambda row: (str(row['ID']), row['Course']) in assigned_courses, axis=1)]
    extra_courses_list = sorted(extra_courses_df['Course'].unique())
    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    """
    Processes a course grade and returns a string in the format:
       "grade tokens | credits | marker"
       
    - If the grade is missing (NaN), returns: "NR | {credits} | FAIL"
    - If the grade is empty (registered but no grade yet), returns: "CR | {credits} | FAIL"
    - Otherwise, splits the grade string (by commas) into tokens, and then checks
      whether any token (after uppercasing and trimming) is present in the course's PassingGrades.
         - If yes, the marker is "PASS".
         - Otherwise, marker is "FAIL".
    
    This method ignores any further nuance—color coding in the UI will depend solely on the marker.
    """
    info = courses_dict[course]
    credits = info["Credits"]
    passing_grades = [x.strip().upper() for x in info["PassingGrades"].split(",")]
    if pd.isna(grade):
        return f"NR | {credits} | FAIL"
    elif grade == "":
        return f"CR | {credits} | FAIL"
    else:
        tokens = [g.strip().upper() for g in grade.split(",") if g.strip()]
        tokens_str = ", ".join(tokens)
        marker = "PASS" if any(token in passing_grades for token in tokens) else "FAIL"
        return f"{tokens_str} | {credits} | {marker}"

def calculate_credits(row, courses_dict):
    completed, registered, remaining = 0, 0, 0
    total_credits = 0
    for course, info in courses_dict.items():
        credit = info["Credits"]
        total_credits += credit
        value = row.get(course, '')
        if isinstance(value, str):
            value = value.strip()
            if value.upper().startswith("CR"):
                registered += credit
            elif value.upper().startswith("NR"):
                remaining += credit
            else:
                parts = value.split("|")
                if len(parts) >= 3:
                    marker = parts[2].strip().upper()
                    if marker == "PASS":
                        completed += credit
                    else:
                        remaining += credit
                else:
                    remaining += credit
        else:
            remaining += credit
    return pd.Series([completed, registered, remaining, total_credits],
                     index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits'])

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color
    output = io.BytesIO()
    workbook = Workbook()
    ws_required = workbook.active
    ws_required.title = "Required Courses"
    light_green_fill = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink_fill = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_required.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                if value == 'c':
                    cell.fill = light_green_fill
                elif value == '':
                    cell.fill = pink_fill
                else:
                    cell.fill = cell_color(str(value))
    ws_intensive = workbook.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_intensive.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                if value == 'c':
                    cell.fill = light_green_fill
                elif value == '':
                    cell.fill = pink_fill
                else:
                    cell.fill = cell_color(str(value))
    workbook.save(output)
    output.seek(0)
    return output
