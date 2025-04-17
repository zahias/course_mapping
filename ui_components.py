import streamlit as st
import re
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

def display_dataframes(styled_req_df, styled_int_df, extra_courses_df, raw_df):
    """
    Displays the Required, Intensive, and Extra Courses dataframes using AgGrid for advanced UI:
    - Freezes ID/NAME columns
    - Groups related courses by prefix (e.g., PBHL)
    - Enables multi-criteria filters and sorting
    """
    tab1, tab2, tab3 = st.tabs(["Required Courses", "Intensive Courses", "Extra Courses"])

    def aggrid_from_styler(styler_df):
        # Extract underlying DataFrame
        df = styler_df.data if hasattr(styler_df, 'data') else styler_df

        # Identify summary columns (credit totals) and course columns
        summary_cols = [c for c in df.columns if c.startswith('#') or c == 'Total Credits']
        course_cols = [c for c in df.columns if c not in ['ID', 'NAME'] + summary_cols]

        # Build column definitions
        col_defs = []
        # Freeze ID and NAME
        col_defs.append({
            'headerName': 'ID', 'field': 'ID', 'pinned': 'left', 'sortable': True, 'filter': True,
            'lockPosition': True
        })
        col_defs.append({
            'headerName': 'NAME', 'field': 'NAME', 'pinned': 'left', 'sortable': True, 'filter': True,
            'lockPosition': True
        })

        # Group course columns by prefix
        groups = {}
        for col in course_cols:
            m = re.match(r'([A-Za-z]+)', col)
            prefix = m.group(1).upper() if m else 'Other'
            groups.setdefault(prefix, []).append(col)

        for prefix, cols in sorted(groups.items()):
            if len(cols) > 1:
                # create a group
                children = []
                for c in sorted(cols):
                    children.append({
                        'headerName': c, 'field': c,
                        'sortable': True, 'filter': 'agMultiColumnFilter',
                        'cellStyle': {'overflow': 'visible'}
                    })
                col_defs.append({
                    'headerName': prefix, 'children': children
                })
            else:
                c = cols[0]
                col_defs.append({
                    'headerName': c, 'field': c,
                    'sortable': True, 'filter': 'agMultiColumnFilter',
                    'cellStyle': {'overflow': 'visible'}
                })

        # Add summary columns last
        for c in summary_cols:
            col_defs.append({
                'headerName': c, 'field': c,
                'sortable': True, 'filter': 'agNumberColumnFilter',
                'type': 'rightAligned'
            })

        # Build grid options
        gb = GridOptionsBuilder()
        gb.configure_grid_options(columnDefs=col_defs)
        gb.configure_default_column(resizable=True)
        gb.configure_grid_options(
            suppressMovableColumns=False,
            enableRangeSelection=False,
            suppressFieldDotNotation=True
        )
        grid_options = gb.build()

        # Render
        return AgGrid(
            df,
            gridOptions=grid_options,
            height=400,
            width='100%',
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True
        )

    with tab1:
        st.subheader("Required Courses Progress Report")
        st.markdown("Courses needed to fulfill the curriculum requirements.")
        aggrid_from_styler(styled_req_df)
        st.markdown("*Courses assigned as S.C.E. or F.E.C. are included here once selected.*")

    with tab2:
        st.subheader("Intensive Courses Progress Report")
        st.markdown("These are intensive courses required for the curriculum.")
        aggrid_from_styler(styled_int_df)
        st.markdown("*Intensive courses are displayed separately.*")

    with tab3:
        st.subheader("Extra Courses Detailed View")
        st.markdown("Courses that are not part of the main or intensive list. They may be assigned as S.C.E. or F.E.C.")
        st.dataframe(extra_courses_df, use_container_width=True)

# Optionally, if you have an add_assignment_selection in this file:
# def add_assignment_selection(extra_courses_df): ...
