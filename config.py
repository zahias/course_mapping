import streamlit as st

def get_allowed_assignment_types():
    """
    Returns the list of assignment types that can be used.
    If the user has set a custom list via the UI, that list is returned.
    Otherwise, default types are used.
    """
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]
