import streamlit as st

def get_default_target_courses():
    return {
        'ACCT201': 3, 'ARAB201': 3, 'BCOM300': 0, 'BIOL201': 3, 'CHEM201': 3,
        'CHEM202': 2, 'CHEM209': 3, 'CHEM210': 1, 'CIVL201': 3, 'CIVL202': 3,
        'CMPS202': 3, 'COMM201': 3, 'COMM214': 3, 'ENGL201': 3, 'ENGL202': 3,
        'F.E.C': 3, 'INFO404': 3, 'MNGT201': 3, 'PBHL201': 3, 'PBHL202': 3,
        'PBHL203': 3, 'PBHL204': 3, 'PBHL205': 3, 'PBHL206': 3, 'PBHL207': 3,
        'PBHL208': 3, 'PBHL211': 3, 'PBHL212': 3, 'PBHL213': 3, 'PBHL220': 3,
        'PBHL270': 0, 'PBHL280': 2, 'PBHL281': 1, 'PBHL282': 2, 'S.C.E': 3,
        'SOCL210': 3, 'STAT201': 3
    }

def get_default_grading_system():
    return {
        'Counted': ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'P', 'P*', 'WP', 'T'],
        'Not Counted': ['F', 'R', 'W', 'WF', 'I']
    }

def get_intensive_courses():
    return {
        'INEG200': 3,
        'INEG300': 3,
        'ENGL101': 3,
        'CHEM101': 3,
        'BIOL101': 3,
        'PHYS101': 3,
        'MATH101': 3,
        'MATH102': 3
    }

def get_allowed_assignment_types():
    """
    Returns the list of assignment types that can be used.
    If the user has set a custom list via the UI, that list is returned.
    Otherwise, default types are used.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def get_course_passing_thresholds():
    """
    Returns a dictionary mapping course codes to the minimum passing grade.
    For courses not specified here, the default passing grade is "D-".
    
    For example:
      - For ARAB201, you might require a grade above C (i.e. at least C+).
      - For many courses, D- might be acceptable.
    Adjust these values as needed.
    """
    return {
        'ARAB201': 'C+',  # For ARAB201, a student must earn at least a C+.
        'F.E.C': 'D-',    # For F.E.C and S.C.E, default passing is D-.
        'S.C.E': 'D-'
        # Other courses will use the default of "D-"
    }
