import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses session state if available; otherwise returns the default list.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is in the comma-separated list of passing grades.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# Alias for backward compatibility.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for cell background.
    """
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if value.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split("|")
    if len(parts) == 2:
        right = parts[1].strip()
        try:
            num = int(right)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if right.upper() == "PASS":
                return "background-color: lightgreen"
            elif right.upper() == "FAIL":
                return "background-color: pink"
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(g in GRADE_ORDER for g in tokens):
        return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    From a detailed cell like "F | 0, CR | 3, C- | 0", picks:
      1) any CR segment first,
      2) then the highest-counted grade in GRADE_ORDER,
      3) then any PASS-type,
      4) else the first segment.

    Returns "Grade | Credit" for that segment.
    """
    if not isinstance(value, str):
        return value

    # Split into segments by comma *between* full segments
    segments = [seg.strip() for seg in value.split(",")]

    parsed = []
    for seg in segments:
        if "|" in seg:
            left, right = seg.split("|", 1)
            grades = [g.strip().upper() for g in left.split(",") if g.strip()]
            credit = right.strip()
            parsed.append((grades, credit))

    if not parsed:
        return value

    # 1) CR over everything
    for grades, credit in parsed:
        if any(g == "CR" for g in grades):
            return f"CR | {credit}"

    # 2) Highest‐priority counted grade
    for grade in GRADE_ORDER:
        for grades, credit in parsed:
            if grade in grades:
                return f"{grade} | {credit}"

    # 3) PASS‐type grades
    for grades, credit in parsed:
        for g in grades:
            if g in {"P", "P*", "WP", "T", "PASS"}:
                return f"{g} | {credit}"

    # 4) Fallback to first segment
    grades, credit = parsed[0]
    return f"{grades[0]} | {credit}" if grades else f"{parsed[0][1]}"
