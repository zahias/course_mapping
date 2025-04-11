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
    Checks if the given grade is one of the passing grades specified in the course configuration.
    
    Parameters:
      - grade: The grade to evaluate (e.g., "B+").
      - passing_grades_str: A comma-separated string of all passing grades (e.g., "A+,A,A-").
    
    Returns:
      - True if the grade (after uppercasing and trimming) is contained in the passing grades list.
      - False otherwise.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility, export is_passing_grade as an alias to is_passing_grade_from_list.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the background color of a cell based on its value.
    
    Rules:
      - If the value starts with "CR", returns light yellow (#FFFACD) to indicate a "Currently Registered" cell.
      - Otherwise, the value is split at the pipe character ("|") to extract the portion with grade information.
        If any token in that part is present in GRADE_ORDER (i.e. it is a valid grade), returns light green.
      - If no valid grade is found, returns pink.
    """
    if not isinstance(value, str):
        return ''
    value_upper = value.upper()
    if value_upper.startswith('CR'):
        return 'background-color: #FFFACD'
    parts = value.split('|')
    if parts:
        grades_part = parts[0]
        grades_list = [g.strip().upper() for g in grades_part.split(',') if g.strip()]
        if any(g in GRADE_ORDER for g in grades_list):
            return 'background-color: lightgreen'
    return 'background-color: pink'
