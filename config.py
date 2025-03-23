import streamlit as st
import json
import os

ASSIGNMENT_TYPES_FILE = "assignment_types.json"

def load_assignment_types():
    if os.path.exists(ASSIGNMENT_TYPES_FILE):
        try:
            with open(ASSIGNMENT_TYPES_FILE, "r") as f:
                data = json.load(f)
            return data
        except Exception as e:
            st.error(f"Error loading assignment types: {e}")
            return ["S.C.E", "F.E.C"]
    return ["S.C.E", "F.E.C"]

def save_assignment_types(assignment_types):
    try:
        with open(ASSIGNMENT_TYPES_FILE, "w") as f:
            json.dump(assignment_types, f)
    except Exception as e:
        st.error(f"Error saving assignment types: {e}")

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
    On first load, it reads from a persistent file.
    """
    if "allowed_assignment_types" not in st.session_state:
        st.session_state["allowed_assignment_types"] = load_assignment_types()
    return st.session_state["allowed_assignment_types"]
