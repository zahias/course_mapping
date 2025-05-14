# data_processing.py

import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def sem_to_ord(sem: str, year: int):
    """Convert Semester+Year into ordinal: year*3 + {FALL→0, SPRING→1, SUMMER→2}."""
    try:
        idx = {"FALL": 0, "SPRING": 1, "SUMMER": 2}[sem.strip().upper()]
        return int(year) * 3 + idx
    except Exception:
        return None

def determine_cell_value(grade, credits, passing_str):
    """
    Given raw grade and rule, returns one of:
      - "NR"
      - "CR | <credits>" or "CR | PASS"
      - "<ALL_GRADES> | <credits>" or "... | PASS/FAIL"
    """
    if pd.isna(grade):
        return "NR"
    if grade == "":
        # currently registered
        return f"CR | {credits}" if credits > 0 else "CR | PASS"

    tokens = [g.strip().upper() for g in grade.split(",") if g.strip()]
    all_toks = ", ".join(tokens)
    allowed = [x.strip().upper() for x in passing_str.split(",")]
    passed = any(t in allowed for t in tokens)

    if credits > 0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def read_equivalent_courses(equiv_df):
    """Build mapping of equivalent→primary from a DataFrame."""
    mapping = {}
    for _, row in equiv_df.iterrows():
        primary = row["Course"].strip().upper()
        for eq in str(row["Equivalent"]).split(","):
            mapping[eq.strip().upper()] = primary
    return mapping

def process_progress_report(
    df: pd.DataFrame,
    target_rules: dict,
    intensive_rules: dict,
    per_student_assignments: dict = None,
    equivalent_mapping: dict = None
):
    """
    1) Maps equivalents and S.C.E./F.E.C.
    2) Computes a numeric semester ordinal.
    3) Computes a ProcessedValue per row via determine_cell_value.
    4) Pivots on ProcessedValue so CR entries are preserved.
    """
    if equivalent_mapping is None:
        equivalent_mapping = {}

    df = df.copy()
    # Map equivalents
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_mapping.get(x, x))

    # Apply S.C.E./F.E.C.
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def apply_assignment(r):
            sid = str(r["ID"])
            orig = r["Mapped Course"]
            for at in allowed:
                if per_student_assignments.get(sid, {}).get(at) == r["Course"]:
                    return at
            return orig
        df["Mapped Course"] = df.apply(apply_assignment, axis=1)

    # Semester ordinal
    df["SemOrd"] = df.apply(lambda r: sem_to_ord(r["Semester"], r["Year"]), axis=1)

    # Compute ProcessedValue
    def compute_val(r):
        mc = r["Mapped Course"]
        ord_ = r["SemOrd"]
        grade = r["Grade"]
        # Get all rules for this course
        rules = target_rules.get(mc, []) + intensive_rules.get(mc, [])
        for rule in rules:
            if rule["FromOrd"] <= ord_ <= rule["ToOrd"]:
                return determine_cell_value(grade, rule["Credits"], rule["PassingGrades"])
        # Fallback
        if rules:
            rule = rules[0]
            return determine_cell_value(grade, rule["Credits"], rule["PassingGrades"])
        return "NR"

    df["ProcessedValue"] = df.apply(compute_val, axis=1)

    # Split into required/intensive/extra
    req_df = df[df["Mapped Course"].isin(target_rules.keys())]
    int_df = df[df["Mapped Course"].isin(intensive_rules.keys())]
    extra_df = df[
        ~df["Mapped Course"].isin(target_rules.keys()) &
        ~df["Mapped Course"].isin(intensive_rules.keys())
    ]

    # Pivot ON ProcessedValue
    pivot_req = req_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()
    pivot_int = int_df.pivot_table(
        index=["ID", "NAME"],
        columns="Mapped Course",
        values="ProcessedValue",
        aggfunc=lambda vals: ", ".join(vals)
    ).reset_index()

    # Remove assigned from extra (vectorized)
    if per_student_assignments:
        assigned = set(
            (sid, course)
            for sid, asgs in per_student_assignments.items()
            for course in asgs.values()
        )
        extra_df = extra_df.copy()
        extra_df["_key"] = list(zip(extra_df["ID"].astype(str), extra_df["Course"]))
        extra_df = extra_df[~extra_df["_key"].isin(assigned)].drop(columns=["_key"])

    extra_list = sorted(extra_df["Course"].unique())
    return pivot_req, pivot_int, extra_df, extra_list

def calculate_credits(row: pd.Series, credit_map: dict):
    completed = registered = remaining = 0
    total = sum(credit_map.values())
    for course, cred in credit_map.items():
        val = row.get(course, "")
        if isinstance(val, str):
            u = val.upper()
            if u.startswith("CR"):
                registered += cred
            elif u.startswith("NR"):
                remaining += cred
            else:
                parts = val.split("|")
                num = parts[1].strip() if len(parts)>1 else "0"
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
