import streamlit as st

# Insert "CR" at the very front so it outranks even "A+"
GRADE_ORDER = [
    "CR",
    "A+", "A", "A-",
    "B+", "B", "B-",
    "C+", "C", "C-",
    "D+", "D", "D-"
]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types (e.g. S.C.E, F.E.C).
    Can be overridden in session state.
    """
    return st.session_state.get("allowed_assignment_types", ["S.C.E", "F.E.C"])

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if 'grade' is in the comma-separated passing_grades_str.
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
    Applies the color rules:
      - CR → pale yellow
      - numeric credits >0 → light green; 0 → pink
      - PASS → light green; FAIL → pink
      - any other counted grade → light green; else pink
    """
    if not isinstance(value, str):
        return ""
    v = value.strip().upper()
    # 1) Explicit CR
    if v.startswith("CR"):
        return "background-color: #FFFACD"
    # 2) Numeric credit part
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
    # 3) Any counted grade token
    tokens = [t.strip() for t in parts[0].split(",") if t.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a cell like "F | 0, CR | 3", returns the single highest-priority entry.
    Priority is:
      1) Any "CR | X"
      2) Then the first grade in GRADE_ORDER found among tokens
      3) Else the very first entry
    Returns "GRADE | credit" (or just "GRADE" if no credit part).
    """
    if not isinstance(value, str):
        return value

    # 1) Split into entries
    entries = [e.strip() for e in value.split(",") if e.strip()]
    parsed = []
    for entry in entries:
        if "|" in entry:
            g, c = entry.split("|", 1)
            parsed.append((g.strip().upper(), c.strip()))
        else:
            parsed.append((entry.strip().upper(), ""))

    # 2) Explicit CR
    for g, c in parsed:
        if g == "CR":
            return f"{g} | {c}" if c else "CR"

    # 3) Scan GRADE_ORDER
    for grade in GRADE_ORDER:
        for g, c in parsed:
            if g == grade:
                return f"{g} | {c}" if c else grade

    # 4) Fallback
    g, c = parsed[0]
    return f"{g} | {c}" if c else g
