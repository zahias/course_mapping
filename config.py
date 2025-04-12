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

# For backward compatibility.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Legacy cell_color function (not used in the new approach).
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
    Revised cell color function that recomputes the pass/fail status using the best grade.

    Parameters:
      - value: Processed cell string in the form "grade tokens | marker".
      - course_code: The course identifier (column name).
      - courses_config: The course configuration dictionary for this category (target_courses or intensive_courses).

    Logic:
      - If value starts with "CR", return light yellow.
      - Otherwise, split value by the pipe character ("|") and extract the grade tokens (left part).
      - From the list of tokens (uppercased), compute the best grade based on GRADE_ORDER.
      - Look up the allowed passing grades for this course (from courses_config).
      - If the best grade is in the allowed passing list, return light green; otherwise, return pink.
    """
    if not isinstance(value, str):
        return ''
    val = value.strip()
    if val.upper().startswith("CR"):
        return 'background-color: #FFFACD'
    parts = val.split("|")
    if len(parts) < 2:
        return 'background-color: pink'
    grade_tokens = parts[0].strip()  # e.g., "D, F"
    tokens = [t.strip().upper() for t in grade_tokens.split(",") if t.strip()]
    if not tokens:
        return 'background-color: pink'
    # Determine the best grade among tokens: lower index in GRADE_ORDER means better.
    best_token = None
    best_index = len(GRADE_ORDER) + 1
    for token in tokens:
        if token in GRADE_ORDER:
            idx = GRADE_ORDER.index(token)
        else:
            # Unknown tokens are treated as worst.
            idx = len(GRADE_ORDER)
        if idx < best_index:
            best_index = idx
            best_token = token
    # Retrieve allowed passing grades for the course from courses_config.
    allowed_str = courses_config.get(course_code, {}).get("PassingGrades", "")
    allowed_grades = [x.strip().upper() for x in allowed_str.split(",") if x.strip()]
    # Debug: You might want to log best_token and allowed_grades for troubleshooting.
    if best_token and best_token in allowed_grades:
        return 'background-color: lightgreen'
    else:
        return 'background-color: pink'
