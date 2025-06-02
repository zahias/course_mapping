import pandas as pd
import streamlit as st
from config import GRADE_ORDER, is_passing_grade, get_allowed_assignment_types

def sem_to_ord(sem: str, year: int) -> int:
    """
    Convert a Semester string + Year into a monotonic integer:
      FALL‐YYYY → YYYY*3 + 0
      SPRING‐YYYY → YYYY*3 + 1
      SUMMER‐YYYY → YYYY*3 + 2
    """
    mapping = {"Fall": 0, "Spring": 1, "Summer": 2}
    return int(year) * 3 + mapping.get(sem.capitalize(), 0)

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
    id_vars     = [c for c in df.columns if c not in course_cols]

    df_melted = df.melt(
        id_vars=id_vars,
        var_name="Course_Column",
        value_name="CourseData"
    )
    df_melted = df_melted[
        df_melted["CourseData"].notnull()
        & (df_melted["CourseData"] != "")
    ]

    split_cols = df_melted["CourseData"].str.split("/", expand=True)
    if split_cols.shape[1] < 3:
        st.error("Parsing error: Expected format COURSECODE/SEMESTER-YEAR/GRADE.")
        return None

    df_melted["Course"]        = split_cols[0].str.strip().str.upper()
    df_melted["Semester_Year"] = split_cols[1].str.strip()
    df_melted["Grade"]         = split_cols[2].str.strip().str.upper()

    sem_year_split = df_melted["Semester_Year"].str.split("-", expand=True)
    if sem_year_split.shape[1] < 2:
        st.error("Semester-Year format not recognized. Expected e.g. FALL-2016.")
        return None

    df_melted["Semester"] = sem_year_split[0].str.strip().str.title()
    df_melted["Year"]     = sem_year_split[1].str.strip()

    df_melted = df_melted.rename(columns={"STUDENT ID": "ID", "NAME": "NAME"})
    req_cols = {"ID", "NAME", "Course", "Grade", "Year", "Semester"}
    if not req_cols.issubset(df_melted.columns):
        st.error(f"Missing columns after transformation: {req_cols - set(df_melted.columns)}")
        return None

    return df_melted[list(req_cols)].drop_duplicates()

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary     = row["Course"].strip().upper()
        equivalents = [x.strip().upper() for x in str(row["Equivalent"]).split(",")]
        for eq in equivalents:
            mapping[eq] = primary
    return mapping

def process_progress_report(
    df: pd.DataFrame,
    target_courses: dict,
    intensive_courses: dict,
    per_student_assignments: dict = None,
    equivalent_courses_mapping: dict = None
):
    """
    1) Map equivalents
    2) Apply S.C.E./F.E.C. (or other allowed assignment types)
    3) Determine each cell's ProcessedValue string
    4) Split DataFrame into required, intensive, extra
    5) Pivot on ProcessedValue, filling missing columns with 'NR'
    6) Remove assigned courses from extra
    """
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    df = df.copy()
    df["Mapped Course"] = df["Course"].apply(
        lambda x: equivalent_courses_mapping.get(x, x)
    )

    # --- 1) Apply S.C.E. / F.E.C. (or any other allowed assignment types) ---
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assignment(r):
            sid     = str(r["ID"])
            crs     = r["Course"]
            mapped  = r["Mapped Course"]
            assigns = per_student_assignments.get(sid, {})
            for atype in allowed:
                if assigns.get(atype) == crs:
                    return atype
            return mapped

        df["Mapped Course"] = df.apply(map_assignment, axis=1)

    # --- 2) Build and apply the time‐scoped rule set per course ---
    #    We fetch the Major‐scoped rule dicts from session_state.
    major = st.session_state.get("selected_major", "")
    if not major:
        st.error("No 'selected_major' found in session_state.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), []

    target_rules_key    = f"{major}_target_course_rules"
    intensive_rules_key = f"{major}_intensive_course_rules"

    if target_rules_key not in st.session_state or intensive_rules_key not in st.session_state:
        st.error("Course rules not found in session_state for this Major.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), []

    target_rules    = st.session_state[target_rules_key]
    intensive_rules = st.session_state[intensive_rules_key]

    def compute_processed_value(r):
        """
        Given a row `r`, look up the matching rule (by semester-year ordinal)
        in either target_rules[course] or intensive_rules[course], then call
        determine_course_value with that rule. If no rules found, fallback to
        zero-credit default.
        """
        mc    = r["Mapped Course"]
        grd   = r["Grade"]
        ordv  = sem_to_ord(r["Semester"], r["Year"])
        # Gather all possible rules for this mapped course (target + intensive)
        rules = []
        if mc in target_rules:
            rules.extend(target_rules[mc])
        if mc in intensive_rules:
            rules.extend(intensive_rules[mc])

        if not rules:
            # fallback to zero-credit rule if nothing configured
            return determine_course_value(grd, mc, {"Credits": 0, "PassingGrades": ""})

        # Find the one rule whose FromOrd <= ordv <= ToOrd
        for rule in rules:
            if rule["FromOrd"] <= ordv <= rule["ToOrd"]:
                return determine_course_value(grd, mc, rule)

        # If none found in range, default to the first rule
        return determine_course_value(grd, mc, rules[0])

    # Apply the compute_processed_value to every row
    df["ProcessedValue"] = df.apply(compute_processed_value, axis=1)

    # --- 3) Split into required, intensive, extra based on Mapped Course presence ---
    extra_df     = df[
        ~df["Mapped Course"].isin(target_courses.keys()) &
        ~df["Mapped Course"].isin(intensive_courses.keys())
    ]
    req_df       = df[df["Mapped Course"].isin(target_courses.keys())]
    intensive_df = df[df["Mapped Course"].isin(intensive_courses.keys())]

    # --- 4) Pivot on ProcessedValue for required and intensive ---
    pivot_req = req_df.pivot_table(
        index=["ID","NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    pivot_int = intensive_df.pivot_table(
        index=["ID","NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    # --- 5) Ensure every required/intensive column appears, fill missing with "NR" ---
    for course in target_courses:
        if course not in pivot_req.columns:
            pivot_req[course] = "NR"
        pivot_req[course] = pivot_req[course].fillna("NR")

    for course in intensive_courses:
        if course not in pivot_int.columns:
            pivot_int[course] = "NR"
        pivot_int[course] = pivot_int[course].fillna("NR")

    result_df           = pivot_req[["ID","NAME"] + list(target_courses.keys())]
    intensive_result_df = pivot_int[["ID","NAME"] + list(intensive_courses.keys())]

    # --- 6) Remove assigned courses from extra_df if per_student_assignments is provided ---
    if per_student_assignments:
        assigned_pairs = {
            (sid, crs)
            for sid, assigns in per_student_assignments.items()
            for crs in assigns.values()
        }
        # Build a temporary key to filter
        extra_df["_pair"] = list(zip(extra_df["ID"].astype(str), extra_df["Course"]))
        extra_df = extra_df[~extra_df["_pair"].isin(assigned_pairs)].drop(columns=["_pair"])

    extra_courses_list = sorted(extra_df["Course"].unique())
    return result_df, intensive_result_df, extra_df, extra_courses_list

def determine_course_value(grade, course, info):
    """
    Given a single rule 'info' dict with:
      - Credits
      - PassingGrades
    produce one of:
      - "NR"
      - "CR | X" or "CR | PASS"
      - "TOKENS | X" or "TOKENS | PASS/FAIL"
    """
    credits = info["Credits"]
    passing = info["PassingGrades"]

    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"

    tokens = [g.strip().upper() for g in grade.split(", ") if g.strip()]
    all_toks = ", ".join(tokens)
    allowed  = [x.strip().upper() for x in passing.split(",")]
    passed   = any(t in allowed for t in tokens)

    if credits > 0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def calculate_credits(row, courses_dict):
    """
    Calculates Completed, Registered, Remaining, Total Credits.
    Now treats any passing entry in a multi-attempt cell as completed,
    and any CR entry anywhere as currently registered.
    Also supports courses_dict values being either int or dict.
    """
    completed = registered = remaining = 0

    def _cred(info):
        if isinstance(info, dict):
            return int(info.get("Credits", 0))
        try:
            return int(info)
        except:
            return 0

    total = sum(_cred(info) for info in courses_dict.values())

    for course, info in courses_dict.items():
        cred = _cred(info)
        val  = row.get(course, "")

        if isinstance(val, str):
            entries = [e.strip() for e in val.split(",") if e.strip()]

            # CR anywhere → registered
            if any(e.upper().startswith("CR") for e in entries):
                registered += cred
                continue

            # any positive credit or PASS → completed
            passed = False
            for e in entries:
                parts = [p.strip() for p in e.split("|")]
                if len(parts) == 2:
                    try:
                        if int(parts[1]) > 0:
                            passed = True
                            break
                    except:
                        if parts[1].upper() == "PASS":
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

def save_report_with_formatting(displayed_df, intensive_displayed_df, timestamp):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill, Font, Alignment
    from config import cell_color

    output   = io.BytesIO()
    workbook = Workbook()
    ws_req   = workbook.active
    ws_req.title = "Required Courses"

    light_green = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
    pink        = PatternFill(start_color="FFC0CB", end_color="FFC0CB", fill_type="solid")

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

    ws_int = workbook.create_sheet(title="Intensive Courses")
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

    workbook.save(output)
    output.seek(0)
    return output
