import streamlit as st
import urllib.request
import urllib.parse
import json
import os
import html as html_lib
from datetime import datetime

st.set_page_config(
    page_title="Планы · Коченевских",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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



# ── brand ──
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GRAY = "#E6E6E6"
WHITE = "#FFFFFF"
SUCCESS = "#2E7D32"
WARNING = "#E65100"
CURRENT_ORANGE = "#FF7A00"

# ── css ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', -apple-system, sans-serif !important; }}
    .stApp {{ background: {WHITE}; }}
    #MainMenu {{ visibility: hidden; }}
    /* Не скрываем шапку Streamlit: на телефоне через неё открывается меню страниц. */
    header {{ visibility: visible !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    
    .hero-title {{
        font-size: 2.4rem; font-weight: 300; color: {GRAPHITE};
        letter-spacing: -0.02em; margin-bottom: 0.2rem;
    }}
    .hero-subtitle {{
        font-size: 0.85rem; font-weight: 400; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase;
    }}
    .section-line {{ height: 1px; background: {GRAY}; margin: 1.8rem 0; }}
    
    .metric-card {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 12px; padding: 1.4rem 1.6rem;
    }}
    .metric-value {{
        font-size: 2rem; font-weight: 600; color: {GRAPHITE};
        letter-spacing: -0.02em; line-height: 1.1;
    }}
    .metric-value.danger {{ color: {ORANGE}; }}
    .metric-value.ok {{ color: {SUCCESS}; }}
    .metric-label {{
        font-size: 0.8rem; font-weight: 500; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase; margin-top: 0.3rem;
    }}
    
    .plan-table {{
        width: 100%; border-collapse: collapse; font-size: 0.82rem;
        margin-top: 1rem;
    }}
    .plan-table th {{
        background: #FAFAFA; color: #666; font-weight: 500;
        font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.04em;
        padding: 0.6rem 0.5rem; border-bottom: 2px solid {GRAY};
        text-align: left; white-space: nowrap;
    }}
    .plan-table thead tr.group-row th {{
        background: {GRAPHITE}; color: {WHITE};
        border-bottom: 0; text-align: center; font-size: 0.72rem;
        letter-spacing: 0.05em; padding: 0.55rem 0.5rem;
    }}
    .profit-cell {{
        background: {MINT} !important; font-weight: 600;
        border-radius: 3px;
    }}
    .money-group-left, .profit-group-left {{
        border-left: 2.5px solid #999 !important;
    }}
    .money-group-right, .profit-group-right {{
        border-right: 2.5px solid #999 !important;
    }}
    .stage-left {{
        border-left: 2.5px solid #999 !important;
    }}
    .stage-right {{
        border-right: 2.5px solid #999 !important;
    }}
    .plan-table td {{
        padding: 0.5rem; border-bottom: 1px solid {GRAY};
        color: {GRAPHITE}; vertical-align: middle;
    }}
    .project-name {{
        font-weight: 700 !important;
    }}
    .plan-table tr:hover {{ background: #FAFAFA; }}
    
    .highlight {{
        background: {MINT} !important; font-weight: 600;
        border-radius: 3px;
    }}
    .highlight-orange {{
        background: #FFF0EB !important; font-weight: 600;
        border-radius: 3px;
    }}
    .current-month-cell {{
        box-shadow: inset 0 0 0 2px {CURRENT_ORANGE} !important;
        border-radius: 3px;
    }}
    .shifted-month-cell {{
        box-shadow: inset 0 0 0 2px {ORANGE} !important;
        border-radius: 3px;
    }}
    .current-month-summary {{
        box-shadow: inset 0 0 0 2px {CURRENT_ORANGE};
        border-radius: 8px;
        padding: 5px 7px 3px;
        margin: -5px -7px 0.6rem;
    }}
    .bar-value {{
        cursor: help;
        border-bottom: 1px dotted currentColor;
    }}
    .bar-legend {{
        display: flex; gap: 0.9rem; flex-wrap: wrap;
        font-size: 0.7rem; color: #999; margin-top: 0.7rem;
    }}
    .bar-legend-item {{ display: inline-flex; align-items: center; gap: 0.3rem; }}
    .bar-legend-dot {{ width: 9px; height: 9px; border-radius: 2px; display: inline-block; }}
    .bar-tooltip {{ position: relative; }}
    .bar-tooltip .bar-tooltip-text {{
        visibility: hidden; opacity: 0; position: absolute; z-index: 10;
        left: 0; top: 1.5rem; width: 300px; padding: 0.7rem 0.8rem;
        background: {GRAPHITE}; color: {WHITE}; border-radius: 8px;
        font-size: 0.78rem; font-weight: 400; line-height: 1.55;
        white-space: normal; text-align: left; transition: opacity 0.15s;
        box-shadow: 0 3px 12px rgba(0,0,0,0.16);
        pointer-events: none;
    }}
    .bar-tooltip:hover .bar-tooltip-text {{ visibility: visible; opacity: 1; }}
    
    .month-selector {{
        display: flex; gap: 0.3rem; flex-wrap: wrap; margin: 1rem 0;
    }}
    .month-btn {{
        padding: 0.4rem 0.8rem; border-radius: 8px; border: 1px solid {GRAY};
        background: {WHITE}; color: {GRAPHITE}; cursor: pointer;
        font-size: 0.8rem; font-weight: 500; transition: all 0.15s;
    }}
    .month-btn.active {{
        background: {GRAPHITE}; color: {WHITE}; border-color: {GRAPHITE};
    }}
    
    .breakeven-line {{
        display: inline-block; background: #FFF5F5; border: 1px solid #FFD6D6;
        border-radius: 8px; padding: 0.4rem 1rem; font-size: 0.8rem;
        color: {ORANGE}; font-weight: 600; margin-left: 1rem;
    }}
    
    .summary-row {{
        font-weight: 600; background: #FAFAFA;
    }}
    .below-target td {{ color: {ORANGE} !important; }}
</style>
""", unsafe_allow_html=True)

# ── logo + title ──
st.markdown(f"""
<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.2rem;">
    <img src="https://optim.tildacdn.com/tild3538-3366-4836-a666-313132343465/-/resize/138x/-/format/webp/Group_417.png.webp" style="height:28px;width:auto;" alt="Kochenevskikh">
    <span class="hero-title">Планы по проектам</span>
</div>
<div class="hero-subtitle">Разработка · плановая выручка по месяцам</div>
""", unsafe_allow_html=True)

# ── data loading ──
def _get_google_token():
    """Refresh and return Google OAuth access token."""
    try:
        client_id = st.secrets["google_client_id"]
        client_secret = st.secrets["google_client_secret"]
        refresh_token = st.secrets["google_refresh_token"]
    except Exception:
        secret_path = os.path.expanduser("/opt/data/google_client_secret.json")
        token_path = os.path.expanduser("/opt/data/google_token.json")
        if not os.path.exists(secret_path) or not os.path.exists(token_path):
            return None
        with open(secret_path) as f:
            secret = json.load(f)
        client_id = secret['installed']['client_id']
        client_secret = secret['installed']['client_secret']
        with open(token_path) as f:
            token_data = json.load(f)
        refresh_token = token_data['refresh_token']

    token_url = 'https://oauth2.googleapis.com/token'
    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(token_url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            tokens = json.loads(resp.read())
        return tokens['access_token']
    except Exception:
        return None

SHEET_ID = '14iQhX1TKJWRnS0W6OCvG8tYVpqMeSGK3hD95T3BdajY'
SHEET_NAME = 'разработка (РАБОЧИЙ)'

@st.cache_data(ttl=300)
def load_sheet_data():
    access_token = _get_google_token()
    if access_token is None:
        st.error("Нет доступа к Google. Проверьте настройки secrets на Streamlit Cloud.")
        return None, None, None, None

    encoded = urllib.parse.quote(SHEET_NAME)
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    try:
        data = json.loads(urllib.request.urlopen(req).read())
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None, None, None, None
    values = data.get('values', [])

    # Find boundaries
    start_row = None
    end_row = None
    for i, row in enumerate(values):
        row_str = ' '.join([str(c) for c in row if c])
        if 'ПЛАНЫ ПО ТЕКУЩИМ ПРОЕКТАМ' in row_str:
            start_row = i
        if start_row is not None and 'РЕСУРСЫ КОМАНДЫ' in row_str:
            end_row = i
            break

    if start_row is None or end_row is None:
        st.error("Не удалось найти границы данных в таблице.")
        return None, None, None

    # Extract current month from row 6 (0-indexed = 5)
    month_row = values[5] if len(values) > 5 else []
    current_month = 8
    for cell in month_row:
        try:
            val = int(str(cell).strip())
            if 1 <= val <= 12:
                current_month = val
                break
        except:
            pass

    return values, start_row, end_row, current_month

values, start_row, end_row, current_month = load_sheet_data()

if values is None:
    st.stop()

# ── month selector ──
month_names = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

selected_month = st.selectbox(
    "Показать планы на месяц",
    list(month_names.keys()),
    format_func=lambda m: month_names[m],
    index=max(0, min(current_month - 1, 11)),
    key="month_select"
)

# ── parse projects ──
def parse_amount(s):
    """Parse amount like '140 000' or '140\\xa0000'"""
    if s is None:
        return 0
    s = str(s).replace('\xa0', ' ').replace(' ', '').replace(',', '.').strip()
    try:
        return int(float(s))
    except:
        return 0

def fmt(n):
    if n == 0:
        return "—"
    return f"{n:,.0f}".replace(",", " ")

# В месячных итогах используются те же столбцы, что и в формуле Google-таблицы:
# 1-4 этапа и постоплата. Колонка 5 этапа показывается в строке проекта,
# но в сводный план месяца не входит.
PLAN_INDICES = (0, 1, 2, 3, 5)

# Extract project rows (from start_row + 8 to before summary section)
projects = []
header_row = None

# Find header row
for i in range(start_row, end_row):
    row = values[i] if i < len(values) else []
    row_str = ' '.join([str(c) for c in row if c])
    if 'Проект' in row_str and 'Заказчик' in row_str:
        header_row = i
        break

# Find first project row after header
first_project = None
for i in range(header_row + 1, end_row):
    row = values[i] if i < len(values) else []
    row_str = ' '.join([str(c) for c in row if c])
    if 'ИТОГО' in row_str:
        first_project = i
        break

# Parse projects from header+2 to the summary section
summary_row = None
for i in range(start_row, end_row):
    row = values[i] if i < len(values) else []
    row_str = ' '.join([str(c) for c in row if c])
    if 'ИТОГО В ПЛАНАХ' in row_str:
        summary_row = i
        break

# Parse projects
projects = []
for i in range(header_row + 2, summary_row if summary_row else end_row):
    row = values[i] if i < len(values) else []
    # Check if row has meaningful data in cols 1-2 (project + client)
    has_data = False
    for j in range(1, min(4, len(row))):
        if row[j] and str(row[j]).strip():
            has_data = True
            break
    if not has_data:
        continue

    name = str(row[1]).strip() if len(row) > 1 and row[1] else (str(row[0]).strip() if row and row[0] else "")
    client = str(row[2]).strip() if len(row) > 2 and row[2] else ""
    contract = str(row[3]).strip() if len(row) > 3 and row[3] and any(c.isdigit() for c in str(row[3])) else ""
    # Designer: col 8 (0-indexed), or find a name-like field (no digits, >3 chars)
    designer = ""
    if len(row) > 8 and row[8] and not any(c.isdigit() for c in str(row[8])):
        designer = str(row[8]).strip()
    else:
        for j in range(4, min(20, len(row))):
            val = str(row[j]).strip() if row[j] else ""
            if val and len(val) > 5 and not any(c.isdigit() for c in val):
                designer = val
                break

    if not name:
        continue
    # If designer not found, show as unassigned — don't lose the project
    if not designer:
        designer = "Не назначен"

    # Фиксированные группы листа: T:X - месяцы, Y:AD - ВР, AJ:AO - прибыль.
    months = [parse_amount(row[j]) if j < len(row) else 0 for j in range(19, 24)]
    revenues = [parse_amount(row[j]) if j < len(row) else 0 for j in range(24, 30)]
    profits = [parse_amount(row[j]) if j < len(row) else 0 for j in range(35, 41)]
    # AP:AU - отметки по оплатам тех же этапов.
    # Пустая ячейка означает, что этап уже оплачен.
    # Заполненная ячейка означает, что оплата ещё ожидается.
    payment_pending = [
        bool(str(row[j]).strip()) if j < len(row) else False
        for j in range(41, 47)
    ]
    # AE:AH - актуальные месяцы первых четырёх этапов.
    # AI - служебный итог проекта, поэтому в этапы его не включаем.
    current_stage_markers = [parse_amount(row[j]) if j < len(row) else 0 for j in range(30, 34)]

    if any(months) or any(revenues) or any(profits):
        projects.append({
            'name': name,
            'client': client,
            'contract': contract,
            'designer': designer,
            'months': months,
            'revenues': revenues,
            'profits': profits,
            'payment_pending': payment_pending,
            'current_stage_markers': current_stage_markers
        })

# ── find monthly totals from the source sheet ──
source_monthly_totals = {}
for i in range(start_row, end_row):
    row = values[i] if i < len(values) else []
    if len(row) >= 3:
        try:
            m = int(str(row[0]).strip())
            if 1 <= m <= 12:
                total = parse_amount(row[2]) if len(row) > 2 else 0
                source_monthly_totals[m] = total
        except:
            pass


def stage_month(project, idx):
    """Возвращает месяц этапа. Постоплата относится к последнему заполненному этапу."""
    if idx < len(project['months']) and project['months'][idx]:
        return project['months'][idx]
    if idx == 5:
        for month in reversed(project['months']):
            if month:
                return month
    return 0


def actual_stage_month(project, idx):
    """Возвращает текущий месяц этапа из AE:AH.

    Пустая отметка означает, что перенос для этапа не задан. AI не читаем,
    потому что это служебный итог проекта, а не месяц шестого этапа.
    """
    months = project.get('months', [])
    markers = project.get('current_stage_markers', [])
    if idx < 4:
        actual_month = markers[idx] if idx < len(markers) else 0
        return actual_month or (months[idx] if idx < len(months) else 0)
    if idx == 4:
        return months[4] if len(months) >= 5 else 0
    if idx == 5 and len(months) >= 5:
        return months[4]
    return 0


def displayed_stage_month(project, idx):
    """Возвращает базовый месяц суммы из T:X.

    Месячные планы и ответственность на странице всегда собираются по
    исходным месяцам T:X. AE:AH используются только для примечаний о том,
    откуда этап был перенесён в текущем плане.
    """
    return project_base_month(project, idx)


def project_base_month(project, idx):
    """Возвращает месяц исходного плана для этапа или постоплаты."""
    months = project.get('months', [])
    if idx < 5:
        return months[idx] if idx < len(months) else 0
    if idx == 5 and len(months) >= 5:
        return months[4]
    return 0


def is_shifted_stage(project, idx):
    """Проверяет изменение месяца в актуальном плане AE:AI."""
    markers = project.get('current_stage_markers', [])
    if idx >= 4 or idx >= len(project['months']) or idx >= len(markers):
        return False
    actual_month = markers[idx]
    planned_month = project['months'][idx]
    return bool(actual_month) and actual_month != planned_month


def transfer_note(project, idx, amount, kind):
    """Возвращает расшифровку переноса для tooltip конкретной ячейки."""
    if not amount or idx >= 4 or not is_shifted_stage(project, idx):
        return ""
    source_month = actual_stage_month(project, idx)
    target_month = project_base_month(project, idx)
    label = "выручка" if kind == "revenue" else "прибыль"
    return f"{label}: {fmt(amount)} ₽, из {month_names.get(source_month, source_month)} в {month_names.get(target_month, target_month)}"


# Своды считаем только по исходным месяцам T:X.
# AE:AH не двигают сумму между строками графика. Они дают примечание,
# в какой базовый месяц T:X добавлен перенос из текущего плана AE:AH.
monthly_totals = {}
revenue_transferred_by_target = {}
revenue_transferred_by_source = {}
for project in projects:
    for idx in PLAN_INDICES:
        amount = project['revenues'][idx] if idx < len(project['revenues']) else 0
        base_month = project_base_month(project, idx)
        if base_month and amount:
            monthly_totals[base_month] = monthly_totals.get(base_month, 0) + amount
        if idx < 4 and is_shifted_stage(project, idx) and amount:
            source_month = actual_stage_month(project, idx)
            target_month = base_month
            if source_month and target_month:
                incoming_bucket = revenue_transferred_by_target.setdefault(target_month, {})
                outgoing_bucket = revenue_transferred_by_source.setdefault(source_month, {})
                incoming_bucket[source_month] = incoming_bucket.get(source_month, 0) + amount
                outgoing_bucket[target_month] = outgoing_bucket.get(target_month, 0) + amount

# Для прибыли используется та же логика: итог месяца из T:X,
# а AE:AH только расшифровывают перенос.
monthly_profit_totals = {}
profit_transferred_by_target = {}
profit_transferred_by_source = {}
monthly_profit_unreceived = {}
for project in projects:
    for idx in PLAN_INDICES:
        profit = project['profits'][idx] if idx < len(project['profits']) else 0
        payment_flags = project.get('payment_pending', [False] * 6)
        payment_is_pending = payment_flags[idx] if idx < len(payment_flags) else False
        base_month = project_base_month(project, idx)
        if base_month and profit:
            monthly_profit_totals[base_month] = monthly_profit_totals.get(base_month, 0) + profit
            # Заполненная AP:AU означает, что деньги по этапу ещё не получены.
            # Пустая AP:AU означает, что этап уже оплачен.
            if payment_is_pending:
                monthly_profit_unreceived[base_month] = monthly_profit_unreceived.get(base_month, 0) + profit
        if idx < 4 and is_shifted_stage(project, idx) and profit:
            source_month = actual_stage_month(project, idx)
            target_month = base_month
            if source_month and target_month:
                incoming_bucket = profit_transferred_by_target.setdefault(target_month, {})
                outgoing_bucket = profit_transferred_by_source.setdefault(source_month, {})
                incoming_bucket[source_month] = incoming_bucket.get(source_month, 0) + profit
                outgoing_bucket[target_month] = outgoing_bucket.get(target_month, 0) + profit

# Для графика используем исходные месячные итоги листа, если они есть.
# Это сохраняет старую логику T:X. AE:AH не меняют суммы, а только
# показывают в примечаниях источник переноса.
if source_monthly_totals:
    monthly_totals = source_monthly_totals.copy()
selected_total = monthly_totals.get(selected_month, 0)


# ── metrics ──
breakeven = 2_000_000
ratio = (selected_total / breakeven * 100) if breakeven > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    danger = "danger" if selected_total < breakeven else "ok"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value {danger}">{fmt(selected_total)} ₽</div>
        <div class="metric-label">План на {month_names[selected_month]}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{fmt(breakeven)} ₽</div>
        <div class="metric-label">Безубыточная выручка</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    pct_color = "danger" if ratio < 90 else "ok"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value {pct_color}">{ratio:.0f}%</div>
        <div class="metric-label">Выполнение плана</div>
    </div>
    """, unsafe_allow_html=True)

# ── сводка выручки, дизайнеров и прибыли над таблицей ──
summary_col1, summary_col2 = st.columns([1.25, 1])

with summary_col1:
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-subtitle" style="margin-bottom:0.8rem;">План на выручку по месяцам <span class="breakeven-line">Безубыточность: {fmt(breakeven)} ₽</span></div>', unsafe_allow_html=True)
    if monthly_totals:
        max_val = max(list(monthly_totals.values()) + [breakeven]) or 1
        bars_html = ""
        for m in range(7, 13):
            val = monthly_totals.get(m, 0)
            pct = round(val / max_val * 100, 1)
            be_pct = round(breakeven / max_val * 100, 1)
            bar_color = ORANGE if val < breakeven else SUCCESS
            weight = "600" if m == selected_month else "400"
            text_color = GRAPHITE if m == selected_month else "#999"
            row_class = 'current-month-summary' if m == selected_month else ''
            bars_html += f'<div class="{row_class}" style="margin-bottom:0.6rem;">'
            bars_html += '<div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:0.2rem;">'
            bars_html += f'<span style="font-weight:{weight};color:{text_color}">{month_names[m]}</span>'
            target_sources = revenue_transferred_by_target.get(m, {})
            source_targets = revenue_transferred_by_source.get(m, {})
            transferred_amount = sum(target_sources.values())
            new_projects_amount = max(0, val - transferred_amount)
            incoming_line = '\n'.join(f'- {month_names.get(src, src)}: {fmt(amount)} ₽' for src, amount in sorted(target_sources.items())) or '- нет'
            outgoing_line = '\n'.join(f'{month_names.get(target, target)}: {fmt(amount)} ₽' for target, amount in sorted(source_targets.items())) or 'нет'
            tooltip = (
                f'План месяца: {fmt(val)} ₽\n'
                f'В том числе:\n'
                f'- Перенесено из другого месяца:\n{incoming_line}\n'
                f'- Новыми проектами: {fmt(new_projects_amount)} ₽\n\n'
                f'! Скорректировано руководителем и исключено в этом месяце:\n{outgoing_line}'
                if val else 'Нет плановой выручки'
            )
            tooltip_html = html_lib.escape(tooltip).replace('\n', '<br>')
            bars_html += f'<span class="bar-tooltip"><span class="bar-value" style="font-weight:600;color:{bar_color}">{fmt(val)} ₽</span><span class="bar-tooltip-text">{tooltip_html}</span></span>'
            bars_html += '</div>'
            bars_html += f'<div style="position:relative;height:24px;background:{GRAY};border-radius:6px;">'
            bar_pct = round(val / max_val * 100, 1) if max_val else 0
            if bar_pct:
                bars_html += f'<div style="position:absolute;left:0;top:0;height:24px;width:{bar_pct}%;background:{bar_color};border-radius:6px;opacity:0.7;"></div>'
            bars_html += f'<div style="position:absolute;left:{be_pct}%;top:-2px;width:2px;height:28px;background:{ORANGE};border-radius:1px;opacity:0.5;"></div>'
            bars_html += '</div></div>'
        summary_html = f'<div style="max-width:600px;">{bars_html}</div>'
        summary_html += '<div style="font-size:0.7rem;color:#999;margin-top:0.35rem;">Наведите на сумму, чтобы увидеть разбивку плана.</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

with summary_col2:
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-subtitle" style="margin-bottom:0.8rem;">Ответственность по выручке на дизайнерах — {month_names[selected_month]}</div>', unsafe_allow_html=True)
    designer_revenue = {}
    for p in projects:
        for idx in PLAN_INDICES:
            if idx >= len(p['revenues']):
                continue
            if displayed_stage_month(p, idx) == selected_month:
                designer = p['designer']
                designer_revenue[designer] = designer_revenue.get(designer, 0) + p['revenues'][idx]
    designer_revenue = {k: v for k, v in sorted(designer_revenue.items(), key=lambda item: -item[1]) if v > 0}
    if designer_revenue:
        max_dr = max(designer_revenue.values())
        dr_html = ""
        for designer, total in designer_revenue.items():
            pct = round(total / max_dr * 100, 1) if max_dr > 0 else 0
            dr_html += '<div style="margin-bottom:0.65rem;">'
            dr_html += '<div style="display:flex;justify-content:space-between;gap:0.5rem;font-size:0.78rem;margin-bottom:0.2rem;">'
            dr_html += f'<span style="color:{GRAPHITE};font-weight:500;overflow-wrap:anywhere;">{designer}</span>'
            dr_html += f'<span style="font-weight:600;color:{GRAPHITE};white-space:nowrap;">{fmt(total)} ₽</span>'
            dr_html += '</div>'
            dr_html += f'<div style="position:relative;height:20px;background:{GRAY};border-radius:6px;">'
            dr_html += f'<div style="position:absolute;left:0;top:0;height:20px;width:{pct}%;background:{GRAPHITE};border-radius:6px;opacity:0.6;"></div>'
            dr_html += '</div></div>'
        dr_html += f'<div style="font-size:0.78rem;font-weight:600;color:{GRAPHITE};margin-top:0.8rem;">Итого: {fmt(sum(designer_revenue.values()))} ₽</div>'
        st.markdown(dr_html, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:0.8rem;color:#999;">Нет плановой выручки на {month_names[selected_month]}</div>', unsafe_allow_html=True)

# ── прибыль по месяцам и прибыль, которая ещё придёт на счёт ──
st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle" style="margin-bottom:0.8rem;">Прибыль по месяцам</div>', unsafe_allow_html=True)

profit_col1, profit_col2 = st.columns(2)
profit_max = max(
    list(monthly_profit_totals.values()) + list(monthly_profit_unreceived.values()) + [1]
)

with profit_col1:
    st.markdown('<div class="hero-subtitle" style="margin-bottom:0.8rem;">Плановая прибыль <span class="breakeven-line">безубыточность разработки: 1 000 000 ₽</span></div>', unsafe_allow_html=True)
    if monthly_profit_totals:
        profit_bars_html = ""
        for m in range(7, 13):
            val = monthly_profit_totals.get(m, 0)
            weight = "600" if m == selected_month else "400"
            text_color = GRAPHITE if m == selected_month else "#999"
            bar_color = SUCCESS if val > 0 else ORANGE
            target_sources = profit_transferred_by_target.get(m, {})
            source_targets = profit_transferred_by_source.get(m, {})
            transferred_amount = sum(target_sources.values())
            new_projects_amount = max(0, val - transferred_amount)
            incoming_line = '\\n'.join(f'- {month_names.get(src, src)}: {fmt(amount)} ₽' for src, amount in sorted(target_sources.items())) or '- нет'
            outgoing_line = '\\n'.join(f'{month_names.get(target, target)}: {fmt(amount)} ₽' for target, amount in sorted(source_targets.items())) or 'нет'
            tooltip = (
                f'План месяца: {fmt(val)} ₽\\n'
                f'В том числе:\\n'
                f'- Перенесено из другого месяца:\\n{incoming_line}\\n'
                f'- Новыми проектами: {fmt(new_projects_amount)} ₽\\n\\n'
                f'! Скорректировано руководителем и исключено в этом месяце:\\n{outgoing_line}'
                if val else 'Нет плановой прибыли'
            )
            tooltip_html = html_lib.escape(tooltip).replace('\\n', '<br>')
            profit_bars_html += '<div style="margin-bottom:0.6rem;">'
            profit_bars_html += '<div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:0.2rem;">'
            profit_bars_html += f'<span style="font-weight:{weight};color:{text_color}">{month_names[m]}</span>'
            profit_bars_html += f'<span class="bar-tooltip"><span class="bar-value" style="font-weight:600;color:{bar_color}">{fmt(val)} ₽</span><span class="bar-tooltip-text">{tooltip_html}</span></span>'
            profit_bars_html += '</div>'
            profit_bars_html += f'<div style="position:relative;height:24px;background:{GRAY};border-radius:6px;">'
            bar_pct = round(val / profit_max * 100, 1) if profit_max else 0
            if bar_pct:
                profit_bars_html += f'<div style="position:absolute;left:0;top:0;height:24px;width:{bar_pct}%;background:{bar_color};border-radius:6px;opacity:0.7;"></div>'
            profit_bars_html += '</div></div>'
        profit_summary_html = f'<div style="max-width:600px;">{profit_bars_html}</div>'
        profit_summary_html += '<div style="font-size:0.7rem;color:#999;margin-top:0.35rem;">Наведите на сумму, чтобы увидеть разбивку прибыли.</div>'
        st.markdown(profit_summary_html, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.8rem;color:#999;">Нет плановой прибыли по месяцам</div>', unsafe_allow_html=True)

with profit_col2:
    st.markdown('<div class="hero-subtitle" style="margin-bottom:0.8rem;">В том числе прибыль ещё придёт на счёт</div>', unsafe_allow_html=True)
    if monthly_profit_unreceived:
        unreceived_bars_html = ""
        for m in range(7, 13):
            val = monthly_profit_unreceived.get(m, 0)
            weight = "600" if m == selected_month else "400"
            text_color = GRAPHITE if m == selected_month else "#999"
            bar_color = WARNING if val > 0 else "#BDBDBD"
            tooltip = (
                f'Прибыль по выполненным этапам: {fmt(val)} ₽\\n'
                f'Оплата по этим этапам ещё не поступила на счёт\\n'
                f'Заполненная AP:AU означает, что оплата ещё ожидается, пустая ячейка - этап уже оплачен'
                if val else 'Нет прибыли, которая ещё придёт на счёт'
            )
            tooltip_html = html_lib.escape(tooltip).replace('\\n', '<br>')
            unreceived_bars_html += '<div style="margin-bottom:0.6rem;">'
            unreceived_bars_html += '<div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:0.2rem;">'
            unreceived_bars_html += f'<span style="font-weight:{weight};color:{text_color}">{month_names[m]}</span>'
            unreceived_bars_html += f'<span class="bar-tooltip"><span class="bar-value" style="font-weight:600;color:{bar_color}">{fmt(val)} ₽</span><span class="bar-tooltip-text">{tooltip_html}</span></span>'
            unreceived_bars_html += '</div>'
            unreceived_bars_html += f'<div style="position:relative;height:24px;background:{GRAY};border-radius:6px;">'
            bar_pct = round(val / profit_max * 100, 1) if profit_max else 0
            if bar_pct:
                unreceived_bars_html += f'<div style="position:absolute;left:0;top:0;height:24px;width:{bar_pct}%;background:{bar_color};border-radius:6px;opacity:0.7;"></div>'
            unreceived_bars_html += '</div></div>'
        unreceived_summary_html = f'<div style="max-width:600px;">{unreceived_bars_html}</div>'
        unreceived_summary_html += '<div style="font-size:0.7rem;color:#999;margin-top:0.35rem;">Прибыль уже отражена в ОПИУ, но соответствующая оплата ещё не пришла.</div>'
        st.markdown(unreceived_summary_html, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.8rem;color:#999;">Нет прибыли, которая ещё придёт на счёт</div>', unsafe_allow_html=True)

# ── фильтры проектной таблицы ──
st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle" style="margin-bottom:0.8rem;">Фильтр проектов</div>', unsafe_allow_html=True)
filter_col1, filter_col2 = st.columns([1, 2])
designer_options = sorted({p['designer'] for p in projects})
with filter_col1:
    selected_designers = st.multiselect(
        'Дизайнеры',
        designer_options,
        default=[],
        key='project_designer_filter',
    )
with filter_col2:
    project_options = sorted({p['name'] for p in projects})
    selected_projects = st.multiselect(
        'Проекты',
        project_options,
        default=[],
        key='project_name_filter',
    )
filtered_projects = [
    p for p in projects
    if (not selected_designers or p['designer'] in selected_designers)
    and (not selected_projects or p['name'] in selected_projects)
]

# ── проектная таблица ──
if filtered_projects:
    table_html = '<table class="plan-table"><thead>'
    table_html += '<tr class="group-row">'
    table_html += '<th colspan="4"></th><th colspan="6">Этапы</th>'
    table_html += '<th colspan="6" class="money-group-left">Суммы ВР по этапам</th>'
    table_html += '<th colspan="6" class="profit-group-left">Прибыль по этапам</th></tr>'
    table_html += '<tr>'
    table_html += '<th>Проект</th><th>Заказчик</th><th>Договор</th><th>Дизайнер</th>'
    table_html += '<th class="stage-left">1 этап</th><th>2 этап</th><th>3 этап</th><th>4 этап</th><th>5 этап</th><th class="stage-right">Постоплата</th>'
    table_html += '<th class="money-group-left">1 этап, ₽</th><th>2 этап, ₽</th><th>3 этап, ₽</th><th>4 этап, ₽</th><th>5 этап, ₽</th><th class="money-group-right">Постоплата, ₽</th>'
    table_html += '<th class="profit-group-left">1 этап, ₽</th><th>2 этап, ₽</th><th>3 этап, ₽</th><th>4 этап, ₽</th><th>5 этап, ₽</th><th class="profit-group-right">Постоплата, ₽</th>'
    table_html += '</tr></thead><tbody>'

    for p in filtered_projects:
        table_html += '<tr>'
        table_html += f'<td class="project-name">{p["name"]}</td><td>{p["client"]}</td><td>{p["contract"]}</td><td>{p["designer"]}</td>'

        for idx in range(6):
            month = p['months'][idx] if idx < len(p['months']) else 0
            cls_parts = []
            actual_month = actual_stage_month(p, idx)
            if is_shifted_stage(p, idx):
                note = f'Этап перенесён из {month_names.get(month, month)} в {month_names.get(actual_month, actual_month)}'
            else:
                note = ''
            if idx == 0: cls_parts.append('stage-left')
            if idx == 5: cls_parts.append('stage-right')
            if project_base_month(p, idx) == selected_month and month:
                cls_parts.append('highlight')
            if is_shifted_stage(p, idx):
                cls_parts.append('shifted-month-cell')
            table_html += f'<td class="{" ".join(cls_parts)}">{month if month else ""}</td>'
        for idx in range(6):
            revenue = p['revenues'][idx] if idx < len(p['revenues']) else 0
            cls_parts = []
            if idx == 0: cls_parts.append('money-group-left')
            if idx == 5: cls_parts.append('money-group-right')
            if displayed_stage_month(p, idx) == selected_month and revenue:
                cls_parts.append('highlight')
            if is_shifted_stage(p, idx) and revenue:
                cls_parts.append('shifted-month-cell')
            note = transfer_note(p, idx, revenue, 'revenue')
            table_html += f'<td class="{" ".join(cls_parts)}">{fmt(revenue)}</td>'

        for idx in range(6):
            profit = p['profits'][idx] if idx < len(p['profits']) else 0
            cls_parts = []
            if idx == 0: cls_parts.append('profit-group-left')
            if idx == 5: cls_parts.append('profit-group-right')
            if displayed_stage_month(p, idx) == selected_month and profit:
                cls_parts.append('profit-cell')
            if is_shifted_stage(p, idx) and profit:
                cls_parts.append('shifted-month-cell')
            note = transfer_note(p, idx, profit, 'profit')
            table_html += f'<td class="{" ".join(cls_parts)}">{fmt(profit)}</td>'
        table_html += '</tr>'

    total_revenue = sum(
        p['revenues'][idx]
        for p in filtered_projects
        for idx in PLAN_INDICES
        if idx < len(p['revenues'])
        and project_base_month(p, idx) == selected_month
    )
    total_profit = sum(
        p['profits'][idx]
        for p in filtered_projects
        for idx in PLAN_INDICES
        if idx < len(p['profits'])
        and project_base_month(p, idx) == selected_month
    )
    table_html += '<tr class="summary-row">'
    table_html += '<td colspan="10">ИТОГО ЗА ВЫБРАННЫЙ МЕСЯЦ</td>'
    table_html += f'<td colspan="6" class="money-group-left">{fmt(total_revenue)} ₽</td>'
    table_html += f'<td colspan="6" class="profit-group-left">{fmt(total_profit)} ₽</td>'
    table_html += '</tr></tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)

# ── footer ──
last_update = ""
for i in range(start_row, min(start_row + 5, len(values))):
    row = values[i] if i < len(values) else []
    row_str = ' '.join([str(c) for c in row if c])
    if 'дата последнего обновления' in row_str:
        for cell in row:
            try:
                cell_str = str(cell).strip()
                if '.' in cell_str and any(c.isdigit() for c in cell_str):
                    last_update = cell_str
            except:
                pass

st.markdown(f"""
<div style="margin-top:2rem;text-align:right;font-size:0.7rem;color:#bbb;">
    Данные из Google Sheets · обновлено {last_update} · 
    <a href="https://kochenevskikh.ru" style="color:#bbb;">kochenevskikh.ru</a>
</div>
""", unsafe_allow_html=True)
