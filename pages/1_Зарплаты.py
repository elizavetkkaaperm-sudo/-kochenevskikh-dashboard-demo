import streamlit as st
import pandas as pd
import urllib.request
import csv
import io

st.set_page_config(page_title="Зарплаты · Коченевских", page_icon="◈", layout="wide")

# -- глазок видимости: скрывает цифры --
import os as _os
import sys as _sys
_root = _os.path.dirname(_os.path.abspath(__file__))
if not _os.path.exists(_os.path.join(_root, "privacy.py")):
    _root = _os.path.dirname(_root)
if _root not in _sys.path:
    _sys.path.insert(0, _root)
import privacy
privacy.arm()


# ── brand ────────────────────────────────────────────
ORANGE = "#F74028"
GRAPHITE = "#252525"
GRAY = "#E6E6E6"
WHITE = "#FFFFFF"
SKY = "#D0E2F7"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

# ── load employees ───────────────────────────────────
@st.cache_data(ttl=1800)
def load_employees():
    url = 'https://docs.google.com/spreadsheets/d/1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw/export?format=csv&gid=1378362572'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    employees = {}

    for row in rows:
        if len(row) >= 5:
            col_b = row[1].strip()
            col_c = row[2].strip()
            col_d = row[3].strip()
            col_e = row[4].strip()

            if col_c and col_c not in ['', 'сотрудники', 'статьи по котрым проходит их зп'] and col_b:
                emp_key = col_c.replace('\u00A0', ' ').strip()
                employees[emp_key] = {
                    'display': col_b,
                    'department': col_d,
                    'position': col_e
                }

    return employees


# ── load salary data ─────────────────────────────────
@st.cache_data(ttl=1800)
def load_salary_data(year=2026):
    url = 'https://docs.google.com/spreadsheets/d/1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw/export?format=csv&gid=0'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    def parse_num(s):
        s = s.strip().replace('\u00A0', ' ').replace('"', '')
        if not s or s == '' or s == '—':
            return 0.0
        s = s.replace(' ', '').replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return 0.0

    header_idx = None
    for i, row in enumerate(rows):
        if row and row[0].strip() == 'Месяц':
            header_idx = i
            break

    if header_idx is None:
        return pd.DataFrame()

    data_rows = []
    for row in rows[header_idx + 1:]:
        if len(row) >= 25 and row[24].strip() == str(year):
            month = row[0].strip()
            amount = abs(parse_num(row[3]))
            contractor = row[6].strip().replace('\u00A0', ' ')
            article = row[10].strip().replace('\u00A0', ' ')

            data_rows.append({
                'Месяц': month,
                'Дата': row[2].strip(),
                'Сумма': amount,
                'Контрагент': contractor,
                'Проект': row[7].strip().replace('\u00A0', ' '),
                'Назначение': row[9].strip().replace('\u00A0', ' '),
                'Статья': article
            })

    return pd.DataFrame(data_rows)


# ── data ─────────────────────────────────────────────
employees = load_employees()

salary_articles = [
    'Зарплата общепроизводственная',
    'Зарабатная плата административного состава',
    'Зарабатная плата комерческого персонала',
    'Зарабатная плата производственного состава',
    'Премии сотрудникам',
    'Процент комплектации за продажу товара',
    'з/п общепроизводственная',
    'з/п административного состава',
    'з/п коммерческого персонала',
    'з/п производственного состава',
]

month_order = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# ── UI ───────────────────────────────────────────────
st.markdown(f"""
<style>
    .stApp {{ background: {WHITE}; }}
    header {{ visibility: hidden; }}
    .metric-box {{
        background: {WHITE};
        border: 1px solid {GRAY};
        border-radius: 10px;
        padding: 1rem 1.3rem;
        text-align: center;
    }}
    .metric-val {{ font-size: 1.4rem; font-weight: 600; color: {GRAPHITE}; }}
    .metric-lbl {{ font-size: 0.7rem; color: #999; text-transform: uppercase; letter-spacing: 0.04em; }}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<h2 style="font-weight:300;color:#252525;"><img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">Зарплата сотрудников</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#999;font-size:0.8rem;">Коченевских бюро</p>', unsafe_allow_html=True)

year = st.selectbox('Год', [2026, 2025, 2024, 2023], key='year_selector')

df_all = load_salary_data(year)

if df_all.empty or 'Статья' not in df_all.columns:
    st.warning(f'Нет данных за {year} год')
    st.stop()

df_salary = df_all[
    df_all['Статья'].isin(salary_articles) &
    df_all['Контрагент'].isin(employees.keys())
].copy()

df_salary['Имя'] = df_salary['Контрагент'].map(lambda x: employees.get(x, {}).get('display', x))
df_salary['Отдел'] = df_salary['Контрагент'].map(lambda x: employees.get(x, {}).get('department', ''))
df_salary['Должность'] = df_salary['Контрагент'].map(lambda x: employees.get(x, {}).get('position', ''))

# ── summary metrics ──────────────────────────────────
total_fot = df_salary['Сумма'].sum()
unique_employees = df_salary['Имя'].nunique()
total_employees = len(employees)
months_count = df_salary['Месяц'].nunique()
avg_monthly = total_fot / months_count / unique_employees if months_count > 0 and unique_employees > 0 else 0

top_emp = df_salary.groupby('Имя')['Сумма'].sum().sort_values(ascending=False)
top_name = top_emp.index[0] if len(top_emp) > 0 else '—'
top_amount = top_emp.iloc[0] if len(top_emp) > 0 else 0


def fmt(v):
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.1f} млн ₽".replace('.', ',')
    return f"{int(v):,} ₽".replace(',', ' ')


c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{fmt(total_fot)}</div><div class="metric-lbl">ФОТ за {year} год</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{unique_employees}</div><div class="metric-lbl">Сотрудников · из {total_employees} в штате</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{fmt(avg_monthly)}</div><div class="metric-lbl">Средняя з/п в месяц</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-box"><div class="metric-val">{fmt(top_amount)}</div><div class="metric-lbl">Крупнейшая · {top_name}</div></div>', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# ── main table: employees × months ──────────────────
st.markdown('<p style="font-weight:500;color:#252525;">▸ Начисления по месяцам</p>', unsafe_allow_html=True)

pivot = df_salary.pivot_table(
    values='Сумма',
    index=['Имя', 'Отдел', 'Должность'],
    columns='Месяц',
    aggfunc='sum',
    fill_value=0
)

available_months = [m for m in month_order if m in pivot.columns]
pivot = pivot[available_months]
pivot['Итого'] = pivot.sum(axis=1)
pivot = pivot.sort_values('Итого', ascending=False)

# ── фильтры ──────────────────────────────────────────
dept_list = sorted(set(str(x) for x in pivot.reset_index()['Отдел'].dropna().unique()))
pos_list = sorted(set(str(x) for x in pivot.reset_index()['Должность'].dropna().unique()))

fc1, fc2 = st.columns(2)
with fc1:
    sel_dept = st.multiselect("Отдел", dept_list)
with fc2:
    sel_pos = st.multiselect("Должность", pos_list)

# ── применяем фильтры ────────────────────────────────
df_work = pivot.copy()
if sel_dept:
    idx_names = df_work.index.get_level_values('Отдел')
    df_work = df_work[idx_names.isin(sel_dept)]
if sel_pos:
    idx_names = df_work.index.get_level_values('Должность')
    df_work = df_work[idx_names.isin(sel_pos)]

# ── итоговая строка (числа) ──────────────────────────
totals = {}
for col in df_work.columns:
    totals[col] = df_work[col].sum()
totals_row = pd.Series(totals, name='ИТОГО')

# ── форматированная таблица для отображения ──────────
def fmt_table(v):
    if v == 0:
        return '—'
    return f"{int(v):,} ₽".replace(',', ' ')

df_display = df_work.copy()
for col in df_display.columns:
    df_display[col] = df_display[col].apply(fmt_table)

df_display = df_display.reset_index()
df_display = df_display.rename(columns={'Имя': 'Сотрудник'})
display_cols = ['Сотрудник', 'Должность', 'Отдел'] + available_months + ['Итого']
df_display = df_display[display_cols]

st.dataframe(df_display, use_container_width=True, hide_index=True)

# ── итоговая строка (голубая полоса) ────────────────
if len(df_work) > 0:
    total_html = '<div style="background:{SKY}; border-radius:10px; padding:0.7rem 1.5rem; margin-top:0.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">'
    total_html += '<span style="font-weight:600; color:{GRAPHITE}; font-size:0.85rem;">ИТОГО</span>'

    # показываем только месяцы с ненулевыми суммами и Итого
    for col in available_months:
        v = totals_row[col]
        if v > 0:
            total_html += f'<span style="color:{GRAPHITE}; font-size:0.8rem;">{col}: <strong>{fmt(v)}</strong></span>'

    total_html += f'<span style="color:{GRAPHITE}; font-size:0.9rem; font-weight:700;">Всего: {fmt(totals_row["Итого"])}</span>'
    total_html += '</div>'
    st.markdown(total_html.format(SKY=SKY, GRAPHITE=GRAPHITE), unsafe_allow_html=True)
    st.caption(f'Показано {len(df_work)} сотрудников из {len(pivot)}')

st.caption(f'Данные из ДДС по ЗП · {year} год · обновлено автоматически')
