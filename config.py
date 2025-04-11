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

# For backward compatibility, export is_passing_grade as an alias.
is_passing_grade = is_passing_grade_from_list

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for the background color of a cell based on the processed grade value.
    
    The processed value is expected to be in the format:
    
        "grade tokens | marker"
    
    Where 'marker' is:
      - A numeric value (the number of credits earned for the course),
      - or a text marker ("PASS" or "FAIL") for courses with 0 credits,
      - or "CR" for currently registered courses.
    
    Rules:
      - If the value starts with "CR", return light yellow (#FFFACD).
      - Otherwise, split the string using the pipe character ("|").
        If a second part exists:
          * Try to convert it to an integer:
              - If the integer is > 0, return light green (passed).
              - If the integer is 0, return pink (failed).
          * If conversion fails:
              - If the marker (after uppercasing) is "PASS", return light green.
              - If it is "FAIL", return pink.
      - If no second part is present or if none of the above conditions match, default to pink.
    """
    if not isinstance(value, str):
        return ''
    
    value = value.strip()
    # Check for "CR" indicating currently registered.
    if value.upper().startswith("CR"):
        return 'background-color: #FFFACD'
    
    parts = value.split("|")
    if len(parts) >= 2:
        marker = parts[1].strip()
        # Try to interpret marker as an integer.
        try:
            numeric = int(marker)
            if numeric > 0:
                return 'background-color: lightgreen'
            else:
                return 'background-color: pink'
        except ValueError:
            # If conversion fails, check text markers.
            if marker.upper() == "PASS":
                return 'background-color: lightgreen'
            elif marker.upper() == "FAIL":
                return 'background-color: pink'
    
    # Fallback: if marker cannot be determined, check if any grade token (from left-hand part) is in GRADE_ORDER.
    tokens = [g.strip().upper() for g in parts[0].split(",") if g.strip()]
    if any(token in GRADE_ORDER for token in tokens):
        return 'background-color: lightgreen'
    return 'background-color: pink'
