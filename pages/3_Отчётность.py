"""
Страница «Отчётность» · Коченевских бюро
Сводный ОПИУ: строки 96–119 из Google Sheets.
"""
import streamlit as st
import pandas as pd
import urllib.request

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
DARK_GREEN = "#315B3A"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

st.set_page_config(page_title="Отчётность · Коченевских", page_icon="◈", layout="wide")

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


st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: {WHITE}; }}
    h1 {{ color: {GRAPHITE}; font-weight: 600; font-size: 1.8rem; }}
    h2 {{ color: {GRAPHITE}; font-weight: 500; font-size: 1.2rem; }}
    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px; margin: 8px 0 24px 0;
    }}
    .report-table {{
        width: 100%; border-collapse: collapse; font-size: 0.85rem;
    }}
    .report-table thead th {{
        background: {ORANGE}; color: white; padding: 10px 14px;
        text-align: right; font-weight: 500; position: sticky; top: 0; z-index: 1;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    .report-table thead th:first-child {{
        background: {GRAPHITE}; text-align: left; min-width: 300px;
    }}
    .report-table td {{
        padding: 7px 14px; text-align: right;
    }}
    .report-table td:first-child {{ text-align: left; font-weight: 500; }}
    .report-table tbody tr:nth-child(even) td {{
        background: {WHITE};
    }}
    .report-table .green td {{
        background: #f6fbf0 !important;
    }}
    .report-table .section td {{
        font-weight: 700; font-size: 0.9rem; color: {GRAPHITE};
        border-top: 2px solid {ORANGE}; background: #fafafa !important;
    }}
    .report-table .highlight td {{
        background: {SKY} !important; font-weight: 500;
    }}
    .report-table .negative {{ color: {ORANGE}; }}
    .report-table .positive {{ color: #16a34a; }}
    .report-table .dim {{ color: #B8B8B8; }}
    .report-table td.pct-good {{ color: #16a34a; font-weight: 600; }}
    .report-table td.pct-low {{ color: {ORANGE}; font-weight: 600; }}
    .report-table.kpi-table td:first-child {{ white-space: nowrap; padding-right: 22px; }}
    .report-table tr.direction-profit td {{
        background: #f1f8ed !important;
        color: {GRAPHITE};
        font-weight: 700;
    }}
    .report-table tr.direction-profit td:first-child {{
        color: {DARK_GREEN};
        border-left: 3px solid {DARK_GREEN};
    }}
    .report-table tr.direction-profit td:last-child {{
        border-right: 3px solid {DARK_GREEN};
    }}
    .report-table tr.direction-profit-first td {{
        border-top: 3px solid {DARK_GREEN};
    }}
    .report-table tr.direction-profit-last td {{
        border-bottom: 3px solid {DARK_GREEN};
    }}
    .report-table tr.direction-profit-middle td {{
        border-top: none;
        border-bottom: none;
    }}
    .report-table tr.direction-profit td.negative {{
        color: {ORANGE};
    }}
</style>
""", unsafe_allow_html=True)

# ── Загрузка данных ─────────────────────────────────────────────
OPIU_URL = "https://docs.google.com/spreadsheets/d/1rXm66oriSs533ghAe4PNi6ze28P-lVPxVUJ63JOKcc0/export?format=csv"

@st.cache_data(ttl=600)
def load_opiu():
    with urllib.request.urlopen(OPIU_URL) as f:
        raw = pd.read_csv(f, header=None, dtype=str)
    section = raw.iloc[95:119].copy()
    section = section.reset_index(drop=True)
    return section


@st.cache_data(ttl=600)
def load_direction_profit():
    """Загружает три строки 31–33 исходного листа сразу после операционной прибыли."""
    with urllib.request.urlopen(OPIU_URL) as f:
        raw = pd.read_csv(f, header=None, dtype=str)

    operating_profit_row = -1
    for i in range(len(raw)):
        label = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
        if label.lower() == "операционная прибыль":
            operating_profit_row = i
            break

    if operating_profit_row < 0:
        return raw.iloc[0:0].copy()

    selected_rows = []
    for i in range(operating_profit_row + 1, min(operating_profit_row + 4, len(raw))):
        label = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
        if label:
            selected_rows.append(i)
        if len(selected_rows) == 3:
            break

    if len(selected_rows) != 3:
        return raw.iloc[0:0].copy()
    return raw.iloc[selected_rows].reset_index(drop=True)


@st.cache_data(ttl=600)
def load_kpi_rows():
    """Строки 122–124: KPI разработки и реализации по месяцам."""
    with urllib.request.urlopen(OPIU_URL) as f:
        raw = pd.read_csv(f, header=None, dtype=str)
    out = []
    for i in (121, 122, 123):
        if i >= len(raw):
            break
        label = str(raw.iloc[i, 0]).strip() if pd.notna(raw.iloc[i, 0]) else ""
        if not label:
            continue
        vals = []
        for j in range(1, raw.shape[1]):
            cellv = raw.iloc[i, j] if pd.notna(raw.iloc[i, j]) else ""
            vals.append(str(cellv).strip())
        out.append({"label": label, "values": vals})
    return out


def clean_number(s):
    if not isinstance(s, str):
        return 0
    s = s.replace("\u00A0", "").replace(" ", "").replace(",", ".").replace("%", "").strip()
    try:
        return int(float(s))
    except (ValueError, OverflowError):
        try:
            return float(s)
        except (ValueError, OverflowError):
            return 0


def fmt_rub(val):
    if val == 0:
        return "—"
    sign = ""
    if val < 0:
        sign = "−"
        val = abs(val)
    return f"{sign}{val:,.0f} ₽".replace(",", " ")


def fmt_pct(val):
    if isinstance(val, (int, float)):
        if val <= 1 and val >= -1:
            return f"{val*100:.0f}%"
        return f"{val:.0f}%"
    return str(val)


opiu = load_opiu()
direction_profit = load_direction_profit()

# ── Парсинг ─────────────────────────────────────────────────────
num_cols = len(opiu.columns) - 1
title = str(opiu.iloc[0, 0]).strip()

# Собираем: (месяц, год) для каждой колонки
col_info = []
for j in range(1, num_cols + 1):
    m = str(opiu.iloc[0, j]).strip() if pd.notna(opiu.iloc[0, j]) else ""
    y = str(opiu.iloc[1, j]).strip() if pd.notna(opiu.iloc[1, j]) else ""
    try:
        year_num = int(float(y))
    except (ValueError, OverflowError):
        year_num = None
    col_info.append({"month": m, "year": y, "year_num": year_num})

# Уникальные годы
years = sorted(set(
    ci["year_num"] for ci in col_info
    if ci["year_num"] is not None
), reverse=True)

# ── Заголовок ───────────────────────────────────────────────────
st.markdown(
    f'<h2 style="font-weight:300;color:#252525;">'
    f'<img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">'
    f'{title}</h2>',
    unsafe_allow_html=True
)
st.markdown('<p style="color:#999;font-size:0.8rem;">Коченевских бюро</p>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Выбор года ──────────────────────────────────────────────────
selected_year = st.selectbox("Год", years, key="year_selector")

# ── Фильтр месяцев ──────────────────────────────────────────────
month_options = []
for ci in col_info:
    if ci["month"] and not ci["month"].startswith(("итог", "1 кв", "2 кв", "3 кв", "4 кв")):
        if ci["year_num"] == selected_year or ci["year_num"] is None:
            month_options.append(ci["month"])

selected_months = st.multiselect(
    "Показать месяцы", month_options,
    default=month_options,
)

if not selected_months:
    st.info("Выбери хотя бы один месяц.")
    st.stop()

# Индексы выбранных месяцев в col_info
month_indices = [
    j for j, ci in enumerate(col_info)
    if ci["month"] in selected_months and (ci["year_num"] == selected_year or ci["year_num"] is None)
]

# ── Данные ──────────────────────────────────────────────────────
data_rows = []
for i in range(2, len(opiu)):
    label = str(opiu.iloc[i, 0]).strip() if pd.notna(opiu.iloc[i, 0]) else ""
    values = [clean_number(opiu.iloc[i, j + 1]) for j in range(num_cols)]
    data_rows.append({"label": label, "values": values})

# Три строки 31–33 из исходного листа вставляем сразу после операционной прибыли.
# Они находятся в другом блоке исходной таблицы, поэтому ищем их через
# отдельный загрузчик direction_profit, а не среди строк сводного ОПИУ 96–119.
direction_rows = []
for row_index in range(len(direction_profit)):
    direction_label = str(direction_profit.iloc[row_index, 0]).strip()
    if not direction_label:
        continue
    direction_values = [
        clean_number(direction_profit.iloc[row_index, j + 1])
        for j in range(num_cols)
    ]
    position = "first" if not direction_rows else "middle"
    direction_rows.append({
        "label": direction_label,
        "values": direction_values,
        "special_class": f"direction-profit direction-profit-{position}",
    })

if direction_rows:
    direction_rows[-1]["special_class"] = "direction-profit direction-profit-last"

rows_to_render = []
for row in data_rows:
    rows_to_render.append(row)
    if row["label"].strip().lower() == "операционная прибыль":
        rows_to_render.extend(direction_rows)

# ── Таблица ─────────────────────────────────────────────────────
st.markdown("### ▸ Сводный ОПИУ")
st.caption("Данные из Google Sheets")

html = '<div style="overflow-x: auto;"><table class="report-table"><thead><tr>'
html += '<th>Показатель</th>'
for m in selected_months:
    html += f'<th>{m}</th>'
html += '<th>Итого</th></tr></thead><tbody>'

for row in rows_to_render:
    label = row["label"]
    if not label:
        continue

    values = row["values"]
    total = sum(values[i] for i in month_indices)

    row_class = row.get("special_class", "")
    if not row_class:
        if label.startswith("ВЫРУЧКА") or label.startswith("СЕБЕСТОИМОСТЬ") or \
           label.startswith("Валовая") or label.startswith("Операционная") or \
           label.startswith("Расходы") or label.startswith("Прибыль") or \
           label.startswith("Чистая"):
            row_class = "section"
        elif label.startswith("Уровень") or label.startswith("Re "):
            row_class = "highlight"

        if label.startswith("FC расходы") or label.startswith("Переменные расходы") or \
           label.startswith("Перерасходы"):
            row_class = (row_class + " green").strip()

    html += f'<tr class="{row_class}">'
    html += f'<td>{label}</td>'

    for idx in month_indices:
        val = values[idx]
        if label.startswith("Re ") or label.startswith("Уровень"):
            html += f'<td>{fmt_pct(val)}</td>'
        else:
            html += f'<td class="{"negative" if val < 0 else ""}">{fmt_rub(val)}</td>'

    if label.startswith("Re ") or label.startswith("Уровень"):
        html += f'<td>—</td>'
    else:
        html += f'<td class="{"negative" if total < 0 else ""}" style="font-weight:600">{fmt_rub(total)}</td>'

    html += '</tr>'

html += '</tbody></table></div>'
st.markdown(html, unsafe_allow_html=True)

# ── KPI направлений (строки 122–124 листа) ──
kpi_rows = load_kpi_rows()
if kpi_rows:
    st.markdown("### ▸ KPI направлений")
    khtml = '<div style="overflow-x: auto;"><table class="report-table kpi-table"><thead><tr>'
    khtml += '<th>Направление</th>'
    for m in selected_months:
        khtml += f'<th>{m}</th>'
    khtml += '</tr></thead><tbody>'
    for row in kpi_rows:
        khtml += f'<tr><td>{row["label"]}</td>'
        for idx in month_indices:
            s = row["values"][idx] if idx < len(row["values"]) else ""
            if not s:
                khtml += '<td class="dim">—</td>'
                continue
            v = clean_number(s)
            cls = "pct-good" if v >= 80 else ("pct-low" if v < 40 else "")
            khtml += f'<td class="{cls}">{fmt_pct(v)}</td>'
        khtml += '</tr>'
    khtml += '</tbody></table></div>'
    st.markdown(khtml, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

