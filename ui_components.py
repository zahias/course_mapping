# ui_components.py
# Helpers for displaying dataframes and interactive assignment editing

from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import List, Optional
from config import get_allowed_assignment_types

# -----------------------------
# Display helpers
# -----------------------------

def display_dataframes(
    styled_required: pd.io.formats.style.Styler,
    styled_intensive: pd.io.formats.style.Styler,
    extra_courses_df: pd.DataFrame,
    raw_df: pd.DataFrame
) -> None:
    """
    Renders the Required, Intensive styled tables and the raw 'extras' table in tabs.
    """
    tab1, tab2, tab3 = st.tabs(["Required", "Intensive", "Extras (raw)"])

    with tab1:
        st.dataframe(styled_required, use_container_width=True, height=450)

    with tab2:
        st.dataframe(styled_intensive, use_container_width=True, height=350)

    with tab3:
        if extra_courses_df is not None and not extra_courses_df.empty:
            st.dataframe(
                extra_courses_df.sort_values(["NAME", "ID", "Course"]),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No extra courses to display.")


# -----------------------------
# Assign Courses editor
# -----------------------------

def add_assignment_selection(
    filtered_extras: pd.DataFrame,
    allowed_assignment_types: Optional[List[str]] = None,
    *,
    key: str = "assign_editor"
) -> pd.DataFrame:
    """
    Returns an editable DataFrame for assigning 'extra' courses to requirement slots
    (assignment types). The available assignment types are read dynamically:

      - If `allowed_assignment_types` is provided, use it.
      - Else, call `config.get_allowed_assignment_types()` at *render time*.

    Expected input columns in `filtered_extras`:
        ["ID", "NAME", "Course", "Grade", "Year", "Semester"]   (extra rows are fine with more cols)

    Output:
        A DataFrame with an added/updated column "AssignTo" containing the chosen slot per row.

    Notes:
      - We do not persist anything here; saving is handled by assignment_utils.save_assignments().
      - We intentionally do NOT cache the options to ensure Customize Courses changes propagate.
    """
    df = filtered_extras.copy()

    # Normalize required columns presence
    for col in ["ID", "NAME", "Course"]:
        if col not in df.columns:
            df[col] = ""

    # Pull dynamic types each render
    opts = allowed_assignment_types
    if opts is None:
        opts = get_allowed_assignment_types()

    # Make them strings, keep display as entered by user in Customize Courses
    opts = [str(x) for x in opts if str(x).strip()]

    # Provide an explicit "no assignment" choice
    select_options = ["— None —"] + opts

    # Ensure we have the editable "AssignTo" column
    if "AssignTo" not in df.columns:
        df["AssignTo"] = "— None —"
    else:
        # Coerce any stale values to legal ones
        df["AssignTo"] = df["AssignTo"].apply(
            lambda v: v if v in select_options else "— None —"
        )

    # Show an editor with a dropdown per row
    # Note: We restrict editing to the AssignTo column only.
    editable_cols = {
        "AssignTo": st.column_config.SelectboxColumn(
            "Assign To (slot)",
            options=select_options,
            help="Choose which requirement slot this course should fulfill.",
            required=False,
            width="small"
        )
    }

    st.caption(
        f"Active assignment types: {', '.join(opts) if opts else '(none configured)'}"
    )

    edited = st.data_editor(
        df[["ID", "NAME", "Course", "Semester", "Year", "Grade", "AssignTo"]]
        if set(["Semester", "Year", "Grade"]).issubset(df.columns)
        else df[["ID", "NAME", "Course", "AssignTo"]],
        column_config=editable_cols,
        disabled=[c for c in ["ID", "NAME", "Course", "Semester", "Year", "Grade"] if c in df.columns],
        num_rows="fixed",
        use_container_width=True,
        key=key
    )

    # Return full original columns + possibly updated AssignTo
    out = filtered_extras.copy()
    out = out.merge(
        edited[["ID", "Course", "AssignTo"]],
        on=["ID", "Course"],
        how="left",
        suffixes=("", "_ed")
    )
    # Prefer edited AssignTo
    out["AssignTo"] = out["AssignTo_ed"].fillna(out.get("AssignTo", "— None —"))
    out.drop(columns=[c for c in ["AssignTo_ed"] if c in out.columns], inplace=True)

    return out
