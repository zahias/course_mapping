import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types.
    If the user has set custom values in session state, that list is returned.
    Otherwise, defaults to ["S.C.E", "F.E.C"].
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the given grade is one of the passing grades specified (as a comma-separated list).
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility
is_passing_grade = is_passing_grade_from_list

def simplify_for_toggle(value: str) -> str:
    """
    Given a processed cell value in the format "<grade tokens> | <credit or marker>",
    returns "c" if the course is passed (that is, if the credit value is > 0 or the marker is "PASS"),
    otherwise returns an empty string.
    """
    if not isinstance(value, str) or '|' not in value:
        return ""
    parts = value.split('|')
    if len(parts) < 2:
        return ""
    credit_str = parts[1].strip()
    if credit_str.isdigit():
        if int(credit_str) > 0:
            return "c"
        else:
            return ""
    else:
        if credit_str.upper() == "PASS":
            return "c"
        else:
            return ""

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the background color of a cell.
    
    - If the value starts with "CR", it is considered currently registered and is colored light yellow.
    - Otherwise, we use the simplified toggle logic:
         If simplify_for_toggle() returns "c" (course passed), we color the cell green.
         If it returns an empty string (course not passed), we color it red.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith('CR'):
        return 'background-color: #FFFACD'
    toggle_val = simplify_for_toggle(value)
    if toggle_val == "c":
        return 'background-color: lightgreen'
    else:
        return 'background-color: red'
