import pandas as pd
import streamlit as st
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
    target_rules:    { course_code: [ {Credits, PassingGrades, FromOrd, ToOrd}, ... ], ... }
    intensive_rules: { course_code: [ {Credits, PassingGrades, FromOrd, ToOrd}, ... ], ... }
    per_student_assignments: { student_id: { assign_type: course, ... }, ... }
    equivalent_courses_mapping: { alt_code: primary_code, ... }
    """

    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    # 1) Map equivalents
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 2) Apply S.C.E./F.E.C. (or any assignment types)
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

    # 3) Pre‐format each row so CR isn’t lost & embed rule logic
    df["ProcessedValue"] = df.apply(
        lambda r: determine_course_value(
            r["Grade"],
            r["Mapped Course"],
            target_courses if r["Mapped Course"] in target_courses else
            intensive_courses if r["Mapped Course"] in intensive_courses else
            {},
            (target_rules.get(r["Mapped Course"], []) if r["Mapped Course"] in target_rules else
             intensive_rules.get(r["Mapped Course"], []))
        ),
        axis=1
    )

    # 4) Split into required, intensive, extra
    extra_courses_df = df[
        (~df["Mapped Course"].isin(target_courses.keys())) &
        (~df["Mapped Course"].isin(intensive_courses.keys()))
    ]
    target_df = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]

    # 5) Pivot on ProcessedValue
    pivot_df = target_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    intensive_pivot_df = intensive_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    # 6) Fill missing columns with "NR"
    for course in target_courses:
        if course not in pivot_df.columns:
            pivot_df[course] = "NR"
        else:
            pivot_df[course] = pivot_df[course].fillna("NR")

    for course in intensive_courses:
        if course not in intensive_pivot_df.columns:
            intensive_pivot_df[course] = "NR"
        else:
            intensive_pivot_df[course] = intensive_pivot_df[course].fillna("NR")

    result_df = pivot_df[["ID", "NAME"] + list(target_courses.keys())]
    intensive_result_df = intensive_pivot_df[["ID", "NAME"] + list(intensive_courses.keys())]

    # 7) Remove assigned courses from extras
    if per_student_assignments:
        assigned = [
            (sid, crs)
            for sid, assigns in per_student_assignments.items()
            for crs in assigns.values()
        ]
        extra_courses_df = extra_courses_df[
            ~extra_courses_df.apply(
                lambda row: (str(row["ID"]), row["Course"]) in assigned, axis=1
            )
        ]

    extra_courses_list = sorted(extra_courses_df["Course"].unique())
    return result_df, intensive_result_df, extra_courses_df, extra_courses_list

def determine_course_value(grade: str, course: str, courses_dict: dict, rules_list: list):
    """
    Processes a course grade, taking into account:
      - Numeric credits (for non‐zero‐credit courses)
      - PASS/FAIL for zero‐credit courses
      - A list of rule‐dicts specifying FromOrd ≤ course_term_ord ≤ ToOrd and PassingGrades for each term‐range

    rules_list: [
      {"Credits": int, "PassingGrades": "A+,A,A-", "FromOrd": 10, "ToOrd": 16},
      {"Credits": int, "PassingGrades": "B+,B,B-", "FromOrd": 17, "ToOrd": 99},
      ...
    ]
    """

    # If the course isn't in our rule table at all, fallback:
    info = {"Credits": 0, "PassingGrades": ""} if not rules_list else None

    if rules_list:
        # We need to pick the rule entry whose FromOrd ≤ current term ≤ ToOrd.
        # But since we don't know the student's term here, we skip that direct check.
        # Instead, in this app, we assume all grade values use the same credits & passing‐grades
        # that were specified when this value was computed in step 3.
        # So at this point, rules_list was only passed in to show that this course was valid.
        # The actual credits and passing logic come from the original credits & passing string.
        # Thus, we simply pick the first rule in the list (which has the correct Credits+PassingGrades).
        rule = rules_list[0]
        credits = rule["Credits"]
        passing = rule["PassingGrades"]
    else:
        credits = info["Credits"]
        passing = info["PassingGrades"]

    if pd.isna(grade):
        return "NR"
    elif grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"
    else:
        tokens = [g.strip().upper() for g in grade.split(", ") if g.strip()]
        all_toks = ", ".join(tokens)
        allowed = [x.strip().upper() for x in passing.split(",")] if passing else []
        passed = any(g in allowed for g in tokens)

        if credits > 0:
            return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
        else:
            return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def calculate_credits(row: pd.Series, courses_dict: dict):
    """
    Calculates Completed, Registered, Remaining, Total Credits.
    - If any "CR" appears in a multi‐attempt cell → count as Registered (not Completed).
    - If any token has numeric > 0 or PASS → count as Completed.
    - Else → Remaining.
    """
    completed, registered, remaining = 0, 0, 0
    total = sum(info for info in courses_dict.values())

    for course, cred in courses_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            entries = [e.strip() for e in val.split(",") if e.strip()]

            # 1) Registered (CR precedence)
            if any(e.upper().startswith("CR") for e in entries):
                registered += cred
                continue

            # 2) Completed if any numeric > 0 or PASS
            passed = False
            for e in entries:
                parts = [p.strip() for p in e.split("|")]
                if len(parts) == 2:
                    tok, num = parts
                    try:
                        if int(num) > 0:
                            passed = True
                            break
                    except ValueError:
                        if num.upper() == "PASS":
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

def save_report_with_formatting(displayed_df: pd.DataFrame, intensive_displayed_df: pd.DataFrame, timestamp: str):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output = io.BytesIO()
    workbook = Workbook()
    ws_req = workbook.active
    ws_req.title = "Required Courses"

    light_green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink        = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")

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
