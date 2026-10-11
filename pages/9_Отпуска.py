"""
Страница «Отпуска» · Коченевских бюро
Диаграмма Ганта отпусков сотрудников из Google Sheets.
"""
import streamlit as st
import urllib.request
import urllib.parse
import json
import os
from datetime import date, timedelta

st.set_page_config(page_title="Отпуска · Коченевских", page_icon="◈", layout="wide")

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


# ── auth ──
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице")
    st.stop()

# ── brand ──
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

# ── CSS ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {WHITE}; }}
    #MainMenu, header, footer {{ visibility: hidden; }}
    
    .hero-title {{
        font-size: 2rem; font-weight: 300; color: {GRAPHITE};
        letter-spacing: -0.02em;
    }}
    .hero-subtitle {{
        font-size: 0.8rem; font-weight: 400; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase;
    }}
    .section-line {{
        height: 1px; background: {GREY}; margin: 1.5rem 0;
    }}
    
    .gantt-table {{
        width: 100%; border-collapse: collapse; font-size: 0.75rem;
    }}
    .gantt-table th {{
        background: #FAFAFA; color: #666; font-weight: 500;
        padding: 8px 4px; border-bottom: 2px solid {GREY};
        text-align: center; white-space: nowrap;
        font-size: 0.7rem; letter-spacing: 0.03em;
    }}
    .gantt-table th.name-col {{
        text-align: left; min-width: 180px; padding-left: 12px;
    }}
    .gantt-table td {{
        padding: 0; border-bottom: 1px solid {GREY};
        height: 36px; position: relative;
    }}
    .gantt-table td.name-cell {{
        padding: 0 12px; font-weight: 500; color: {GRAPHITE};
        font-size: 0.78rem; white-space: nowrap;
    }}
    .gantt-table tr:hover td {{ background: #FAFAFA; }}
    .gantt-table tr:hover td.name-cell {{ background: #FAFAFA; }}
    
    .vacation-bar {{
        position: absolute; top: 4px; height: 28px;
        border-radius: 4px; opacity: 0.85;
    }}
    
    .month-header {{
        font-size: 0.7rem !important; font-weight: 600 !important;
        color: {GRAPHITE} !important;
    }}
    
    .stat-card {{
        background: {WHITE}; border: 1px solid {GREY};
        border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center;
    }}
    .stat-value {{
        font-size: 1.8rem; font-weight: 600; color: {GRAPHITE};
    }}
    .stat-label {{
        font-size: 0.75rem; font-weight: 500; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase;
    }}
</style>
""", unsafe_allow_html=True)

# ── Google auth ──
def _get_token():
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

    data = urllib.parse.urlencode({
        'client_id': client_id, 'client_secret': client_secret,
        'refresh_token': refresh_token, 'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())['access_token']
    except Exception:
        return None

SHEET_ID = '1mg5uGPAYCjvsBdLJJP96EN_gXqrsksqNDGpTy-_Ed2k'

@st.cache_data(ttl=600)
def load_data(year):
    access_token = _get_token()
    if access_token is None:
        return None

    sheet_name = f'Календарь {year}'
    encoded = urllib.parse.quote(sheet_name)
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded}'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    try:
        data = json.loads(urllib.request.urlopen(req).read())
    except Exception:
        return None
    return data.get('values', [])

def parse_date_ranges(date_str, year):
    """Parse '16.03-30.03 21.09-05.10' into list of (start_date, end_date)."""
    if not date_str or date_str == '-':
        return []
    ranges = []
    parts = date_str.strip().split()
    for part in parts:
        part = part.strip().replace('\n', '')
        if '-' not in part:
            continue
        try:
            start_str, end_str = part.split('-')
            start_parts = start_str.strip().split('.')
            end_parts = end_str.strip().split('.')
            if len(start_parts) == 2 and len(end_parts) == 2:
                d1, m1 = int(start_parts[0]), int(start_parts[1])
                d2, m2 = int(end_parts[0]), int(end_parts[1])
                # Determine year: if end month < start month, it's next year
                y_start = year
                y_end = year if m2 >= m1 else year + 1
                ranges.append((date(y_start, m1, d1), date(y_end, m2, d2)))
        except (ValueError, IndexError):
            continue
    return ranges

def parse_employees(values, year):
    """Parse employee data from rows 5-16."""
    employees = []
    for i in range(5, min(17, len(values))):
        row = values[i] if i < len(values) else []
        if len(row) < 3:
            continue
        name = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        date_str = str(row[3]).strip() if len(row) > 3 and row[3] else ""
        total_days = str(row[4]).strip() if len(row) > 4 and row[4] else "0"
        planned_days = str(row[5]).strip() if len(row) > 5 and row[5] else "0"
        remaining = str(row[6]).strip() if len(row) > 6 and row[6] else "0"

        if not name or name in ('производство', 'менеджмент', 'отдел реализации', 'адми.состав'):
            continue
        # Skip combined rows like "Коченевских Катя+ Сергей"
        if 'Коченевских Катя' in name:
            continue

        ranges = parse_date_ranges(date_str, year)
        # Parse numeric values
        try:
            total = int(total_days.replace('-', '0'))
        except:
            total = 0
        try:
            planned = int(planned_days.replace('-', '0'))
        except:
            planned = 0
        try:
            rem = int(remaining.replace('-', '0'))
        except:
            rem = 0

        employees.append({
            'name': name,
            'ranges': ranges,
            'total': total,
            'planned': planned,
            'remaining': rem,
        })
    return employees

# ── Year selector ──
available_years = [2026, 2025]
selected_year = st.selectbox("Год", available_years, key="year_select")

values = load_data(selected_year)

if values is None:
    st.error("Не удалось загрузить данные. Проверьте доступ к Google Sheets.")
    st.stop()

employees = parse_employees(values, selected_year)

# ── Header ──
st.markdown(f"""
<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.2rem;">
    <img src="{LOGO_URL}" style="height:24px;width:auto;">
    <span class="hero-title">Отпуска {selected_year}</span>
</div>
""", unsafe_allow_html=True)

# ── Summary cards ──
total_employees = len(employees)
on_vacation_now = 0
today = date.today()
for emp in employees:
    for s, e in emp['ranges']:
        if s <= today <= e:
            on_vacation_now += 1
            break

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-value">{total_employees}</div><div class="stat-label">Сотрудников</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-value" style="color:{ORANGE};">{on_vacation_now}</div><div class="stat-label">В отпуске сейчас</div></div>', unsafe_allow_html=True)
with c3:
    total_remaining = sum(e['remaining'] for e in employees)
    st.markdown(f'<div class="stat-card"><div class="stat-value" style="color:#2E7D32;">{total_remaining}</div><div class="stat-label">Осталось дней отпуска</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

# ── Gantt chart ──
if not employees:
    st.info("Нет данных по отпускам за этот год.")
    st.stop()

# Build month columns: all 12 months
month_names = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
months_in_year = []
for m in range(1, 13):
    # Days in month
    if m == 12:
        next_m = date(selected_year, 12, 31)
    else:
        next_m = date(selected_year, m + 1, 1) - timedelta(days=1)
    days = next_m.day
    months_in_year.append({'num': m, 'days': days})

# Total day columns for the year
total_days_in_year = 365 + (1 if selected_year % 4 == 0 and (selected_year % 100 != 0 or selected_year % 400 == 0) else 0)
day_width_pct = 100.0 / total_days_in_year

# Build Gantt table
gantt_html = '<table class="gantt-table"><thead><tr>'
gantt_html += '<th class="name-col">Сотрудник</th>'

# Month headers with colspan proportional to days
for m_info in months_in_year:
    gantt_html += f'<th class="month-header" style="width:{m_info["days"] * day_width_pct:.1f}%;">{month_names[m_info["num"]-1]}</th>'
gantt_html += '</tr></thead><tbody>'

# Color palette for employees
colors = ["#F74028", "#2E7D32", "#1565C0", "#6A1B9A", "#E65100", "#00838F", "#4E342E", "#558B2F", "#C62828", "#283593", "#AD1457", "#00695C"]

for idx, emp in enumerate(employees):
    color = colors[idx % len(colors)]
    
    gantt_html += '<tr>'
    gantt_html += f'<td class="name-cell">{emp["name"]}</td>'
    
    # Build vacation bars for each month cell
    for m_info in months_in_year:
        m = m_info['num']
        month_start = date(selected_year, m, 1)
        if m == 12:
            month_end = date(selected_year, 12, 31)
        else:
            month_end = date(selected_year, m + 1, 1) - timedelta(days=1)
        
        gantt_html += '<td>'
        
        for s, e in emp['ranges']:
            # Find overlap with this month
            overlap_start = max(s, month_start)
            overlap_end = min(e, month_end)
            if overlap_start <= overlap_end:
                # Calculate position within the month cell
                days_in_month = m_info['days']
                day_offset = (overlap_start - month_start).days
                span_days = (overlap_end - overlap_start).days + 1
                
                left_pct = (day_offset / days_in_month * 100) if days_in_month > 0 else 0
                width_pct = (span_days / days_in_month * 100) if days_in_month > 0 else 0
                
                # Clamp
                left_pct = max(0, min(100, left_pct))
                width_pct = max(1, min(100 - left_pct, width_pct))
                
                gantt_html += f'<div class="vacation-bar" style="left:{left_pct:.1f}%;width:{width_pct:.1f}%;background:{color};" title="{s.strftime("%d.%m")} – {e.strftime("%d.%m")}"></div>'
        
        gantt_html += '</td>'
    
    gantt_html += '</tr>'

gantt_html += '</tbody></table>'

st.markdown(gantt_html, unsafe_allow_html=True)

# ── Detail table ──
st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-subtitle">Детализация</div>', unsafe_allow_html=True)

detail_html = '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;margin-top:12px;">'
detail_html += '<thead><tr style="background:#FAFAFA;color:#666;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;">'
detail_html += '<th style="padding:8px 12px;text-align:left;">Сотрудник</th>'
detail_html += '<th style="padding:8px 12px;text-align:left;">Периоды</th>'
detail_html += '<th style="padding:8px 12px;text-align:center;">Всего дней</th>'
detail_html += '<th style="padding:8px 12px;text-align:center;">Запланировано</th>'
detail_html += '<th style="padding:8px 12px;text-align:center;">Остаток</th>'
detail_html += '</tr></thead><tbody>'

for emp in employees:
    periods = ', '.join(f'{s.strftime("%d.%m")}–{e.strftime("%d.%m")}' for s, e in emp['ranges'])
    if not periods:
        periods = '—'
    
    rem_color = ORANGE if emp['remaining'] <= 0 else '#2E7D32'
    
    detail_html += '<tr style="border-bottom:1px solid #E6E6E6;">'
    detail_html += f'<td style="padding:8px 12px;font-weight:500;color:{GRAPHITE};">{emp["name"]}</td>'
    detail_html += f'<td style="padding:8px 12px;color:#555;">{periods}</td>'
    detail_html += f'<td style="padding:8px 12px;text-align:center;color:{GRAPHITE};">{emp["total"]}</td>'
    detail_html += f'<td style="padding:8px 12px;text-align:center;color:{GRAPHITE};">{emp["planned"]}</td>'
    detail_html += f'<td style="padding:8px 12px;text-align:center;font-weight:600;color:{rem_color};">{emp["remaining"]}</td>'
    detail_html += '</tr>'

detail_html += '</tbody></table>'
st.markdown(detail_html, unsafe_allow_html=True)

# ── footer ──
st.markdown(f"""
<div style="margin-top:2rem;text-align:right;font-size:0.7rem;color:#bbb;">
    Данные из Google Sheets · 
    <a href="https://kochenevskikh.ru" style="color:#bbb;">kochenevskikh.ru</a>
</div>
""", unsafe_allow_html=True)
