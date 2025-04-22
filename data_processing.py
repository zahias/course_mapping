import pandas as pd
import streamlit as st
from config import is_passing_grade_from_list, get_allowed_assignment_types

# Academic semester ordering for comparisons
SEM_ORDER = {'Fall': 1, 'Spring': 2, 'Summer': 3}

def select_course_definition(defs, year, sem):
    """
    From defs (a list of course‐config entries), pick the one whose
    Effective_From/To includes (year, sem). If none match, return defs[0].
    """
    candidates = []
    for d in defs:
        ef = d['Effective_From']
        et = d['Effective_To']
        ok_from = True
        if ef:
            e_sem, e_yr = ef
            if (year < e_yr) or (year == e_yr and SEM_ORDER[sem] < SEM_ORDER[e_sem]):
                ok_from = False
        ok_to = True
        if et:
            t_sem, t_yr = et
            if (year > t_yr) or (year == t_yr and SEM_ORDER[sem] > SEM_ORDER[t_sem]):
                ok_to = False
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
        # Pick the one with the latest Effective_From
        def keyfn(d):
            ef = d['Effective_From']
            if not ef:
                return (0, 0)
            s, y = ef
            return (y, SEM_ORDER[s])
        return max(candidates, key=keyfn)
    return defs[0]

def determine_course_value(grade, course, courses_cfg, year, semester):
    """
    Time‐aware grading: pick the correct cfg entry for (year,semester),
    then test grade tokens against its PassingGrades; return "tokens | credits" or "tokens | 0"/PASS/FAIL.
    """
    defs = courses_cfg.get(course, [])
    if not defs:
        st.error(f"No configuration for course {course}")
        return "NR"
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    passing = cfg['PassingGrades']
    if pd.isna(grade):
        return "NR"
    if grade == "":
        return f"CR | {credits}"
    tokens = [g.strip().upper() for g in grade.split(',') if g.strip()]
    passed = any(is_passing_grade_from_list(tok, passing) for tok in tokens)
    tokstr = ", ".join(tokens)
    if credits > 0:
        return f"{tokstr} | {credits}" if passed else f"{tokstr} | 0"
    else:
        return f"{tokstr} | PASS" if passed else f"{tokstr} | FAIL"

def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}

    # Map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x, x))

    # Apply assignments (S.C.E. / F.E.C. / etc.)
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid = str(r['ID'])
            crs = r['Course']
            if sid in per_student_assignments:
                for a in allowed:
                    if per_student_assignments[sid].get(a) == crs:
                        return a
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign, axis=1)

    # Partition
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[
        ~df['Mapped Course'].isin(target_cfg)
        & ~df['Mapped Course'].isin(intensive_cfg)
    ]

    # Pivot & process
    def pivot_process(subdf, cfg_dict):
        piv = subdf.pivot_table(
            index=['ID','NAME','Year','Semester'],
            columns='Mapped Course',
            values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # Ensure all columns
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # Apply time‐aware grading
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c],
                    c,
                    cfg_dict,
                    int(r['Year']),
                    r['Semester']
                ),
                axis=1
            )
        # Drop Year,Semester for final
        return piv[['ID','NAME'] + list(cfg_dict.keys())]

    req_piv = pivot_process(req_df, target_cfg)
    int_piv = pivot_process(int_df, intensive_cfg)

    return req_piv, int_piv, extra_df, sorted(extra_df['Course'].unique())

def calculate_credits(row, credits_dict):
    """
    Static credit summation. credits_dict maps course->credit (int).
    """
    completed = registered = remaining = 0
    total = sum(credits_dict.values())
    for course, cred in credits_dict.items():
        val = row.get(course, "")
        if isinstance(val, str):
            u = val.upper()
            if u.startswith("CR"):
                registered += cred
            elif u.startswith("NR"):
                remaining += cred
            else:
                right = val.split("|")[-1].strip()
                try:
                    num = int(right)
                    if num > 0:
                        completed += cred
                    else:
                        remaining += cred
                except ValueError:
                    if right.upper() == "PASS":
                        # 0‐credit passed
                        pass
                    else:
                        remaining += cred
        else:
            remaining += cred

    return pd.Series(
        [completed, registered, remaining, total],
        index=['# of Credits Completed', '# Registered', '# Remaining', 'Total Credits']
    )
