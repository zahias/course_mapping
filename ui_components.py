# ui_components.py

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, ColumnsAutoSizeMode

def display_dataframes(required_df, intensive_df, extra_courses_df, raw_df):
    """Render the required and intensive DataFrames with AgGrid, and extra_courses with st.dataframe."""
    st.subheader("Required Courses Progress Report")
    _show_aggrid(required_df)

    st.subheader("Intensive Courses Progress Report")
    _show_aggrid(intensive_df)

    st.subheader("Extra Courses Detailed View")
    st.dataframe(extra_courses_df, use_container_width=True)


def _show_aggrid(df):
    """
    Renders a pandas DataFrame in an AgGrid with:
      - ID & NAME columns pinned (frozen) to the left
      - Column sorting & filtering enabled
      - Columns auto‑sized to fit the view
      - Grouping of columns by their leading alphabetical prefix
    """
    gb = GridOptionsBuilder.from_dataframe(df)

    # 1) Pin ID & NAME
    if "ID" in df.columns:
        gb.configure_column("ID", pinned="left", header_name="ID")
    if "NAME" in df.columns:
        gb.configure_column("NAME", pinned="left", header_name="NAME")

    # 2) Default: sortable, filterable, resizable
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    # 3) Group columns by alphabetical prefix (letters before digits)
    prefix_map = {}
    for col in df.columns:
        if col in ("ID", "NAME"):
            continue
        prefix = ""
        for ch in col:
            if ch.isalpha():
                prefix += ch
            else:
                break
        if not prefix:
            prefix = "Other"
        prefix_map.setdefault(prefix, []).append(col)

    for group, cols in prefix_map.items():
        for col in cols:
            gb.configure_column(col, column_group=group)

    # 4) Build options and display
    grid_options = gb.build()
    AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        height=400,
        fit_columns_on_grid_load=True
    )


def add_assignment_selection(extra_courses_df):
    """
    Presents the extra_courses_df in a Data Editor for assignment selection.
    Returns the edited DataFrame for further validation.
    """
    # We assume extra_courses_df already has the boolean columns for each assignment type.
    edited = st.data_editor(
        extra_courses_df,
        num_rows="dynamic",
        use_container_width=True,
        key="extra_courses_editor"
    )
    return edited
