# ui_components.py

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, ColumnsAutoSizeMode

def display_dataframes(required_df, intensive_df, extra_courses_df, raw_df):
    st.subheader("Required Courses Progress Report")
    _show_aggrid(required_df)

    st.subheader("Intensive Courses Progress Report")
    _show_aggrid(intensive_df)

    st.subheader("Extra Courses Detailed View")
    st.dataframe(extra_courses_df)  # leave editable assignment logic intact

def _show_aggrid(df):
    """
    Renders a pandas DataFrame in an AgGrid with:
     - First two columns (ID, NAME) pinned
     - Columns sortable and filterable
     - Columns auto‑sized
     - Course columns grouped by their alphabetical prefix
    """
    gb = GridOptionsBuilder.from_dataframe(df)

    # 1) Pin ID & NAME
    if "ID" in df.columns:
        gb.configure_column("ID", pinned="left")
    if "NAME" in df.columns:
        gb.configure_column("NAME", pinned="left")

    # 2) Enable sorting, filtering, resizing
    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True
    )

    # 3) Group related course columns by prefix (letters before digits)
    prefix_map = {}
    for col in df.columns:
        if col in ("ID", "NAME"):
            continue
        # Extract leading letters as the group key
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

    # 4) Build and display
    grid_options = gb.build()
    AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        height=400,  # adjust as needed
        fit_columns_on_grid_load=True
    )
