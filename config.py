import streamlit as st

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def get_grade_hierarchy():
    """
    Returns the grade hierarchy from highest to lowest.
    Highest: A+, then A, A-, B+, B, B-, C+, C, C-, D+, D, D-.
    """
    return ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]
