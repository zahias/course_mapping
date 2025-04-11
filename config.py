import streamlit as st
from dataclasses import dataclass

# Global grade order (from highest to lowest); can be used for fallback if needed.
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

@dataclass
class CourseResult:
    display: str   # Text to show in the cell
    passed: bool   # True if course passed, False if failed; None for "Currently Registered" (CR)
    credit: int    # The numeric credit awarded; for 0-credit courses, credit remains 0 but we use pass/fail marker

def get_allowed_assignment_types():
    """
    Returns the list of assignment types as defined in session state or default.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def is_passing_grade_from_list(grade: str, passing_grades_str: str) -> bool:
    """
    Returns True if the provided grade (after stripping and uppercasing) is in the comma-separated passing grades list.
    """
    try:
        passing_grades = [x.strip().upper() for x in passing_grades_str.split(',')]
    except Exception:
        passing_grades = []
    return grade.strip().upper() in passing_grades

# For backward compatibility.
is_passing_grade = is_passing_grade_from_list

def cell_color(value) -> str:
    """
    Determine cell color based on a CourseResult or a legacy string.
    
    If value is a CourseResult:
      - If the display text starts with "CR", return light yellow.
      - If passed is True, return light green.
      - If passed is False, return pink.
    
    If value is a string, use fallback logic.
    """
    if isinstance(value, CourseResult):
        if value.display.upper().startswith("CR"):
            return 'background-color: #FFFACD'
        if value.passed is True:
            return 'background-color: lightgreen'
        elif value.passed is False:
            return 'background-color: pink'
        else:
            return 'background-color: pink'
    elif isinstance(value, str):
        val = value.strip()
        if val.upper().startswith("CR"):
            return 'background-color: #FFFACD'
        # Fallback: simple heuristic
        parts = val.split("|")
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
        return 'background-color: pink'
    return ''
