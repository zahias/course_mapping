# data_processing.py

import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

def read_progress_report(filepath):
    """
    Reads an uploaded progress report (Excel or CSV), in either:
      - “long” format with columns [ID or STUDENT ID, NAME, Course, Grade, Year, Semester]
      - “wide” format with columns ID/NAME plus COURSE… columns
    Returns a long‐format DataFrame with exactly ['ID','NAME','Course','Grade','Year','Semester'] or None on error.
    """
    try:
        # Excel files
        if filepath.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(filepath)
            # If there is a sheet named "Progress Report", read that long‐form
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='Progress Report')
                required = {'ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester'}
                missing = required - set(df.columns)
                if missing:
                    st.error(f"Missing columns: {missing}")
                    return None
                return df[list(required)]
            # Otherwise, pull the first sheet and attempt wide‐to‐long
            df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
            transformed = transform_wide_format(df)
            if transformed is None:
                st.error("Failed to read the uploaded progress report file.")
            return transformed

        # CSV files
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course','Grade','Year','Semester'}.issubset(df.columns):
                # assume long form
                if 'ID' not in df.columns and 'STUDENT ID' not in df.columns:
                    st.error("Missing 'ID' or 'STUDENT ID' in CSV.")
                    return None
                if 'NAME' not in df.columns:
                    st.error("Missing 'NAME' in CSV.")
                    return None
                df = df.rename(columns={'STUDENT ID': 'ID'}) if 'STUDENT ID' in df.columns else df
                return df[['ID','NAME','Course','Grade','Year','Semester']]
            # otherwise try wide form
            transformed = transform_wide_format(df)
            if transformed is None:
                st.error("Failed to read the uploaded progress report file.")
            return transformed

        else:
            st.error("Unsupported file format. Please upload an Excel or CSV file.")
            return None

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def transform_wide_format(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Converts a wide‐format progress sheet into long form.
    Detects an ID column ('ID' or 'STUDENT ID') plus any columns starting with 'COURSE'
    Expects each cell as 'COURSECODE/SEMESTER-YEAR/GRADE'.
    Returns a DataFrame with columns ['ID','NAME','Course','Grade','Year','Semester'].
    """
    # 1) Find the student‐ID column
    if 'ID' in df.columns:
        id_col = 'ID'
    elif 'STUDENT ID' in df.columns:
        id_col = 'STUDENT ID'
    else:
        st.error("Wide format file missing an 'ID' or 'STUDENT ID' column.")
        return None

    # 2) Ensure we have a NAME column
    if 'NAME' not in df.columns and 'Name' in df.columns:
        df = df.rename(columns={'Name': 'NAME'})
    if 'NAME' not in df.columns:
        st.error("Wide format file missing a 'NAME' column.")
        return None

    # 3) Detect all COURSE columns
    course_cols = [c for c in df.columns if c.upper().startswith('COURSE')]
    if not course_cols:
        st.error("Wide format file missing any 'COURSE…' columns.")
        return None

    # 4) Melt into long form
    id_vars = [c for c in df.columns if c not in course_cols]
    df_melt = df.melt(
        id_vars=id_vars,
        value_vars=course_cols,
        var_name='Course_Column',
        value_name='CourseData'
    )

    # 5) Drop empty entries
    df_melt = df_melt[df_melt['CourseData'].notna() & (df_melt['CourseData'].str.strip() != '')]

    # 6) Split COURSECODE/SEMESTER-YEAR/GRADE
    parts = df_melt['CourseData'].str.split('/', expand=True)
    if parts.shape[1] < 3:
        st.error("Parsing error: expected 'CODE/SEMESTER-YEAR/GRADE'.")
        return None

    df_melt['Course'] = parts[0].str.strip().str.upper()
    df_melt['RawSemYear'] = parts[1].str.strip()
    df_melt['Grade'] = parts[2].str.strip().str.upper()

    # 7) Split Semester and Year
    sem_parts = df_melt['RawSemYear'].str.split('-', expand=True)
    if sem_parts.shape[1] < 2:
        st.error("Expected Semester-Year in format 'FALL-2016'.")
        return None

    df_melt['Semester'] = sem_parts[0].str.strip().str.title()
    df_melt['Year'] = sem_parts[1].str.strip()

    # 8) Rename ID column to 'ID'
    if id_col != 'ID':
        df_melt = df_melt.rename(columns={id_col: 'ID'})

    # 9) Collect only needed columns
    final_cols = ['ID', 'NAME', 'Course', 'Grade', 'Year', 'Semester']
    missing = [c for c in final_cols if c not in df_melt.columns]
    if missing:
        st.error(f"Missing columns after transformation: {missing}")
        return None

    return df_melt[final_cols].drop_duplicates()


def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row["Course"].strip().upper()
        equivalents = [x.strip().upper() for x in str(row["Equivalent"]).split(",")]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping


def process_progress_report(
    df: pd.DataFrame,
    target_courses: dict,
    intensive_courses: dict,
    target_rules: dict,
    intensive_rules: dict,
    per_student_assignments: dict = None,
    equivalent_courses_mapping: dict = None
):
    """
    df: the raw long‐format progress data
    target_courses: { course_code: credits, ... }
    intensive_courses: { course_code: credits, ... }
    target_rules:    { course_code: [rule_dicts], ... }
    intensive_rules: { course_code: [rule_dicts], ... }
    per_student_assignments: { student_id: { assign_type: course, ... }, ... }
    equivalent_courses_mapping: { alt_code: primary_code, ... }
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    # 1) Map equivalents
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 2) Apply assignments (S.C.E./F.E.C.)
    if per_student_assignments:
        allowed_types = get_allowed_assignment_types()
        def map_assignment(row):
            sid = str(row["ID"])
            course = row["Course"]
            mapped = row["Mapped Course"]
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for atype in allowed_types:
                    if assigns.get(atype) == course:
                        return atype
            return mapped
        df["Mapped Course"] = df.apply(map_assignment, axis=1)

    # 3) Compute ProcessedValue
    df["ProcessedValue"] = df.apply(
        lambda r: determine_course_value(
            r["Grade"],
            r["Mapped Course"],
            target_courses if r["Mapped Course"] in target_courses else
            intensive_courses if r["Mapped Course"] in intensive_courses else {},
            (target_rules.get(r["Mapped Course"], []) if r["Mapped Course"] in target_rules else
             intensive_rules.get(r["Mapped Course"], []))
        ),
        axis=1
    )

    # 4) Split into required, intensive, extra
    extra_df     = df[~df["Mapped Course"].isin(target_courses.keys())
                      & ~df["Mapped Course"].isin(intensive_courses.keys())]
    target_df    = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]

    # 5) Pivot
    pivot = target_df.pivot_table(
        index=["ID","NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()
    int_pivot = intensive_df.pivot_table(
        index=["ID","NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    # 6) Fill missing with "NR"
    for course in target_courses:
        pivot[course] = pivot.get(course, pd.Series()).fillna("NR")
    for course in intensive_courses:
        int_pivot[course] = int_pivot.get(course, pd.Series()).fillna("NR")

    result_df          = pivot[["ID","NAME"] + list(target_courses.keys())]
    intensive_result_df = int_pivot[["ID","NAME"] + list(intensive_courses.keys())]

    # 7) Exclude assigned extras
    if per_student_assignments:
        assigned = [
            (sid, crs)
            for sid, assigns in per_student_assignments.items()
            for crs in assigns.values()
        ]
        extra_df = extra_df[~extra_df.apply(
            lambda row: (str(row["ID"]), row["Course"]) in assigned, axis=1
        )]

    extra_courses_list = sorted(extra_df["Course"].unique())
    return result_df, intensive_result_df, extra_df, extra_courses_list


def determine_course_value(grade: str, course: str, courses_dict: dict, rules_list: list):
    """
    Processes a course grade into:
      - "NR" if not registered
      - ""   if failed
      - "<tokens> | <credits>" if passed
    """
    if rules_list:
        rule = rules_list[0]
        credits = rule["Credits"]
        passing = rule["PassingGrades"]
    else:
        credits = 0
        passing = ""

    if pd.isna(grade) or str(grade).strip().upper() == "NR":
        return "NR"
    if grade == "":
        return ""  # failed
    tokens = [g.strip().upper() for g in grade.split(",") if g.strip()]
    all_toks = ", ".join(tokens)
    allowed  = [x.strip().upper() for x in passing.split(",")] if passing else []
    passed   = any(g in allowed for g in tokens)

    if credits > 0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"


def calculate_credits(row: pd.Series, courses_dict: dict):
    """
    Calculates Completed, Registered, Remaining, Total Credits
    based on values like "NR", "" (fail), or "XXX | N".
    """
    completed = registered = remaining = 0
    total     = sum(courses_dict.values())

    for course, cred in courses_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            entries = [e.strip() for e in val.split(",") if e.strip()]
            # Registered takes precedence
            if any(e.upper() == "NR" for e in entries):
                registered += cred
                continue
            # Check for PASS or numeric > 0
            passed = False
            for e in entries:
                parts = [p.strip() for p in e.split("|")]
                if len(parts) == 2:
                    right = parts[1].strip().upper()
                    try:
                        if int(right) > 0:
                            passed = True
                            break
                    except ValueError:
                        if right == "PASS":
                            passed = True
                            break
            if passed:
                completed += cred
            else:
                remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
    )


def save_report_with_formatting(displayed_df: pd.DataFrame,
                                intensive_displayed_df: pd.DataFrame,
                                timestamp: str):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    wb     = Workbook()
    ws_req = wb.active
    ws_req.title = "Required Courses"

    light_green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink        = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")

    # Write required courses sheet
    for r_idx, row in enumerate(dataframe_to_rows(displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_req.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font      = Font(bold=True)
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

    # Intensive sheet
    ws_int = wb.create_sheet(title="Intensive Courses")
    for r_idx, row in enumerate(dataframe_to_rows(intensive_displayed_df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws_int.cell(row=r_idx, column=c_idx, value=value)
            if r_idx == 1:
                cell.font      = Font(bold=True)
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

    wb.save(output)
    output.seek(0)
    return output
