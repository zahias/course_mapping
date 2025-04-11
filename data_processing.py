import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

# ... (the functions read_progress_report(), transform_wide_format(), and read_equivalent_courses() remain unchanged)

def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))
    if per_student_assignments:
        allowed_assignment_types = get_allowed_assignment_types()
        def map_assignment(row):
            student_id = str(row['ID'])
            course = row['Course']
            mapped_course = row['Mapped Course']
            if student_id in per_student_assignments:
                assignments = per_student_assignments[student_id]
                for assign_type in allowed_assignment_types:
                    if assignments.get(assign_type) == course:
                        return assign_type
            return mapped_course
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
        pivot_df[course] = pivot_df[course].apply(
            lambda grade: determine_course_value(grade, course, target_courses)
        )
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None
        intensive_pivot_df[course] = intensive_pivot_df[course].apply(
            lambda grade: determine_course_value(grade, course, intensive_courses)
        )
    result_df = pivot_df[['ID', 'NAME'] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[['ID', 'NAME'] + list(intensive_courses.keys())]
    if per_student_assignments:
        assigned_courses = []
        for student_id, assignments in per_student_assignments.items():
            for assign_type, course in assignments.items():
                assigned_courses.append((student_id, course))
        extra_courses_df = extra_courses_df[
            ~extra_courses_df.apply(lambda row: (str(row['ID']), row['Course']) in assigned_courses, axis=1)
        ]
    extra_courses_list = sorted(extra_courses_df['Course'].unique())
    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict):
    # Retrieve course info; note that "PassingGrades" is a comma-separated string now.
    info = courses_dict[course]
    credits = info["Credits"]
    # Parse the list of passing grades from the configuration string.
    passing_grades = [g.strip().upper() for g in info["PassingGrades"].split(',')]
    if pd.isna(grade):
        return 'NR'
    elif grade == '':
        return f'CR | {credits}'
    else:
        grades = grade.split(', ')
        grades_cleaned = [g.strip() for g in grades if g.strip()]
        all_grades = ', '.join(grades_cleaned)
        # A passing grade is determined by whether any grade is a member of the passing grades list.
        passing = any(is_passing_grade(g, passing_grades) for g in grades_cleaned)
        if passing:
            return f'{all_grades} | {credits}'
        else:
            return f'{all_grades} | 0'

def calculate_credits(row, courses_dict):
    completed, registered, remaining = 0, 0, 0
    total_credits = 0
    for course, info in courses_dict.items():
        credit = info["Credits"]
        total_credits += credit
        value = row.get(course, '')
        # Parse passing grades for this course
        passing_grades = [g.strip().upper() for g in info["PassingGrades"].split(',')]
        if isinstance(value, str):
            value_upper = value.upper()
            if value_upper.startswith('CR'):
                registered += credit
            elif value_upper.startswith('NR'):
                remaining += credit
            else:
                parts = value.split('|')
                grades_part = parts[0].strip()
                grades_list = [g.strip() for g in grades_part.split(',') if g.strip()]
                passing = any(is_passing_grade(g, passing_grades) for g in grades_list)
                if passing:
                    completed += credit
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
                    style_str = cell_color(str(value))
                    if "lightgreen" in style_str:
                        cell.fill = light_green_fill
                    elif "#FFFACD" in style_str:
                        cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                    else:
                        cell.fill = pink_fill
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
                    style_str = cell_color(str(value))
                    if "lightgreen" in style_str:
                        cell.fill = light_green_fill
                    elif "#FFFACD" in style_str:
                        cell.fill = PatternFill(start_color='FFFACD', end_color='FFFACD', fill_type='solid')
                    else:
                        cell.fill = pink_fill
    workbook.save(output)
    output.seek(0)
    return output
