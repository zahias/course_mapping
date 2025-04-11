import streamlit as st

# Global grade order (from highest to lowest) remains defined here for any ordering needs.
GRADE_ORDER = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-"]

def get_allowed_assignment_types():
    if "allowed_assignment_types" in st.session_state:
        return st.session_state["allowed_assignment_types"]
    return ["S.C.E", "F.E.C"]

def cell_color(value: str) -> str:
    """
    Returns a CSS style string for background color based on the cell value.
    - If the cell value starts with 'CR', returns light yellow (#FFFACD).
    - Otherwise, if the cell value contains a vertical bar ('|'),
      the number after the bar is interpreted as the awarded credits.
      If that number is 0, the cell is considered not passing and will be colored pink;
      otherwise, it is colored light green.
    - In all other cases, returns an empty string.
    """
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if value.upper().startswith('CR'):
        return 'background-color: #FFFACD'
    if '|' in value:
        try:
            # Expecting the format "grade1, grade2, ... | credit"
            credit_part = value.split('|')[1].strip()
            credit = int(credit_part)
            return 'background-color: lightgreen' if credit > 0 else 'background-color: pink'
        except Exception:
            return 'background-color: pink'
    return 'background-color: pink'
