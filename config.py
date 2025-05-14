# config.py

import streamlit as st

# Insert "CR" first so it's the very highest priority when collapsing.
GRADE_ORDER = [
    "CR",
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-"
]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise defaults to S.C.E and F.E.C.
    """
    return st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if a grade token is in the comma-separated passing grades.
    """
    try:
        passing = [g.strip().upper() for g in passing_grades_str.split(",")]
    except Exception:
        passing = []
    return grade.strip().upper() in passing

# Alias for backwards compatibility
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns CSS background-color based on the value:
      - CR → pale yellow
      - numeric credit >0 → lightgreen; 0 → pink
      - PASS → lightgreen; FAIL → pink
      - any counted grade → lightgreen; else pink
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    if v.startswith("CR"):
        return "background-color: #FFFACD"
    parts = v.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        try:
            n = int(right)
            return "background-color: lightgreen" if n > 0 else "background-color: pink"
        except ValueError:
            if right == "PASS":
                return "background-color: lightgreen"
            if right == "FAIL":
                return "background-color: pink"
    # fallback on any grade token
    tokens = [t.strip() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Collapses a full cell string (e.g. "F | 0, CR | 3") down to a single entry:
      1) If any entry starts with "CR", returns that entry verbatim.
      2) Otherwise, splits into (grade,credit) pairs and scans GRADE_ORDER
         (CR, A+, A, …, D-) to pick the first matching grade.
      3) If still no match, falls back to the very first entry.
    Returns "GRADE | credit" or just "GRADE" if no credit part.
    """
    if not isinstance(value, str):
        return value

    # Split into entries by comma
    entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in entries:
        if "|" in entry:
            g, c = entry.split("|", 1)
            parsed.append((g.strip().upper(), c.strip()))
        else:
            parsed.append((entry.strip().upper(), ""))

    # 1) Explicit CR check
    for grade_tok, cred in parsed:
        if grade_tok == "CR":
            return f"{grade_tok} | {cred}" if cred else "CR"

    # 2) Scan GRADE_ORDER
    for grade in GRADE_ORDER:
        for grade_tok, cred in parsed:
            if grade_tok == grade:
                return f"{grade_tok} | {cred}" if cred else grade_tok

    # 3) Fallback to first entry
    grade_tok, cred = parsed[0]
    return f"{grade_tok} | {cred}" if cred else grade_tok
