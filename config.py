import streamlit as st

# Global grade order (from highest to lowest)
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    """
    Returns the list of assignment types (editable via session state).
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Checks if the grade is one of the acceptable passing grades.
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
    This is the default cell color function for full-detail grade display.
    It parses the processed grade string (e.g. "B, A | 3") and returns a color.
    (Not used when the simplified 'completed' toggle is on.)
    """
    if not isinstance(value, str):
        return ''
    
    value = value.strip()
    if value.upper().startswith("CR"):
        return 'background-color: #FFFACD'
    
    parts = value.split("|")
    if len(parts) >= 2:
        marker = parts[1].strip()
        try:
            numeric = int(marker)
            if numeric > 0:
                return 'background-color: lightgreen'
            else:
                return 'background-color: pink'
        except ValueError:
            if marker.upper() == "PASS":
                return 'background-color: lightgreen'
            elif marker.upper() == "FAIL":
                return 'background-color: pink'
    # Fallback: if something is recognized in the grade tokens, return lightgreen
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(g in GRADE_ORDER for g in tokens):
        return 'background-color: lightgreen'
    return 'background-color: pink'

def simple_cell_color(value: str) -> str:
    """
    In the simplified mode (when the Completed/Not Completed toggle is on),
    each cell is processed to either be "c" (indicating passed) or blank.
    This function returns light green if the value is "c", and red otherwise.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value == "c":
        return "background-color: lightgreen"
    else:
        return "background-color: red"
