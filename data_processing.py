import pandas as pd
import streamlit as st
from config import get_allowed_assignment_types

def read_progress_report(filepath):
    try:
        if filepath.lower().endswith(('.xlsx','.xls')):
            xls = pd.ExcelFile(filepath)
            if 'Progress Report' in xls.sheet_names:
                df = pd.read_excel(xls,sheet_name='Progress Report')
                req = {'ID','NAME','Course','Grade','Year','Semester'}
                if not req.issubset(df.columns):
                    missing = req - set(df.columns)
                    st.error(f"Missing columns: {missing}")
                    return None
                return df
            else:
                df = pd.read_excel(xls)
                return transform_wide_format(df)
        elif filepath.lower().endswith('.csv'):
            df = pd.read_csv(filepath)
            if {'Course','Grade','Year','Semester'}.issubset(df.columns):
                return df
            else:
                return transform_wide_format(df)
        else:
            st.error("Unsupported format.")
            return None
    except Exception as e:
        st.error(f"Read error: {e}")
        return None

def transform_wide_format(df):
    if 'STUDENT ID' not in df.columns or not any(c.startswith('COURSE') for c in df.columns):
        st.error("Wide format missing STUDENT ID or COURSE columns.")
        return None
    course_cols = [c for c in df.columns if c.startswith('COURSE')]
    id_vars = [c for c in df.columns if c not in course_cols]
    dfm = df.melt(id_vars=id_vars, var_name='Course_Column', value_name='CourseData')
    dfm = dfm[dfm['CourseData'].notna() & (dfm['CourseData']!='')]
    parts = dfm['CourseData'].str.split('/',expand=True)
    if parts.shape[1]<3:
        st.error("Expect COURSE/SEMESTER-YEAR/GRADE")
        return None
    dfm['Course']=parts[0].str.upper().str.strip()
    dfm['Semester_Year']=parts[1].str.strip()
    dfm['Grade']=parts[2].str.upper().str.strip()
    sy = dfm['Semester_Year'].str.split('-',expand=True)
    if sy.shape[1]<2:
        st.error("Expect SEMESTER-YEAR format")
        return None
    dfm['Semester']=sy[0].str.title().str.strip()
    dfm['Year']=sy[1].str.strip()
    dfm = dfm.rename(columns={'STUDENT ID':'ID','NAME':'NAME'})
    req = {'ID','NAME','Course','Grade','Year','Semester'}
    if not req.issubset(dfm.columns):
        st.error(f"Missing after transform: {req - set(dfm.columns)}")
        return None
    return dfm[list(req)].drop_duplicates()

def read_equivalent_courses(equiv_df):
    mapping = {}
    for _,r in equiv_df.iterrows():
        p = r['Course'].strip().upper()
        eqs = [e.strip().upper() for e in str(r['Equivalent']).split(',')]
        for e in eqs:
            mapping[e]=p
    return mapping

def process_progress_report(
    df,
    target_courses,
    intensive_courses,
    per_student_assignments=None,
    equivalent_courses_mapping=None,
    course_rules=None
):
    if equivalent_courses_mapping is None:
        equivalent_courses_mapping = {}
    if course_rules is None:
        course_rules = {}

    # compute numeric semester value
    sem_map = {'Spring':1,'Summer':2,'Fall':3}
    df['SemValue'] = df['Year'].astype(int)*10 + df['Semester'].map(sem_map)

    # map equivalents
    df['Mapped Course'] = df['Course'].apply(lambda c: equivalent_courses_mapping.get(c,c))

    # apply S.C.E./F.E.C.
    if per_student_assignments:
        allowed = get_allowed_assignment_types()
        def assign_map(r):
            sid = str(r['ID']); cr = r['Course']; mc = r['Mapped Course']
            if sid in per_student_assignments:
                for t in allowed:
                    if per_student_assignments[sid].get(t)==cr:
                        return t
            return mc
        df['Mapped Course'] = df.apply(assign_map,axis=1)

    # determine PassedFlag by effective rules
    def passed(r):
        course = r['Mapped Course']; grade = str(r['Grade']).strip().upper(); sv = r['SemValue']
        rules = course_rules.get(course,[])
        applicable = [ru for ru in rules if ru['eff']<=sv]
        if applicable:
            rule = max(applicable,key=lambda x:x['eff'])
        elif rules:
            rule = rules[0]
        else:
            return False
        return grade in rule['passing_grades']

    df['PassedFlag'] = df.apply(passed,axis=1)

    # split
    extra = df[
        ~df['Mapped Course'].isin(target_courses) &
        ~df['Mapped Course'].isin(intensive_courses)
    ]
    targ = df[df['Mapped Course'].isin(target_courses)]
    inten = df[df['Mapped Course'].isin(intensive_courses)]

    # pivot grades & flags
    pg = targ.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna,map(str,x)))
    ).reset_index()
    pp = targ.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    ipg = inten.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='Grade',
        aggfunc=lambda x: ', '.join(filter(pd.notna,map(str,x)))
    ).reset_index()
    ipp = inten.pivot_table(
        index=['ID','NAME'],
        columns='Mapped Course',
        values='PassedFlag',
        aggfunc='any'
    ).reset_index()

    # ensure all columns
    for c in target_courses:
        if c not in pg: pg[c]=None
        if c not in pp: pp[c]=False
    for c in intensive_courses:
        if c not in ipg: ipg[c]=None
        if c not in ipp: ipp[c]=False

    # merge to "grade | credits"
    def merge_row(g_row,f_row,cdict):
        out={}
        for course,cred in cdict.items():
            gs = g_row.get(course) or ''
            ok = bool(f_row.get(course))
            if gs=='':
                cell = 'NR'
            else:
                cell = f"{gs} | {cred if ok else 0}"
            out[course]=cell
        return out

    req_out = pg[['ID','NAME']].copy()
    for i,r in pg.iterrows():
        fo = merge_row(r,pp.iloc[i],target_courses)
        for k,v in fo.items():
            req_out.at[i,k] = v

    int_out = ipg[['ID','NAME']].copy()
    for i,r in ipg.iterrows():
        fo = merge_row(r,ipp.iloc[i],intensive_courses)
        for k,v in fo.items():
            int_out.at[i,k] = v

    extra_list = sorted(extra['Course'].unique())
    return req_out, int_out, extra, extra_list

def calculate_credits(row, courses_dict):
    completed,registered,remaining=0,0,0
    total=sum(courses_dict.values())
    for course,cred in courses_dict.items():
        val = row.get(course,'')
        if isinstance(val,str):
            up=val.upper()
            if up.startswith('CR'):
                registered+=cred
            elif up.startswith('NR'):
                remaining+=cred
            else:
                parts=val.split('|')
                if len(parts)==2:
                    rp=parts[1].strip()
                    try:
                        n=int(rp)
                        if n>0: completed+=cred
                        else: remaining+=cred
                    except:
                        if rp.upper()=='PASS':
                            pass
                        else:
                            remaining+=cred
                else:
                    remaining+=cred
        else:
            remaining+=cred
    return pd.Series([completed,registered,remaining,total],
                     index=['# of Credits Completed','# Registered','# Remaining','Total Credits'])

def save_report_with_formatting(displayed_df, intensive_df, timestamp):
    import io
    from openpyxl import Workbook
    from openpyxl.utils.dataframe import dataframe_to_rows
    from openpyxl.styles import PatternFill,Font,Alignment
    from config import cell_color
    output=io.BytesIO()
    wb=Workbook()
    ws=wb.active; ws.title="Required Courses"
    green=PatternFill('solid',start_color='90EE90',end_color='90EE90')
    pink=PatternFill('solid',start_color='FFC0CB',end_color='FFC0CB')
    yellow=PatternFill('solid',start_color='FFFACD',end_color='FFFACD')
    for i,row in enumerate(dataframe_to_rows(displayed_df,index=False,header=True),1):
        for j,val in enumerate(row,1):
            c=ws.cell(row=i,column=j,value=val)
            if i==1:
                c.font=Font(bold=True); c.alignment=Alignment('center','center')
            else:
                s=cell_color(str(val))
                if 'lightgreen' in s: c.fill=green
                elif '#FFFACD' in s: c.fill=yellow
                else: c.fill=pink
    ws2=wb.create_sheet("Intensive Courses")
    for i,row in enumerate(dataframe_to_rows(intensive_df,index=False,header=True),1):
        for j,val in enumerate(row,1):
            c=ws2.cell(row=i,column=j,value=val)
            if i==1:
                c.font=Font(bold=True); c.alignment=Alignment('center','center')
            else:
                s=cell_color(str(val))
                if 'lightgreen' in s: c.fill=green
                elif '#FFFACD' in s: c.fill=yellow
                else: c.fill=pink
    wb.save(output); output.seek(0)
    return output
