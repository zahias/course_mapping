import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

# Semester index for computing a linear code: FALL→0, SPRING→1, SUMMER→2
SEM_INDEX = {'Fall': 0, 'Spring': 1, 'Summer': 2}

def select_config(defs, record_code):
    """
    From a list of definitions, select the one whose [Eff_From, Eff_To]
    range includes record_code. If multiple, pick the one with the largest Eff_From.
    """
    candidates = []
    for d in defs:
        ef = d['Eff_From']
        et = d['Eff_To']
        ok_from = (ef is None) or (record_code >= ef)
        ok_to   = (et is None) or (record_code <= et)
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
        # pick the one with max Eff_From (None→treated as 0)
        return max(candidates, key=lambda d: d['Eff_From'] or 0)
    # fallback
    return defs[0]

def determine_course_value(grade_str, course, cfg_list, record_code):
    """
    Determine the cell value for a single course pivot:
      - Picks the config entry valid at record_code
      - Then applies passing‐grade logic to grade_str tokens
      - Uses Credits from that config entry
    """
    if pd.isna(grade_str):
        return "NR"
    if grade_str=="":
        cfg = select_config(cfg_list, record_code)
        return f"CR | {cfg['Credits']}"

    cfg = select_config(cfg_list, record_code)
    credits = cfg['Credits']
    passing = [g.strip().upper() for g in cfg['PassingGrades'].split(',')]

    tokens = [g.strip().upper() for g in grade_str.split(',') if g.strip()]
    tok_display = ", ".join(tokens)
    passed = any(tok in passing for tok in tokens)

    if credits > 0:
        return f"{tok_display} | {credits}" if passed else f"{tok_display} | 0"
    else:
        return f"{tok_display} | PASS" if passed else f"{tok_display} | FAIL"

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _, row in equiv_df.iterrows():
        prim = row['Course'].strip().upper()
        equivs = [e.strip().upper() for e in str(row['Equivalent']).split(',')]
        for e in equivs:
            mapping[e] = prim
    return mapping

def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    # 1) Compute a record code per row
    df['RecordCode'] = df.apply(
        lambda r: int(r['Year']) * 3 + SEM_INDEX[r['Semester']],
        axis=1
    )

    # 2) Map equivalent courses
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # 3) Apply S.C.E./F.E.C. assignments
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(row):
            sid = str(row['ID'])
            crs = row['Course']
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for t in allowed:
                    if assigns.get(t)==crs:
                        return t
            return row['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # 4) Split into required/intensive/extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) &
                  ~df['Mapped Course'].isin(intensive_cfg)]

    # 5) Build pivots for grades and for record‐code
    grade_piv_req = req_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='Grade',
        aggfunc=lambda x: ", ".join(x.astype(str))
    ).reset_index()
    code_piv_req = req_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='RecordCode',
        aggfunc='max'
    ).reset_index().fillna(0)

    grade_piv_int = int_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='Grade',
        aggfunc=lambda x: ", ".join(x.astype(str))
    ).reset_index()
    code_piv_int = int_df.pivot_table(
        index=['ID','NAME'], columns='Mapped Course', values='RecordCode',
        aggfunc='max'
    ).reset_index().fillna(0)

    # 6) Ensure all columns exist & apply determine_course_value
    def finalize(piv_grad, piv_code, cfg_dict):
        for course in cfg_dict.keys():
            if course not in piv_grad.columns:
                piv_grad[course] = None
            # apply time‐aware logic
            piv_grad[course] = piv_grad.apply(
                lambda r: determine_course_value(
                    r[course],
                    course,
                    cfg_dict[course],
                    int(piv_code.at[r.name, course] if course in piv_code else 0)
                ),
                axis=1
            )
        return piv_grad[['ID','NAME'] + list(cfg_dict.keys())]

    req_final = finalize(grade_piv_req, code_piv_req, target_cfg)
    int_final = finalize(grade_piv_int, code_piv_int, intensive_cfg)

    extra_list = sorted(extra_df['Course'].unique())
    return req_final, int_final, extra_df, extra_list
