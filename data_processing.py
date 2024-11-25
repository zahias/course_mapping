# data_processing.py

import pandas as pd
import streamlit as st

def read_progress_report(filepath):
    try:
        xls = pd.ExcelFile(filepath)
        if 'Progress Report' not in xls.sheet_names:
            st.error("The uploaded file does not contain a 'Progress Report' sheet.")
            return None
        df = pd.read_excel(xls, sheet_name='Progress Report')
        required_columns = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
        if not required_columns.issubset(df.columns):
            st.error(f"The following required columns are missing from the data: {required_columns - set(df.columns)}")
            return None
        return df
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        return None

def process_progress_report(df, target_courses, intensive_courses, grading_system, per_student_assignments=None):
    # Map courses to target courses
    course_code_mapping = {course: course for course in target_courses}

    # Map courses to intensive courses
    course_code_mapping.update({course: course for course in intensive_courses})

    df['Mapped Course'] = df['Course']  # Start with original courses

    # Apply per-student S.C.E. and F.E.C. assignments
    if per_student_assignments:
        def map_sce_fec(row):
            student_id = str(row['ID'])
            course = row['Course']
            mapped_course = row['Mapped Course']

            # Check if this course is selected as S.C.E. or F.E.C. for this student
            if student_id in per_student_assignments:
                assignments = per_student_assignments[student_id]
                if assignments.get('S.C.E.') == course:
                    return 'S.C.E'
                elif assignments.get('F.E.C.') == course:
                    return 'F.E.C'
            return mapped_course

        df['Mapped Course'] = df.apply(map_sce_fec, axis=1)

    # Identify extra courses (exclude target and intensive courses)
    extra_courses_df = df[
        (~df['Mapped Course'].isin(target_courses)) &
        (~df['Mapped Course'].isin(intensive_courses))
    ]

    # Filter df to only target courses
    target_df = df[df['Mapped Course'].isin(target_courses)]

    # Filter df to only intensive courses
    intensive_df = df[df['Mapped Course'].isin(intensive_courses)]

    # Create pivot tables for target courses and intensive courses
    # Required courses pivot table
    pivot_df = target_df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(map(str, filter(pd.notna, x)))
    ).reset_index()

    # Intensive courses pivot table
    intensive_pivot_df = intensive_df.pivot_table(
        index=['ID', 'NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(map(str, filter(pd.notna, x)))
    ).reset_index()

    # Now process each required course
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = None

        pivot_df[course] = pivot_df[course].apply(
            lambda grade: determine_course_value(grade, course, target_courses, grading_system)
        )

    # Process each intensive course
    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = None

        intensive_pivot_df[course] = intensive_pivot_df[course].apply(
            lambda grade: determine_course_value(grade, course, intensive_courses, grading_system)
        )

    # Keep only ID, NAME, and the courses
    result_df = pivot_df[['ID', 'NAME'] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[['ID', 'NAME'] + list(intensive_courses.keys())]

    # Remove assigned courses from extra_courses_df
    if per_student_assignments:
        assigned_courses = []
        for student_id, assignments in per_student_assignments.items():
            for course in assignments.values():
                assigned_courses.append((student_id, course))
        extra_courses_df = extra_courses_df[
            ~extra_courses_df.apply(lambda row: (str(row['ID']), row['Course']) in assigned_courses, axis=1)
        ]

    # Get list of extra courses (excluding intensive courses)
    extra_courses_list = sorted(extra_courses_df['Course'].unique())

    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade, course, courses_dict, grading_system):
    if pd.isna(grade):
        return 'NR'  # Not Registered
    elif grade == '':
        return f'CR | {courses_dict[course]}'  # Currently Registered
    else:
        grades = grade.split(', ')
        grades_cleaned = [g.strip() for g in grades if g.strip()]
        all_grades = ', '.join(grades_cleaned)
        counted_grades = [g for g in grades_cleaned if g in grading_system['Counted']]
        if not counted_grades:
            return f'{all_grades} | 0'
        else:
            counted_credits = courses_dict[course]
            return f'{all_grades} | {counted_credits}'

def calculate_credits(row, courses_dict, grading_system):
    completed, registered, remaining = 0, 0, 0
    total_credits = sum(courses_dict.values())

    for course in courses_dict:
        value = row.get(course, '')
        if isinstance(value, str):
            if 'NR' in value:
                remaining += courses_dict[course]
            elif 'CR' in value or value.lower() == 'c':
                registered += courses_dict[course]
            else:
                # Extract grades
                grades_list = [g.strip() for g in value.split(',') if g.strip()]
                if any(grade in grading_system['Counted'] for grade in grades_list):
                    completed += courses_dict[course]
                else:
                    remaining += courses_dict[course]

    return pd.Series([completed, registered, remaining, total_credits],
                     index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits'])

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp, grading_system):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment

    output = io.BytesIO()
    workbook = Workbook()
    ws_required = workbook.active
    ws_required.title = "Required Courses"

    # Define fill colors
    light_green_fill = PatternFill(start_color='90EE90', end_color='90EE90', fill_type='solid')
    pink_fill = PatternFill(start_color='FFC0CB', end_color='FFC0CB', fill_type='solid')

    # Write the displayed_df to Excel with formatting
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_required.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                # Header row formatting
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                # Apply color formatting based on cell value
                if value == 'c':
                    cell.fill = light_green_fill
                elif value == '':
                    cell.fill = pink_fill
                else:
                    if isinstance(value, str):
                        grades_list = [g.strip() for g in value.split(',') if g.strip()]
                        if any(grade in grading_system['Counted'] or 'CR' == grade.upper() for grade in grades_list):
                            cell.fill = light_green_fill
                        else:
                            cell.fill = pink_fill

    # Add the Intensive Courses sheet
    ws_intensive = workbook.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_intensive.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                # Header row formatting
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                # Apply color formatting based on cell value
                if value == 'c':
                    cell.fill = light_green_fill
                elif value == '':
                    cell.fill = pink_fill
                else:
                    if isinstance(value, str):
                        grades_list = [g.strip() for g in value.split(',') if g.strip()]
                        if any(grade in grading_system['Counted'] or 'CR' == grade.upper() for grade in grades_list):
                            cell.fill = light_green_fill
                        else:
                            cell.fill = pink_fill

    # Save the workbook to the output stream
    workbook.save(output)
    output.seek(0)
    return output
