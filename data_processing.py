import pandas as pd
import streamlit as st
from config import is_passing_grade_from_list, GRADE_ORDER, get_allowed_assignment_types

# Map semester names to order
SEM_ORDER = {'Spring':1,'Summer':2,'Fall':3}

def select_course_definition(defs, year, sem):
    """
    From a list of definitions (each with Effective_From/To),
    pick the one whose date‑range includes (year,sem). If multiple,
    choose the one with the latest Effective_From. If none match,
    fallback to the first definition.
    """
    candidates = []
    for d in defs:
        ok_from = True
        ef = d['Effective_From']
        if ef:
            e_sem, e_year = ef
            if (year < e_year) or (year==e_year and SEM_ORDER[sem]<SEM_ORDER[e_sem]):
                ok_from = False
        ok_to = True
        et = d['Effective_To']
        if et:
            t_sem, t_year = et
            if (year > t_year) or (year==t_year and SEM_ORDER[sem]>SEM_ORDER[t_sem]):
                ok_to = False
        if ok_from and ok_to:
            candidates.append(d)
    if candidates:
        # pick with max Effective_From date
        def keyfn(d):
            ef = d['Effective_From']
            if not ef:
                return (0,0)
            s,y = ef
            return (y, SEM_ORDER[s])
        return max(candidates, key=keyfn)
    return defs[0]

def determine_course_value(grade, course, courses_config, year, semester):
    """
    Time‑aware determine value:
     - Pick appropriate course definition for this (year,semester).
     - Use its PassingGrades and Credits.
     - Then same logic: if grade missing→NR; if ""→CR; else test passing via is_passing_grade_from_list.
    """
    defs = courses_config.get(course)
    if not defs:
        st.error(f"No config for course {course}")
        return "NR"
    cfg = select_course_definition(defs, year, semester)
    credits = cfg['Credits']
    pass_str = cfg['PassingGrades']
    if pd.isna(grade):
        return "NR"
    if grade=="":
        return f"CR | {credits}"
    tokens = [g.strip().upper() for g in grade.split(',')]
    passed = any(is_passing_grade_from_list(tok,pass_str) for tok in tokens)
    toklist = ", ".join(tokens)
    if credits>0:
        return f"{toklist} | {credits}" if passed else f"{toklist} | 0"
    else:
        return f"{toklist} | PASS" if passed else f"{toklist} | FAIL"

def process_progress_report(
    df,
    target_cfg,
    intensive_cfg,
    per_student_assignments=None,
    equivalent_courses_mapping=None
):
    # Map equivalents
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    df['Mapped Course'] = df['Course'].apply(lambda x: equivalent_courses_mapping.get(x,x))
    # Apply S.C.E/F.E.C...
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def map_assign(r):
            sid,str_course = str(r['ID']), r['Course']
            if sid in per_student_assignments:
                assigns = per_student_assignments[sid]
                for t in allowed:
                    if assigns.get(t)==str_course:
                        return t
            return r['Mapped Course']
        df['Mapped Course'] = df.apply(map_assign,axis=1)
    # Split into required/intensive/extra
    req_df = df[df['Mapped Course'].isin(target_cfg)]
    int_df = df[df['Mapped Course'].isin(intensive_cfg)]
    extra_df = df[~df['Mapped Course'].isin(target_cfg) & ~df['Mapped Course'].isin(intensive_cfg)]
    # Pivot
    def pivot_and_process(group_df, cfg_dict):
        piv = group_df.pivot_table(
            index=['ID','NAME'], columns='Mapped Course', values='Grade',
            aggfunc=lambda x: ', '.join(x.astype(str))
        ).reset_index()
        # Ensure all columns exist
        for c in cfg_dict:
            if c not in piv.columns:
                piv[c] = None
        # Apply determine_course_value
        for c in cfg_dict:
            piv[c] = piv.apply(
                lambda r: determine_course_value(
                    r[c], c, cfg_dict, int(r['Year']), r['Semester']
                ),
                axis=1
            )
        return piv[['ID','NAME'] + list(cfg_dict.keys())]
    req_piv = pivot_and_process(req_df, target_cfg)
    int_piv = pivot_and_process(int_df, intensive_cfg)
    # Build extra list
    extra_list = sorted(extra_df['Course'].unique())
    return req_piv, int_piv, extra_df, extra_list

def calculate_credits(row, courses_config, year, semester):
    """
    For each required/intensive course in courses_config,
    recalc completed, registered, remaining, total exactly as before,
    but using time‑aware credits.
    """
    comp = reg = rem = tot = 0
    for course, defs in courses_config.items():
        cfg = select_course_definition(defs, year, semester)
        cred = cfg['Credits']
        tot += cred
        val = row.get(course,'')
        if isinstance(val,str) and val.upper().startswith('CR'):
            reg += cred
        elif isinstance(val,str) and val.upper().startswith('NR'):
            rem += cred
        elif isinstance(val,str):
            parts = val.split('|')
            if len(parts)==2:
                right = parts[1].strip()
                try:
                    num = int(right)
                    if num>0:
                        comp += cred
                    else:
                        rem += cred
                except ValueError:
                    if right.upper()=='PASS':
                        # 0-credit passed
                        pass
                    else:
                        rem += cred
            else:
                rem += cred
        else:
            rem += cred
    return pd.Series([comp,reg,rem,tot],
                     index=['# of Credits Completed','# Registered','# Remaining','Total Credits'])
