import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types. Uses session state if available.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is one of the passing grades from a comma‐separated string.
    For example, if passing_grades_str is "A+,A,A-", then the function returns True
    if grade (after cleaning and uppercasing) is one of those.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility, export an alias.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for a cell’s background color based on its processed value.
    
    Logic:
      - If the value starts with "CR", returns light yellow (#FFFACD).
      - Otherwise, splits the value by the pipe ("|") and inspects the second portion.
        * For courses with nonzero credit, if the numeric part > 0, returns light green; if 0, returns pink.
        * For 0‑credit courses (using "PASS"/"FAIL"), returns light green if "PASS" or pink if "FAIL".
      - As a fallback, if any grade token from the left portion is in GRADE_ORDER, returns light green.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split("|")
    if len(parts) == 2:
        second = parts[1].strip()
        try:
            num = int(second)
            return "background-color: lightgreen" if num > 0 else "background-color: pink"
        except ValueError:
            if second.upper() == "PASS":
                return "background-color: lightgreen"
            elif second.upper() == "FAIL":
                return "background-color: pink"
    # Fallback: if any grade token is recognized (even if failing)
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(g in GRADE_ORDER for g in tokens):
        return "background-color: lightgreen"
    return "background-color: pink"

def extract_primary_grade_from_full_value(value: str) -> str:
    """
    Given a processed full grade string (e.g., "B+, A, C | 3"), this function scans
    the grade tokens (from left of the pipe) and returns the highest-priority grade
    (using GRADE_ORDER) found in that list. If no token is found, it returns an empty string.
    """
    if not isinstance(value, str):
        return value
    parts = value.split("|")
    if len(parts) < 2:
        return value
    grades_part = parts[0].strip()
    if not grades_part:
        return ""
    tokens = [g.strip().upper() for g in grades_part.split(",") if g.strip()]
    for grade in GRADE_ORDER:
        if grade in tokens:
            return grade
    return tokens[0] if tokens else ""
