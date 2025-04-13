import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    Uses the user-defined list from session state if available,
    otherwise returns the default list.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks whether a given grade is one of the acceptable passing grades
    as defined by the comma-separated passing_grades_str from the configuration file.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(",")]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility, export is_passing_grade as an alias.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for setting a cell’s background color based on its value.
    
    Logic:
      - If the value starts with "CR" (currently registered), returns a light yellow color.
      - Otherwise, splits the value by the pipe symbol ("|") and examines the right-hand side:
          • If that portion is a numeric string: nonzero means passing (light green), 0 means failing (pink).
          • If nonnumeric (e.g. "PASS" or "FAIL" for 0‑credit courses), "PASS" returns light green and "FAIL" returns pink.
      - As a fallback, if any token in the left-hand side (grade tokens) is recognized in GRADE_ORDER,
        light green is returned; otherwise pink.
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
    Given a processed full grade string (e.g., "B+, A, C | 3" or "A, B | PASS"), this function extracts
    the primary grade based on the global GRADE_ORDER.
    
    It splits the string on the pipe ("|") and examines the left-hand side (the grade tokens).
    It then returns the first grade (according to GRADE_ORDER) that appears among the tokens.
    If none match, it returns the first available token or an empty string.
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
