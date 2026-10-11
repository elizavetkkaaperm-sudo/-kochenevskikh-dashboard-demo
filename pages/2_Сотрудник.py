"""
Страница «Сотрудник» · Коченевских бюро
Детальный график зарплаты по месяцам с расшифровкой по статьям.
"""
import streamlit as st
import pandas as pd
import urllib.request
import csv
import io

# ── Авторизация ─────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице.")
    st.stop()

# ── Брендовые цвета ─────────────────────────────────────────────
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

st.set_page_config(page_title="Сотрудник · Коченевских", page_icon="◈", layout="wide")

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


# ── CSS (полный, как на листе Зарплаты) ─────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: {WHITE}; }}
    h1 {{ color: {GRAPHITE}; font-weight: 600; font-size: 1.8rem; }}
    h2 {{ color: {GRAPHITE}; font-weight: 500; font-size: 1.2rem; }}
    h3 {{ color: {GRAPHITE}; font-weight: 400; font-size: 1rem; }}
    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px; margin: 8px 0 24px 0;
    }}
    .metric-card {{
        background: {WHITE}; border: 1px solid {GREY};
        border-radius: 12px; padding: 24px; text-align: center;
    }}
    .metric-value {{ font-size: 2rem; font-weight: 700; color: {GRAPHITE}; }}
    .metric-label {{ font-size: 0.85rem; color: #888; margin-top: 4px; }}
    .total-row td {{
        font-weight: 700 !important;
        font-size: 1.1em !important;
        border-top: 2px solid {GRAPHITE} !important;
    }}
    /* Таблица расшифровки */
    .article-table {{ width: 100%; border-collapse: collapse; }}
    .article-table th {{
        background: {GRAPHITE}; color: white;
        padding: 8px 12px; text-align: left;
    }}
    .article-table th:not(:first-child) {{ text-align: right; }}
    .article-table td {{ padding: 6px 12px; }}
    .article-table td:not(:first-child) {{ text-align: right; }}
    .article-table tbody tr:nth-child(even) {{ background: #fafafa; }}
</style>
""", unsafe_allow_html=True)

# ── Месяцы ──────────────────────────────────────────────────────
MONTH_ORDER = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]

# ── Загрузка: список сотрудников + статьи ───────────────────────
@st.cache_data(ttl=1800)
def load_employees_and_articles():
    req = urllib.request.Request(EMPLOYEE_URL := 
        f"https://docs.google.com/spreadsheets/d/1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw/export?format=csv&gid=1378362572")
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    employees = {}
    for row in rows:
        if len(row) >= 5:
            col_b = row[1].strip()   # красивое имя
            col_c = row[2].strip()   # имя из ДДС (для сопоставления)
            col_d = row[3].strip()   # отдел
            if col_c and col_c not in ['', 'сотрудники', 'статьи по котрым проходит их зп'] and col_b:
                employees[col_c] = col_b

    articles = []
    for i in range(25, min(35, len(rows))):
        val = rows[i][3].strip() if len(rows[i]) > 3 else ""
        if val:
            articles.append(val)

    return employees, articles

# ── Загрузка: ДДС по ЗП (все годы) ──────────────────────────────
@st.cache_data(ttl=600)
def load_dds():
    req = urllib.request.Request(
        "https://docs.google.com/spreadsheets/d/1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw/export?format=csv&gid=0")
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    # Ищем строку-заголовок «Месяц»
    header_idx = None
    for i, row in enumerate(rows):
        if row and row[0].strip() == "Месяц":
            header_idx = i
            break

    if header_idx is None:
        return pd.DataFrame()

    headers = [h.strip() for h in rows[header_idx]]

    data_rows = []
    for row in rows[header_idx + 1:]:
        if len(row) < 25:
            continue
        data_rows.append(row)

    df = pd.DataFrame(data_rows, columns=headers)

    # Парсим сумму
    def parse_num(s):
        if not isinstance(s, str):
            return 0.0
        s = s.strip().replace('\u00A0', ' ').replace('"', '')
        if not s or s in ('', '—'):
            return 0.0
        s = s.replace(' ', '').replace(',', '.')
        try:
            return abs(float(s))
        except ValueError:
            return 0.0

    df["Сумма_число"] = df["Сумма"].apply(parse_num)
    return df


employees, salary_articles = load_employees_and_articles()
dds = load_dds()

if dds.empty:
    st.error("Не удалось загрузить данные ДДС.")
    st.stop()

# Годы
available_years = sorted(
    dds[dds.columns[24]].dropna().unique() if len(dds.columns) > 24 else [],
    reverse=True
)
if not available_years:
    # fallback: колонка «год» может быть под другим индексом
    year_col = None
    for col in dds.columns:
        if 'год' in str(col).lower():
            year_col = col
            break
    if year_col:
        available_years = sorted(dds[year_col].dropna().unique(), reverse=True)
    else:
        available_years = ["2026", "2025", "2024", "2023"]

# ── Заголовок ───────────────────────────────────────────────────
st.markdown(f'<h2 style="font-weight:300;color:#252525;"><img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">Зарплата сотрудника</h2>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    display_names = sorted(employees.values())
    selected_display = st.selectbox("Сотрудник", display_names)
    # Обратный поиск ключа
    selected_key = None
    for k, v in employees.items():
        if v == selected_display:
            selected_key = k
            break
with col2:
    year = st.selectbox("Год", available_years, index=0)

if selected_key is None:
    st.warning("Сотрудник не найден")
    st.stop()

# ── Фильтрация ──────────────────────────────────────────────────
year_col = None
for col in dds.columns:
    if 'год' in str(col).lower():
        year_col = col
        break

emp_data = dds[
    (dds["Контрагент"] == selected_key) &
    (dds["Статья"].isin(salary_articles))
].copy()

if year_col:
    emp_data = emp_data[emp_data[year_col] == str(year)]

if emp_data.empty:
    st.info(f"За {year} год данных по сотруднику {selected_display} нет.")
    st.stop()

# ── График: месяцы по порядку (categorical) ─────────────────────
monthly = emp_data.groupby("Месяц")["Сумма_число"].sum().reset_index()
monthly["Месяц_cat"] = pd.Categorical(monthly["Месяц"], categories=MONTH_ORDER, ordered=True)
monthly = monthly.dropna(subset=["Месяц_cat"]).sort_values("Месяц_cat")

st.markdown(f"### ▸ {selected_display} · {year}")
st.caption("Суммарные начисления по месяцам")

chart_df = monthly.set_index("Месяц_cat")[["Сумма_число"]]
chart_df.index.name = "Месяц"
st.bar_chart(chart_df, color=ORANGE)

# ── Сводные цифры ───────────────────────────────────────────────
total = emp_data["Сумма_число"].sum()
months_count = monthly["Месяц_cat"].nunique()
avg = total / months_count if months_count > 0 else 0
best_idx = monthly["Сумма_число"].idxmax()
best_month = monthly.loc[best_idx, "Месяц"]
best_amount = monthly.loc[best_idx, "Сумма_число"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего за год", f"{total:,.0f} ₽".replace(",", " "))
col2.metric("В среднем в месяц", f"{avg:,.0f} ₽".replace(",", " "))
col3.metric("Месяцев с начислениями", months_count)
col4.metric(f"Лучший месяц — {best_month}", f"{best_amount:,.0f} ₽".replace(",", " "))

st.markdown("<br>", unsafe_allow_html=True)

# ── Расшифровка по статьям (TOTAL — жирный, крупнее) ───────────
st.markdown("### ▸ Расшифровка по статьям")

def clean_article(name):
    name = str(name).strip()
    name = name.replace("Зарабатная", "Заработная")
    name = name.replace("Зарплата", "з/п")
    name = name.replace("Заработная плата", "з/п")
    name = name.replace("комерческого", "коммерческого")
    return name

emp_data["Статья_чист"] = emp_data["Статья"].apply(clean_article)

article_pivot = emp_data.pivot_table(
    values="Сумма_число", index="Статья_чист", columns="Месяц",
    aggfunc="sum", fill_value=0,
)
existing_months = [m for m in MONTH_ORDER if m in article_pivot.columns]
article_pivot = article_pivot[existing_months]
article_pivot["Итого"] = article_pivot.sum(axis=1)
article_pivot = article_pivot.sort_values("Итого", ascending=False)

# Строка ВСЕГО
totals = article_pivot.sum(axis=0)
totals.name = "ВСЕГО"

# Строим HTML-таблицу (TOTAL — жирный + крупнее)
def fmt_rub(v):
    if v == 0:
        return "—"
    return f"{v:,.0f} ₽".replace(",", " ")

all_columns = existing_months + ["Итого"]

html = '<table class="article-table"><thead><tr><th>Статья</th>'
for m in all_columns:
    html += f"<th>{m}</th>"
html += "</tr></thead><tbody>"

# Данные
for idx, row in article_pivot.iterrows():
    html += "<tr>"
    html += f"<td>{idx}</td>"
    for col in all_columns:
        html += f"<td>{fmt_rub(row[col])}</td>"
    html += "</tr>"

# Строка ВСЕГО
html += '<tr class="total-row">'
html += "<td>ВСЕГО</td>"
for col in all_columns:
    html += f"<td>{fmt_rub(totals[col])}</td>"
html += "</tr>"

html += "</tbody></table>"
st.markdown(html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Расшифровка по годам (средняя в месяц) ──────────────────────
all_emp = dds[
    (dds["Контрагент"] == selected_key) &
    (dds["Статья"].isin(salary_articles))
].copy()

if not all_emp.empty and year_col:
    # Определяем список годов для таблицы (2023, 2024, 2025)
    all_emp["год_int"] = pd.to_numeric(all_emp[year_col], errors="coerce")
    history_years = sorted(all_emp["год_int"].dropna().unique())
    # Оставляем только реальные года (не текущий, если хотим)
    target_years = [y for y in [2023, 2024, 2025] if y in history_years]

    if target_years:
        st.markdown("### ▸ Расшифровка по годам")
        st.caption("Средняя зарплата в месяц")

        yearly_rows = []
        for y in target_years:
            y_data = all_emp[all_emp["год_int"] == y]
            if y_data.empty:
                continue
            total_y = y_data["Сумма_число"].sum()
            months_y = y_data["Месяц"].nunique()
            avg_y = total_y / months_y if months_y > 0 else 0
            yearly_rows.append({
                "Год": str(y),
                "Всего за год": fmt_rub(total_y),
                "В среднем в месяц": fmt_rub(avg_y),
            })

        if yearly_rows:
            # Табличка
            yr_html = '<table style="width:auto; border-collapse:collapse; margin-bottom:16px;">'
            yr_html += '<thead><tr style="background:#252525;color:white;">'
            yr_html += '<th style="padding:8px 16px;text-align:left;">Год</th>'
            yr_html += '<th style="padding:8px 16px;text-align:right;">Всего за год</th>'
            yr_html += '<th style="padding:8px 16px;text-align:right;">В среднем в месяц</th>'
            yr_html += '</tr></thead><tbody>'
            for i, r in enumerate(yearly_rows):
                bg = '#fafafa' if i % 2 == 0 else 'white'
                yr_html += f'<tr style="background:{bg};"><td style="padding:6px 16px;">{r["Год"]}</td>'
                yr_html += f'<td style="padding:6px 16px;text-align:right;">{r["Всего за год"]}</td>'
                yr_html += f'<td style="padding:6px 16px;text-align:right;">{r["В среднем в месяц"]}</td></tr>'
            yr_html += '</tbody></table>'
            st.markdown(yr_html, unsafe_allow_html=True)

# ── Год устройства ──────────────────────────────────────────────
all_emp_for_date = dds[
    (dds["Контрагент"] == selected_key) &
    (dds["Статья"].isin(salary_articles))
].copy()

if not all_emp_for_date.empty:
    all_emp_for_date["Дата_dt"] = pd.to_datetime(
        all_emp_for_date["Дата"], format="%d.%m.%Y", errors="coerce"
    )
    first_date = all_emp_for_date["Дата_dt"].min()
    if pd.notna(first_date):
        hire_year = int(first_date.year)
    else:
        hire_year = "—"
else:
    hire_year = "—"

maybe_earlier = " (возможно ранее)" if isinstance(hire_year, int) and hire_year <= 2023 else ""
st.markdown(f"**Год устройства:** {hire_year}{maybe_earlier}")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Данные из Google Sheets · обновляются автоматически · Neo AI Dashboard")
