import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def sem_to_ord(sem: str, year: int):
    """
    Converts Semester + Year into an ordinal:
      ordinal = year * 3 + {FALL→0, SPRING→1, SUMMER→2}.
    """
    try:
        idx = {"FALL": 0, "SPRING": 1, "SUMMER": 2}[sem.strip().upper()]
        return int(year) * 3 + idx
    except Exception:
        return None

def determine_cell_value(grade, credits, passing_str):
    """
    Given a raw grade and a rule’s credits + passing grades list,
    returns "NR", "CR | X", "Tokens | X", or "Tokens | PASS/FAIL" as before.
    """
    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}" if credits > 0 else "CR | PASS"
    tokens = [g.strip().upper() for g in grade.split(",") if g.strip()]
    all_toks = ", ".join(tokens)
    allowed = [x.strip().upper() for x in passing_str.split(",")]
    passed = any(g in allowed for g in tokens)
    if credits > 0:
        return f"{all_toks} | {credits}" if passed else f"{all_toks} | 0"
    else:
        return f"{all_toks} | PASS" if passed else f"{all_toks} | FAIL"

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _, r in equiv_df.iterrows():
        primary = r["Course"].strip().upper()
        for eq in str(r["Equivalent"]).split(","):
            mapping[eq.strip().upper()] = primary
    return mapping

def process_progress_report(
    df: pd.DataFrame,
    target_rules: dict,
    intensive_rules: dict,
    per_student_assignments: dict = None,
    equivalent_mapping: dict = None
):
    if equivalent_mapping is None:
        equivalent_mapping = {}

    # 1) Map equivalents
    df = df.copy()
    df["Mapped Course"] = df["Course"].apply(lambda x: equivalent_mapping.get(x, x))

    # 2) Apply S.C.E. / F.E.C. overrides
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assignment(row):
            sid = str(row["ID"])
            course = row["Course"]
            mapped = row["Mapped Course"]
            for atype in allowed:
                if per_student_assignments.get(sid, {}).get(atype) == course:
                    return atype
            return mapped
        df["Mapped Course"] = df.apply(map_assignment, axis=1)

    # 3) Compute semester ordinal
    df["SemOrd"] = df.apply(lambda r: sem_to_ord(r["Semester"], r["Year"]), axis=1)

    # 4) Compute ProcessedValue based on matching rule
    def compute_val(row):
        mc = row["Mapped Course"]
        ord_ = row["SemOrd"]
        grade = row["Grade"]
        # combine required + intensive rules for lookup
        rules = target_rules.get(mc, []) + intensive_rules.get(mc, [])
        # find first matching
        for rule in rules:
            if rule["FromOrd"] <= ord_ <= rule["ToOrd"]:
                return determine_cell_value(grade, rule["Credits"], rule["PassingGrades"])
        # fallback to first rule
        if rules:
            rule = rules[0]
            return determine_cell_value(grade, rule["Credits"], rule["PassingGrades"])
        return "NR"

    df["ProcessedValue"] = df.apply(compute_val, axis=1)

    # 5) Split into Required, Intensive, Extra
    req_df = df[df["Mapped Course"].isin(target_rules.keys())]
    int_df = df[df["Mapped Course"].isin(intensive_rules.keys())]
    extra_df = df[
        ~df["Mapped Course"].isin(target_rules.keys()) &
        ~df["Mapped Course"].isin(intensive_rules.keys())
    ]

    # 6) Pivot tables
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

    # 7) Remove already‐assigned extra courses **vectorized**
    if per_student_assignments:
        assigned = set()
        for sid, assigns in per_student_assignments.items():
            for course in assigns.values():
                assigned.add((str(sid), course))
        # create a helper column of tuples
        extra_df = extra_df.copy()
        extra_df["_id_course"] = list(zip(extra_df["ID"].astype(str), extra_df["Course"]))
        # filter out assigned
        extra_df = extra_df[~extra_df["_id_course"].isin(assigned)].drop(columns=["_id_course"])

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
