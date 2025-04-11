import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types that can be used.
    If the user has set a custom list via session state, that list is returned.
    Otherwise, it defaults to ["S.C.E", "F.E.C"].
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade (after trimming and uppercasing) is one of the allowed passing grades.
    passing_grades_str is a comma-separated string (e.g. "A+,A,A-").
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility:
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the background color of a cell based on the value.
    
    Rules:
      - If the value starts with "CR", return light yellow (#FFFACD) for currently registered.
      - Otherwise, split the cell value by the pipe symbol.
          * If the right-hand side is numeric, then if it is > 0 the cell is light green, otherwise pink.
          * If the marker is nonnumeric, then "PASS" yields light green and "FAIL" yields pink.
      - Fallback: if no proper marker is found, return pink.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith("CR"):
        return "background-color: #FFFACD"
    parts = value.split('|')
    if len(parts) == 2:
        marker = parts[1].strip()
        try:
            num = int(marker)
            if num > 0:
                return "background-color: lightgreen"
            else:
                return "background-color: pink"
        except ValueError:
            # Non-numeric marker; check for PASS or FAIL
            if marker.upper() == "PASS":
                return "background-color: lightgreen"
            elif marker.upper() == "FAIL":
                return "background-color: pink"
            else:
                return "background-color: pink"
    # Fallback: if we cannot split properly, check for any valid grade token in the string.
    tokens = value.split(',')
    if any(t.strip().upper() in GRADE_ORDER for t in tokens):
        return "background-color: lightgreen"
    return "background-color: pink"
