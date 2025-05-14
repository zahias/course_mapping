import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def read_progress_report(filepath):
    # ... your existing read_progress_report and transform_wide_format code here ...
    # Make no changes to these two functions.
    # (Omitted for brevity; copy exactly from your current file.)
    pass  # replace with your existing implementation

def transform_wide_format(df):
    # ... your existing transform_wide_format implementation ...
    pass

def read_equivalent_courses(equivalent_courses_df):
    mapping = {}
    for _, row in equivalent_courses_df.iterrows():
        primary = row["Course"].strip().upper()
        for eq in str(row["Equivalent"]).split(","):
            mapping[eq.strip().upper()] = primary
    return mapping

def sem_to_ord(sem: str, year: int):
    """
    Convert 'FALL-2017', 'SPRING-2018', 'SUMMER-2019' to an integer ordinal:
      ordinal = year * 3 + {FALL→0, SPRING→1, SUMMER→2}
    """
    try:
        idx = {"FALL": 0, "SPRING": 1, "SUMMER": 2}[sem.strip().upper()]
        return int(year) * 3 + idx
    except Exception:
        return None

def determine_cell_value(grade, credits, passing_str):
    """
    The same logic you already have:
      - blank → CR
      - NA → NR
      - otherwise check tokens vs passing_str and assign credits or 0
    """
    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"
    tokens = [g.strip().upper() for g in grade.split(",") if g.strip()]
    allowed = [x.strip().upper() for x in passing_str.split(",")]
    passed = any(t in allowed for t in tokens)
    all_toks = ", ".join(tokens)
    if credits > 0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def process_progress_report(
    df: pd.DataFrame,
    target_rules: dict,
    intensive_rules: dict,
    per_student_assignments: dict = None,
    equivalent_mapping: dict = None
):
    # --- 1) Copy & map equivalents ---
    df = df.copy()
    if equivalent_mapping is None:
        equivalent_mapping = {}
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_mapping.get(x, x))

    # --- 2) S.C.E./F.E.C. overrides ---
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_asg(r):
            sid = str(r["ID"])
            cr = r["Course"]
            mc = r["Mapped Course"]
            for atype in allowed:
                if per_student_assignments.get(sid, {}).get(atype) == cr:
                    return atype
            return mc
        df["Mapped Course"] = df.apply(map_asg, axis=1)

    # --- 3) Semester ordinal ---
    df["SemOrd"] = df.apply(lambda r: sem_to_ord(r["Semester"], r["Year"]), axis=1)

    # --- 4) Compute fully processed cell value per row ---
    # Build a lookup of Credits and PassingGrades for each course
    course_config = {}
    for c, rules in target_rules.items():
        # each rule dict has 'Credits' and 'PassingGrades'; we pick the first for credit here
        course_config[c] = (rules[0]["Credits"], rules[0]["PassingGrades"])
    for c, rules in intensive_rules.items():
        course_config[c] = (rules[0]["Credits"], rules[0]["PassingGrades"])

    def compute_val(r):
        mc = r["Mapped Course"]
        ord_ = r["SemOrd"]
        grd = r["Grade"]
        # find the rule whose range covers this semester
        applicable = []
        if mc in target_rules:
            applicable += target_rules[mc]
        if mc in intensive_rules:
            applicable += intensive_rules[mc]
        for rule in applicable:
            if rule["FromOrd"] <= ord_ <= rule["ToOrd"]:
                return determine_cell_value(grd, rule["Credits"], rule["PassingGrades"])
        # fallback to first rule if none match
        if applicable:
            rule = applicable[0]
            return determine_cell_value(grd, rule["Credits"], rule["PassingGrades"])
        return "NR"

    df["ProcessedValue"] = df.apply(compute_val, axis=1)

    # --- 5) Split into Required, Intensive, Extra ---
    req_df = df[df["Mapped Course"].isin(target_rules.keys())]
    int_df = df[df["Mapped Course"].isin(intensive_rules.keys())]
    extra_df = df[
        ~df["Mapped Course"].isin(target_rules.keys()) &
        ~df["Mapped Course"].isin(intensive_rules.keys())
    ]

    # --- 6) Pivot on ProcessedValue ---
    pivot_req = req_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda x: ", ".join(x)
    ).reset_index()

    pivot_int = int_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda x: ", ".join(x)
    ).reset_index()

    # Ensure all columns exist
    for c in target_rules:
        if c not in pivot_req.columns:
            pivot_req[c] = None
    for c in intensive_rules:
        if c not in pivot_int.columns:
            pivot_int[c] = None

    # Final shape
    result_df = pivot_req[["ID", "NAME"] + list(target_rules.keys())]
    intensive_result_df = pivot_int[["ID", "NAME"] + list(intensive_rules.keys())]

    # --- 7) Remove assigned from extras (vectorized) ---
    if per_student_assignments:
        assigned = {
            (sid, course)
            for sid, assigns in per_student_assignments.items()
            for course in assigns.values()
        }
        extra_df = extra_df.copy()
        extra_df["_pair"] = list(zip(extra_df["ID"].astype(str), extra_df["Course"]))
        extra_df = extra_df[~extra_df["_pair"].isin(assigned)].drop(columns=["_pair"])

    extra_list = sorted(extra_df["Course"].unique())
    return result_df, intensive_result_df, extra_df, extra_list

def calculate_credits(row: pd.Series, credit_map: dict):
    """
    Same as before: count '# of Credits Completed', '# Registered', etc.
    """
    completed = registered = remaining = 0
    total = sum(credit_map.values())

    for course, cred in credit_map.items():
        val = row.get(course, "")
        if isinstance(val, str):
            v = val.upper()
            if v.startswith("CR"):
                registered += cred
            elif v.startswith("NR"):
                remaining += cred
            else:
                parts = v.split("|")
                num = parts[1].strip() if len(parts) > 1 else "0"
                try:
                    n = int(num)
                    if n > 0:
                        completed += cred
                    else:
                        remaining += cred
                except:
                    if num.upper() != "PASS":
                        remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=["# of Credits Completed", "# Registered", "# Remaining", "Total Credits"]
    )
