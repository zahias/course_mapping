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
    Checks if the given grade is in the list of allowed passing grades (comma‑separated).
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
    Legacy cell_color function (not used in our new approach).
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
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(g in GRADE_ORDER for g in tokens):
        return 'background-color: lightgreen'
    return 'background-color: pink'

def cell_color_for_course(value: str, course_code: str, courses_config: dict) -> str:
    """
    New cell color function that re-computes pass/fail by using the allowed passing grades 
    from the course configuration.
    
    Parameters:
      - value: The processed cell value string, e.g. "B, A | 3" or "D, F | 0" or "P | PASS".
      - course_code: The course identifier (which is the column name in the pivot table).
      - courses_config: Dictionary of course configuration for that category (target_courses or intensive_courses).
      
    Logic:
      - If value begins with "CR", return light yellow.
      - Otherwise, split the value by "|" to extract the grade tokens.
      - Retrieve the allowed passing grades (a comma-separated string) from courses_config for the course.
      - Split that string into a list.
      - If at least one token (after uppercasing) is found in the allowed passing list, return light green.
      - Otherwise, return pink.
    """
    if not isinstance(value, str):
        return ''
    val = value.strip()
    if val.upper().startswith("CR"):
        return 'background-color: #FFFACD'
    parts = val.split("|")
    if len(parts) < 2:
        # Fallback to legacy approach if format unexpected.
        tokens = [g.strip().upper() for g in val.split(",") if g.strip()]
        if any(token in GRADE_ORDER for token in tokens):
            return 'background-color: lightgreen'
        return 'background-color: pink'
    grade_tokens = parts[0].strip()
    tokens = [t.strip().upper() for t in grade_tokens.split(",") if t.strip()]
    # Retrieve allowed passing grades for this course.
    allowed_str = courses_config.get(course_code, {}).get("PassingGrades", "")
    allowed_grades = [x.strip().upper() for x in allowed_str.split(",") if x.strip()]
    if any(token in allowed_grades for token in tokens):
        return 'background-color: lightgreen'
    else:
        return 'background-color: pink'
