"""
dashboard.py — Ключевые показатели студии «Коченевских»
Одна страница: результаты месяца + счета + календарь приходов/расходов
"""
import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
import csv
import io
import json
import calendar
import html
import re
from datetime import date, datetime

# ── page config ──────────────────────────────────────
st.set_page_config(
    page_title="Ключевые показатели · Коченевских",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="auto"
)

# ── password ─────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""<style>.stApp { background: #FFFFFF; }
    @media (max-width: 640px) {
        .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
        .hero-title { font-size: 1.35rem; }
        .profit-scenarios { gap: 0.7rem; }
        .profit-scenario-label { font-size: 0.62rem; }
        .debt-value { font-size: 2rem; }
        .hero-subtitle { font-size: 1.05rem; }
        .plan-card-sm-pct-row { flex-wrap: wrap; gap: 0.25rem 0.45rem; }
    }
</style>""", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            '<h1 style="text-align:center;font-weight:300;color:#252525;">'
            '<img src="https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png" '
            'style="height:28px;vertical-align:middle;margin-right:10px;">'
            'Финансы студии</h1>',
            unsafe_allow_html=True
        )
        password = st.text_input("Пароль", type="password", key="pw_input")
        if st.button("Войти", use_container_width=True):
            if password == "845K":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Неверный пароль")
    st.stop()

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
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GRAY = "#E6E6E6"
WHITE = "#FFFFFF"
SUCCESS = "#2E7D32"
WARNING = "#E65100"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

# ── CSS ──────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', -apple-system, sans-serif !important; }}
    .stApp {{ background: {WHITE}; }}
    #MainMenu {{ visibility: hidden; }}
    header {{ visibility: visible !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    .hero-title {{
        font-size: 2.15rem; font-weight: 300; color: {GRAPHITE};
        letter-spacing: -0.03em; margin-bottom: 0.35rem;
    }}
    .hero-subtitle {{
        font-size: 1.25rem; font-weight: 500; color: {GRAPHITE};
        letter-spacing: 0.01em; text-transform: none; margin-bottom: 2rem;
    }}

    .metric-card {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 12px; padding: 1.4rem 1.6rem; transition: border-color 0.2s;
    }}
    .metric-card:hover {{ border-color: #ccc; }}
    .metric-value {{
        font-size: 2rem; font-weight: 600; color: {GRAPHITE};
        letter-spacing: -0.02em; line-height: 1.1;
    }}
    .metric-value.negative {{ color: {ORANGE}; }}
    .metric-value.positive {{ color: {SUCCESS}; }}
    .metric-label {{
        font-size: 0.78rem; font-weight: 500; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase; margin-top: 0.3rem;
    }}

    .profit-wide {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 12px; padding: 1.4rem 1.6rem;
    }}
    .profit-main {{
        font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1;
    }}
    .profit-scenarios {{
        display: flex; gap: 1.5rem; margin-top: 0.8rem;
        padding-top: 0.8rem; border-top: 1px solid {GRAY};
    }}
    .profit-scenario {{ flex: 1; }}
    .profit-scenario-val {{ font-size: 1.05rem; font-weight: 600; }}
    .profit-scenario-label {{ font-size: 0.7rem; color: #999; margin-top: 0.15rem; }}

    .section-line {{ height: 1px; background: {GRAY}; margin: 1.6rem 0; }}
    .section-title {{
        font-size: 1rem; font-weight: 700; color: {GRAPHITE};
        letter-spacing: 0.01em; text-transform: none; margin-bottom: 0.85rem;
        padding-left: 0.15rem;
    }}

    .wallet-block {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 12px; padding: 1.2rem 1.4rem;
    }}
    .wallet-header {{
        font-size: 0.7rem; font-weight: 500; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.5rem;
    }}
    .wallet-total {{
        font-size: 1.6rem; font-weight: 600; color: {GRAPHITE}; letter-spacing: -0.02em;
    }}
    .wallet-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.3rem 0; font-size: 0.82rem;
    }}
    .wallet-name {{ color: #999; font-weight: 400; }}
    .wallet-amount {{ color: {GRAPHITE}; font-weight: 500; }}

    .overrun-badge {{
        display: inline-block; background: #FFF5F5; border: 1px solid #FFD6D6;
        border-radius: 8px; padding: 0.5rem 1rem;
        font-size: 0.8rem; color: {ORANGE}; font-weight: 500;
    }}

    /* calendar */
    .cal-table {{ width: 100%; border-collapse: separate; border-spacing: 3px; }}
    .cal-table th {{
        text-align: center; font-size: 11px; color: #999; padding: 4px 0; font-weight: 400;
    }}
    .cal-table td {{
        background: #fff; border: 1px solid {GRAY}; border-radius: 10px;
        padding: 8px 5px; text-align: center; vertical-align: top; width: 14.2%;
    }}
    .cal-table td.today {{ border: 2px solid {ORANGE}; background: #FFF9F7; }}
    .cal-table td.empty {{ background: #fafafa; border: 1px dashed #e8e8e8; }}
    .cal-num {{ font-size: 15px; font-weight: 700; color: {GRAPHITE}; }}
    .cal-num.today {{ color: {ORANGE}; }}

    .cal-inc {{
        font-size: 13px; font-weight: 700; color: {SUCCESS}; margin-top: 3px;
        background: #E8F5E9; border-radius: 4px; padding: 2px 4px;
    }}
    .cal-split {{
        font-size: 10px; color: {SUCCESS}; line-height: 1.4;
        padding: 1px 0; margin-top: 1px;
    }}
    .cal-table.detailed td {{
        padding: 8px 6px; min-height: 112px;
    }}
    .cal-detail-line {{
        display: flex; justify-content: space-between; gap: 4px;
        text-align: left; font-size: 10px; line-height: 1.25;
        margin-top: 3px; padding-top: 3px; border-top: 1px solid #F0F0F0;
    }}
    .cal-detail-line span {{
        min-width: 0; overflow-wrap: anywhere;
    }}
    .cal-detail-line strong {{ white-space: nowrap; font-weight: 600; }}
    .cal-detail-line.income {{ color: {SUCCESS}; }}
    .cal-detail-line.expense {{ color: {ORANGE}; }}
    .calendar-view-label {{
        font-size: 0.78rem; color: #888; margin: -0.35rem 0 0.5rem 0;
    }}
    .cal-exp {{
        font-size: 12px; font-weight: 700; color: {ORANGE}; margin-top: 2px;
        background: #FFF5F5; border-radius: 4px; padding: 2px 4px;
    }}
    .cal-net {{
        font-size: 10px; font-weight: 600; margin-top: 2px;
        padding: 2px 4px; border-radius: 4px;
        background: #F5F5F5;
    }}

    .cal-summary {{
        display: flex; gap: 1rem; margin-top: 1rem;
    }}
    .cal-summary-item {{
        flex: 1; background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 10px; padding: 1rem; text-align: center;
    }}
    .cal-summary-val {{ font-size: 1.2rem; font-weight: 600; color: {GRAPHITE}; }}
    .cal-summary-label {{ font-size: 0.72rem; color: #999; margin-top: 0.2rem; }}
    .cal-summary-sub {{ font-size: 0.7rem; color: #bbb; margin-top: 0.15rem; }}

    .weekly-summary {{
        margin-top: 1.15rem; border-top: 1px solid {GRAY};
        padding-top: 0.75rem;
    }}
    .weekly-summary-title {{
        font-size: 0.9rem; font-weight: 600; color: {GRAPHITE};
        margin-bottom: 0.45rem;
    }}
    .weekly-line {{
        display: grid; grid-template-columns: 110px 1fr 1fr 1fr;
        gap: 0.8rem; align-items: center;
        padding: 0.42rem 0; border-bottom: 1px solid #F2F2F2;
        font-size: 0.8rem;
    }}
    .weekly-line.current {{ background: #FFF9F7; border-radius: 5px; padding-left: 0.45rem; }}
    .weekly-label {{ color: {GRAPHITE}; font-weight: 600; }}
    .weekly-value {{ color: {GRAPHITE}; white-space: nowrap; }}
    .weekly-value.income {{ color: {SUCCESS}; }}
    .weekly-value.expense {{ color: {ORANGE}; }}
    .weekly-value.positive {{ color: {SUCCESS}; }}
    .weekly-value.negative {{ color: {ORANGE}; }}
    @media (max-width: 640px) {{
        .weekly-line {{ grid-template-columns: 82px 1fr 1fr 1fr; gap: 0.35rem; font-size: 0.7rem; }}
    }}

    /* plan cards (below calendar) */
    .plan-card-sm {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 14px; padding: 1.45rem 1.5rem; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .plan-card-sm-title {{
        font-size: 0.82rem; font-weight: 600; color: {GRAPHITE};
        letter-spacing: 0.02em; text-transform: uppercase; margin-bottom: 0.9rem;
    }}
    .plan-card-sm-pct-row {{
        display: flex; align-items: baseline; justify-content: center;
        gap: 0.55rem; white-space: nowrap;
    }}
    .plan-card-sm-pct {{
        font-size: 1.85rem; font-weight: 700; line-height: 1.1;
        letter-spacing: -0.03em;
    }}
    .plan-card-sm-fact {{
        font-size: 0.95rem; font-weight: 600; color: {GRAPHITE};
    }}
    .plan-card-sm-val {{
        font-size: 1rem; font-weight: 600; color: #666;
        margin-top: 1rem; padding-top: 0.8rem;
        border-top: 1px dashed #BDBDBD;
    }}
    .debt-card {{
        background: {WHITE}; border: 2px solid {ORANGE};
        border-radius: 12px; padding: 1.6rem 1.8rem; min-height: 100%;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .debt-value {{
        font-size: 2.4rem; font-weight: 600; color: {GRAPHITE};
        letter-spacing: -0.03em; line-height: 1.1;
    }}
    .control-card {{
        background: {WHITE}; border: 1px solid {GRAY};
        border-radius: 12px; padding: 1.2rem 1.4rem;
        min-height: 100%;
    }}
    .control-header {{
        font-size: 0.7rem; font-weight: 600; color: #999;
        letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.65rem;
    }}
    .control-total {{
        font-size: 1.7rem; font-weight: 600; color: {GRAPHITE};
        letter-spacing: -0.02em; margin-bottom: 0.55rem;
    }}
    .control-row {{
        display: flex; justify-content: space-between; gap: 1rem;
        padding: 0.38rem 0; border-top: 1px solid #F2F2F2;
        font-size: 0.82rem;
    }}
    .control-name {{ color: #777; }}
    .control-amount {{ color: {GRAPHITE}; font-weight: 600; white-space: nowrap; }}
    .control-row-extended {{
        display: grid; grid-template-columns: minmax(140px, 1.8fr) 0.9fr 0.9fr 1.1fr 1.3fr;
        align-items: center; gap: 0.5rem;
    }}
    @media (max-width: 900px) {{
        .control-row-extended {{
            grid-template-columns: minmax(110px, 1fr) 1fr 1fr;
            row-gap: 0.2rem;
        }}
        .control-row-extended .control-name {{ grid-column: span 3; font-weight: 600; color: {GRAPHITE}; }}
    }}
    .control-spent, .control-pct-cell, .control-limit, .control-remaining, .control-overrun, .control-pct {{
        text-align: right; white-space: nowrap; color: {GRAPHITE};
    }}
    .control-spent {{ font-weight: 600; }}
    .control-pct-cell {{ text-align: right; }}
    .control-pct-inline {{ color: {ORANGE}; font-weight: 700; }}
    .control-limit {{ color: #999; font-size: 0.78rem; text-align: right; }}
    .control-remaining {{ color: {SUCCESS}; font-weight: 600; text-align: right; }}
    .control-overrun {{ color: {ORANGE}; font-weight: 700; text-align: right; }}
    .control-empty {{ color: #aaa; font-size: 0.85rem; padding-top: 0.3rem; }}
    .plan-card-sm-sub {{
        font-size: 0.72rem; color: #aaa; margin-top: 4px;
    }}

    .block-container {{
        padding-top: 2rem !important; padding-bottom: 1rem !important;
        padding-left: 2rem !important; padding-right: 2rem !important;
        max-width: 100% !important; width: 100% !important;
    }}

    /* Небольшая временная шкала цели «Машина» */
    .car-progress-wrap {{
        width: 58%; min-width: 420px; max-width: 760px;
        margin: 0.6rem 0 1.35rem 0;
    }}
    .car-progress-track {{
        position: relative; height: 86px;
    }}
    .car-progress-line {{
        position: absolute; left: 0; right: 92px; top: 42px;
        height: 2px; background: #252525;
    }}
    .car-progress-slider {{
        position: absolute; top: 29px; width: 4px; height: 28px;
        background: #F74028; border-radius: 4px;
        box-shadow: 0 0 0 3px rgba(247,64,40,0.12);
    }}
    .car-progress-slider::before {{
        content: ''; position: absolute; left: -5px; top: -5px;
        width: 14px; height: 14px; border-radius: 50%;
        background: #FFFFFF; border: 2px solid #F74028;
    }}
    .car-progress-image {{
        position: absolute; right: 0; top: 0; width: 92px; height: 78px;
        object-fit: contain; object-position: center;
    }}
    @media (max-width: 640px) {{
        .car-progress-wrap {{ width: 100%; min-width: 0; }}
        .car-progress-line {{ right: 78px; }}
        .car-progress-image {{ width: 78px; }}
    }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════

def _get_google_token():
    """Refresh and return Google OAuth access token."""
    try:
        client_id = st.secrets["google_client_id"]
        client_secret = st.secrets["google_client_secret"]
        refresh_token = st.secrets["google_refresh_token"]
    except Exception:
        import os
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
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read())
    return tokens['access_token']


CAR_SHEET_ID = "1rXm66oriSs533ghAe4PNi6ze28P-lVPxVUJ63JOKcc0"
CAR_SHEET_GID = 1084693313

@st.cache_data(ttl=600, show_spinner=False)
def load_car_progress():
    """Читает текущий процент цели «Машина» из ячейки D6 через Google Sheets API."""
    access_token = _get_google_token()
    if not access_token:
        return 0.0
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        meta_url = f'https://sheets.googleapis.com/v4/spreadsheets/{CAR_SHEET_ID}'
        req = urllib.request.Request(meta_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())
        sheet_name = next(
            (s['properties']['title'] for s in info.get('sheets', [])
             if s['properties']['sheetId'] == CAR_SHEET_GID),
            None,
        )
        if not sheet_name:
            return 0.0
        cell_range = urllib.parse.quote(f"'{sheet_name}'!D6", safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{CAR_SHEET_ID}/values/{cell_range}'
        req = urllib.request.Request(values_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            values = json.loads(resp.read()).get('values', [])
        raw_value = values[0][0] if values and values[0] else ''
        raw_value = str(raw_value).replace('\u00a0', ' ').replace('%', '').replace(' ', '').replace(',', '.')
        progress = float(raw_value) if raw_value else 0.0
        return max(0.0, min(progress, 100.0))
    except Exception:
        return 0.0


# ═══════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def load_expenses_control():
    """Расходы на контроле за текущий месяц по правилам листа расходы_контроль."""
    CONTROL_URL = (
        'https://docs.google.com/spreadsheets/d/'
        '1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw'
        '/export?format=csv&gid=907517409'
    )
    DDS_URL = (
        'https://docs.google.com/spreadsheets/d/'
        '1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw'
        '/export?format=csv&gid=0'
    )

    def get_csv(url):
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return list(csv.reader(io.StringIO(resp.read().decode('utf-8-sig', errors='replace'))))

    def norm(value):
        return ' '.join(str(value or '').replace('\u00a0', ' ').split()).strip().casefold()

    def parse_amount(value):
        text = str(value or '').replace('\u00a0', '').replace(' ', '').replace('"', '').replace(',', '.')
        try:
            return float(text)
        except (TypeError, ValueError):
            return 0.0

    try:
        control_rows = get_csv(CONTROL_URL)
        dds_rows = get_csv(DDS_URL)

        # В листе расходы_контроль: B = статья, C = контрагент, D = название на дашборде.
        rules = []
        for row in control_rows[6:]:
            if len(row) < 4 or not norm(row[1]) or norm(row[1]) == 'статья':
                continue
            rules.append({
                'article': norm(row[1]),
                'counterparty': norm(row[2]),
                'label': str(row[3] or row[1]).strip(),
                'limit': parse_amount(row[4]) if len(row) > 4 else 0.0,
            })
        if not rules:
            return [], 0.0, ''

        now = date.today()
        month_names_genitive = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        current_month_key = norm(f'{month_names_genitive[now.month - 1]}{now.year}')
        current_month_label = f'{month_names_genitive[now.month - 1]} {now.year}'

        totals = {rule['label']: 0.0 for rule in rules}
        limits = {rule['label']: rule['limit'] for rule in rules}
        for row in dds_rows[4:]:
            # D = сумма, G = контрагент, K = статья, Z = месяц.
            if len(row) <= 25:
                continue
            amount = parse_amount(row[3])
            month_value = norm(row[25])
            if amount >= 0 or month_value != current_month_key:
                continue
            article = norm(row[10])
            counterparty = norm(row[6])
            for rule in rules:
                if article != rule['article']:
                    continue
                if rule['counterparty'] and counterparty != rule['counterparty']:
                    continue
                totals[rule['label']] += abs(amount)
                break

        # Последняя дата операции с деньгами из столбца C (индекс 2) листа ДДС
        last_dds_date = ''
        for row in reversed(dds_rows):
            if len(row) > 2 and row[2].strip():
                val = row[2].strip().replace('\u00a0', ' ')
                try:
                    datetime.strptime(val, '%d.%m.%Y')
                    last_dds_date = val
                    break
                except ValueError:
                    pass

        return [
            {
                'label': label,
                'spent': amount,
                'limit': limits.get(label, 0.0),
            }
            for label, amount in totals.items()
        ], sum(totals.values()), current_month_label, last_dds_date
    except Exception:
        return [], 0.0, '', ''


@st.cache_data(ttl=600, show_spinner=False)
def load_opiu():
    """Загрузка ОПИУ."""
    url = 'https://docs.google.com/spreadsheets/d/1rXm66oriSs533ghAe4PNi6ze28P-lVPxVUJ63JOKcc0/export?format=csv&gid=0'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    lines = raw.split('\n')

    def parse_num(s):
        s = s.strip().replace('\r', '').replace('"', '')
        if not s:
            return 0.0
        s = s.replace(' ', '').replace('\u00A0', '').replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return 0.0

    header_idx = None
    for i, line in enumerate(lines):
        if 'ОПИУ свод укрупненно' in line:
            header_idx = i
            break
    if header_idx is None:
        return None

    revenue = [parse_num(v) for v in lines[header_idx + 2].split(',')[1:]]
    overruns = [parse_num(v) for v in lines[header_idx + 9].split(',')[1:]]
    eat = [parse_num(v) for v in lines[header_idx + 12].split(',')[1:]]
    eat_v1 = [parse_num(v) for v in lines[header_idx + 21].split(',')[1:]]
    eat_v2 = [parse_num(v) for v in lines[header_idx + 22].split(',')[1:]]

    import csv as _csv
    v3_reader = _csv.reader(io.StringIO(lines[header_idx + 23]))
    v3_row = next(v3_reader)
    eat_v3 = [parse_num(v) for v in v3_row[1:]]

    months_2026 = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']

    return {
        'revenue': revenue,
        'overruns': overruns,
        'eat': eat,
        'eat_v1': eat_v1,
        'eat_v2': eat_v2,
        'eat_v3': eat_v3,
        'months_2026': months_2026,
    }


@st.cache_data(ttl=600, show_spinner=False)
def load_wallets():
    """Загрузка остатков по кошелькам."""
    import csv as csv_module
    url = 'https://docs.google.com/spreadsheets/d/1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw/export?format=csv&gid=0'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    def parse_num(s):
        s = s.strip().replace('\r', '').replace('"', '')
        if not s:
            return 0.0
        s = s.replace(' ', '').replace('\u00A0', '').replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return 0.0

    reader = csv_module.reader(io.StringIO(raw))
    rows = list(reader)

    def canonical_wallet_name(name):
        text = str(name).strip().lower().replace('ё', 'е')
        text = re.sub(r'["“”„«»]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if 'райф' in text:
            return 'Рас/счет "Райф"'
        # Не путать рабочий счёт Точка с «Копилка налоги Точка».
        if 'точка' in text and ('рас/счет' in text or 'расчет' in text):
            return 'Рас/счет 2 Точка'
        if text == 'рас/счет':
            return 'Рас/счет'
        if text == 'карта':
            return 'Карта'
        if text == 'резервный фонд':
            return 'Резервный фонд'
        if text == 'копилка':
            return 'Копилка'
        if text == 'цифра банк р/с':
            return 'Цифра банк р/с'
        return str(name).strip().strip('"')

    wallets = {}
    allowed_wallets = {
        'Рас/счет', 'Карта', 'Цифра банк р/с', 'Рас/счет 2 Точка',
        'Рас/счет "Райф"', 'Резервный фонд', 'Копилка',
    }
    for row_idx in range(min(3, len(rows))):
        row = rows[row_idx]
        i = 0
        while i < len(row) - 1:
            raw_name = row[i].strip().replace('\u00A0', ' ')
            val_text = row[i + 1] if i + 1 < len(row) else ''
            val = parse_num(val_text)
            if raw_name and raw_name != 'Итого' and val_text.strip() not in ('', 'nan'):
                name = canonical_wallet_name(raw_name)
                if name in allowed_wallets and name not in wallets:
                    wallets[name] = val
            i += 1
    return wallets


@st.cache_data(ttl=600, show_spinner=False)
def load_money_calendar():
    """
    Календарь «Привлечь деньги» из DEV-таблицы, раздел БЛОК СТАТИСТИКА ПРИХОДОВ.
    Возвращает {день: сумма} и сумму на следующий месяц.
    """
    access_token = _get_google_token()
    if not access_token:
        return {}, 0, {}

    DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
    DEV_SHEET_GID = 1010682300

    try:
        # Sheet name
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())

        sheet_name = None
        for s in info.get('sheets', []):
            if s['properties']['sheetId'] == DEV_SHEET_GID:
                sheet_name = s['properties']['title']
                break
        if not sheet_name:
            return {}, 0, {}

        encoded_name = urllib.parse.quote(sheet_name, safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}/values/{encoded_name}'
        req = urllib.request.Request(values_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            values_data = json.loads(resp.read())
        rows_val = values_data.get('values', [])

    except Exception:
        return {}, 0, {}

    def safe_val(r, c):
        if r < len(rows_val) and c < len(rows_val[r]):
            return rows_val[r][c].strip()
        return ''

    def parse_num(s):
        s = s.strip().replace('\u00A0', ' ').replace('"', '').replace(' ', '').replace(',', '.')
        try:
            return int(float(s))
        except ValueError:
            return 0

    stats_start = None
    for r in range(len(rows_val)):
        combined = (safe_val(r, 0) + ' ' + safe_val(r, 1)).upper()
        if 'БЛОК СТАТИСТИКА' in combined:
            stats_start = r + 2
            break

    if not stats_start:
        return {}, 0, {}

    today = date.today()
    money_cal = {}
    money_details = {}
    money_next = 0

    for r in range(stats_start, len(rows_val)):
        proj_name = safe_val(r, 1)
        if not proj_name or 'ИТОГО' in safe_val(r, 0).upper():
            break
        amount = parse_num(safe_val(r, 2))
        date_str = safe_val(r, 8)
        status = safe_val(r, 4)
        if amount > 0 and date_str:
            parts = date_str.split('.')
            if len(parts) >= 1:
                try:
                    day = int(parts[0])
                    mon = int(parts[1]) if len(parts) > 1 else today.month
                    detail = {
                        'amount': amount,
                        'project': proj_name,
                        'status': status,
                        'reason': safe_val(r, 3),
                        'received': 'оплачено' in status.lower(),
                    }
                    if mon == today.month:
                        if 'оплачено' not in status.lower():
                            money_cal[day] = money_cal.get(day, 0) + amount
                        money_details.setdefault(day, []).append(detail)
                    else:
                        if 'оплачено' not in status.lower():
                            money_next += amount
                except ValueError:
                    pass

    return money_cal, money_next, money_details


@st.cache_data(ttl=600, show_spinner=False)
def load_receipts_data():
    """Календарь «Реализация» + процент выполнения + детализация по проектам."""
    receipts_cal = {}
    receipt_details = {}
    pct_complete = 0
    try:
        RECEIPTS_URL = (
            'https://docs.google.com/spreadsheets/d/'
            '11f_FJivwUEPxEF2QgHExdo1O1QBllLjNcY_dfsz_ac4'
            '/export?format=csv&gid=2015821513'
        )
        req = urllib.request.Request(RECEIPTS_URL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(raw))
        rows = list(reader)

        def col(r, i):
            if r >= len(rows) or i >= len(rows[r]):
                return ''
            return rows[r][i].strip().replace('\u00A0', ' ')

        # Percentage — ищем строку «Выполнение плана»
        pct_complete = 0
        for r in range(len(rows)):
            c0 = col(r, 1)
            if 'выполнение плана' in c0.lower():
                pct_str = col(r, 4).replace('%', '').strip()
                try:
                    pct_complete = float(pct_str.replace(',', '.'))
                except ValueError:
                    pct_complete = 0
                break

        # Структура листа «Приходы»: дата плана в col1, фактическая дата
        # получения в col2, проверка получения в col3, сумма в col4.
        # Раньше здесь дополнительно требовалось TRUE в col0. В актуальном листе
        # этот служебный признак не заполняется, из-за чего вся «Реализация»
        # исчезала из календаря. Отбираем строки по фактическим данным, не меняя
        # логику краткого и детального режимов.
        # Начинаем после строки с названиями колонок и строки с номерами полей,
        # чтобы не принять служебную строку «1 / 2 / 3 / 4» за приход.
        data_start = 6
        for idx, row in enumerate(rows):
            if len(row) > 1 and 'план дата получения' in row[1].strip().lower():
                data_start = idx + 2
                break
        for r in range(data_start, len(rows)):
            if len(rows[r]) < 6:
                continue
            plan_date = rows[r][1].strip() if len(rows[r]) > 1 else ''
            actual_date = rows[r][2].strip() if len(rows[r]) > 2 else ''
            received = rows[r][3].strip().lower() if len(rows[r]) > 3 else ''
            amount_str = (
                rows[r][4].strip()
                .replace('\u00a0', ' ').replace('"', '').replace(' ', '').replace(',', '.')
                if len(rows[r]) > 4 else '0'
            )
            try:
                amount = int(float(amount_str))
            except ValueError:
                amount = 0
            if amount <= 0:
                continue

            # Полученные деньги показываем по фактической дате, планируемые —
            # по плановой. Так строка с фактом без даты плана не теряется.
            event_date = actual_date if received == 'да' and actual_date else plan_date
            if not event_date or event_date.lower() == 'без даты':
                continue
            try:
                day = int(event_date)
            except ValueError:
                continue

            # В краткий календарь попадают только неполученные суммы.
            # В детальном режиме показываем и полученные, и планируемые строки.
            if received != 'да':
                receipts_cal[day] = receipts_cal.get(day, 0) + amount

            project = rows[r][8].strip() if len(rows[r]) > 8 else ''
            deal_type = rows[r][9].strip() if len(rows[r]) > 9 else ''
            supplier = rows[r][11].strip() if len(rows[r]) > 11 else ''
            description = rows[r][12].strip() if len(rows[r]) > 12 else ''
            direction = rows[r][5].strip() if len(rows[r]) > 5 else ''
            details_text = ' · '.join(x for x in (project, supplier, description) if x)
            if details_text:
                receipt_details.setdefault(day, []).append({
                    'amount': amount,
                    'project': project or 'Реализация',
                    'deal_type': deal_type,
                    'supplier': supplier,
                    'description': description,
                    'direction': direction,
                    'received': received == 'да',
                })
    except Exception:
        pass
    return receipts_cal, pct_complete, receipt_details


@st.cache_data(ttl=600, show_spinner=False)
def load_expenses_calendar():
    """Календарь расходов."""
    expenses_cal = {}
    month = date.today().month
    year = date.today().year
    try:
        EXP_URL = (
            'https://docs.google.com/spreadsheets/d/'
            '14FFru1xtbOtcLDkjLC-t-Nawy9jPnHrcm-1KZ6coZiU'
            '/export?format=csv'
        )
        req = urllib.request.Request(EXP_URL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(raw))
        rows = list(reader)

        try:
            month = int(rows[0][3].strip()) if len(rows[0]) > 3 else date.today().month
        except (ValueError, IndexError):
            month = date.today().month
        try:
            year = int(rows[0][4].strip()) if len(rows[0]) > 4 else date.today().year
        except (ValueError, IndexError):
            year = date.today().year

        for row in rows:
            if len(row) > 19:
                day_cal = row[16].strip()
                try:
                    day_num = int(day_cal)
                except ValueError:
                    continue
                exp_str = row[17].strip().replace('\u00a0', ' ').replace(',', '.').replace(' ', '')
                try:
                    expense = float(exp_str) if exp_str else 0
                except ValueError:
                    expense = 0
                if expense > 0:
                    expenses_cal[day_num] = int(expense)
    except Exception:
        pass
    return expenses_cal, month, year


@st.cache_data(ttl=600, show_spinner=False)
def load_ar_total():
    """Загрузка итоговой суммы дебиторской задолженности."""
    try:
        AR_URL = (
            'https://docs.google.com/spreadsheets/d/'
            '14FFru1xtbOtcLDkjLC-t-Nawy9jPnHrcm-1KZ6coZiU'
            '/export?format=csv&gid=1273919189'
        )
        req = urllib.request.Request(AR_URL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        reader = csv.reader(io.StringIO(raw))
        rows = list(reader)

        def parse_num(s):
            s = s.strip().replace('\u00A0', ' ').replace('"', '').replace(' ', '').replace(',', '.')
            try:
                return int(float(s))
            except ValueError:
                return 0

        if rows and len(rows[0]) > 6:
            return parse_num(rows[0][6])
    except Exception:
        pass
    return 0


@st.cache_data(ttl=600, show_spinner=False)
def load_dev_kpi():
    """Загрузка KPI из DEV-таблицы: процент выполнения разработки и привлечения денег."""
    access_token = _get_google_token()
    if not access_token:
        return 0, 0

    DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
    DEV_SHEET_GID = 1010682300

    try:
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())

        sheet_name = None
        for s in info.get('sheets', []):
            if s['properties']['sheetId'] == DEV_SHEET_GID:
                sheet_name = s['properties']['title']
                break
        if not sheet_name:
            return 0, 0

        encoded_name = urllib.parse.quote(sheet_name, safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}/values/{encoded_name}'
        req = urllib.request.Request(values_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            values_data = json.loads(resp.read())
        rows_val = values_data.get('values', [])

    except Exception:
        return 0, 0

    def safe_val(r, c):
        if r < len(rows_val) and c < len(rows_val[r]):
            return rows_val[r][c].strip()
        return ''

    def parse_pct(s):
        s = s.strip().replace('%', '').replace(',', '.').replace('\u00A0', ' ')
        try:
            return float(s)
        except ValueError:
            return 0

    dev_pct = 0
    money_pct = 0

    for r in range(len(rows_val)):
        c1 = safe_val(r, 1).upper()
        if 'KPI 1' in c1:
            dev_pct = parse_pct(safe_val(r, 3))
        if 'KPI 2' in c1:
            money_pct = parse_pct(safe_val(r, 3))

    return dev_pct, money_pct


@st.cache_data(ttl=600, show_spinner=False)
def load_dev_month_label():
    """Получает текущий месяц из той же DEV-таблицы, что и страница «Планы»."""
    access_token = _get_google_token()
    if not access_token:
        return ''
    DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
    DEV_SHEET_GID = 1010682300
    try:
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())
        sheet_name = None
        for sheet in info.get('sheets', []):
            if sheet.get('properties', {}).get('sheetId') == DEV_SHEET_GID:
                sheet_name = sheet['properties'].get('title')
                break
        if not sheet_name:
            return ''
        encoded_name = urllib.parse.quote(sheet_name, safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}/values/{encoded_name}'
        req = urllib.request.Request(values_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows_val = json.loads(resp.read()).get('values', [])
        if len(rows_val) > 1 and len(rows_val[1]) > 1:
            return rows_val[1][1].strip()
    except Exception:
        pass
    return ''


@st.cache_data(ttl=600, show_spinner=False)
def load_plan_facts():
    """Загружает фактические суммы из тех же детализаций, что и страница «Планы»."""
    result = {'dev_fact': 0, 'money_fact': 0, 'receipts_fact': 0}

    # Разработка и Привлечь деньги: закрытые зелёные ячейки листа Разработка.
    access_token = _get_google_token()
    if access_token:
        DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
        DEV_SHEET_GID = 1010682300
        try:
            meta_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
            req = urllib.request.Request(meta_url)
            req.add_header('Authorization', f'Bearer {access_token}')
            with urllib.request.urlopen(req, timeout=30) as resp:
                info = json.loads(resp.read())

            sheet_name = None
            sheet_index = 0
            for idx, sheet in enumerate(info.get('sheets', [])):
                if sheet.get('properties', {}).get('sheetId') == DEV_SHEET_GID:
                    sheet_name = sheet['properties'].get('title')
                    sheet_index = idx
                    break

            if sheet_name:
                encoded_name = urllib.parse.quote(sheet_name, safe='')
                values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}/values/{encoded_name}'
                req = urllib.request.Request(values_url)
                req.add_header('Authorization', f'Bearer {access_token}')
                with urllib.request.urlopen(req, timeout=30) as resp:
                    rows_val = json.loads(resp.read()).get('values', [])

                range_param = urllib.parse.quote(f"'{sheet_name}'")
                fmt_url = (
                    f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
                    f'?includeGridData=true&ranges={range_param}'
                )
                req = urllib.request.Request(fmt_url)
                req.add_header('Authorization', f'Bearer {access_token}')
                with urllib.request.urlopen(req, timeout=30) as resp:
                    fmt_data = json.loads(resp.read())

                rows_fmt = []
                try:
                    rows_fmt = fmt_data['sheets'][0]['data'][0].get('rowData', [])
                except (KeyError, IndexError, TypeError):
                    pass

                def safe_val(r, c):
                    if r < len(rows_val) and c < len(rows_val[r]):
                        return rows_val[r][c].strip()
                    return ''

                def parse_num(value):
                    value = str(value).strip().replace('\u00A0', ' ').replace('"', '')
                    if not value or value in ('—', '-'):
                        return 0
                    try:
                        return int(float(value.replace(' ', '').replace(',', '.')))
                    except ValueError:
                        return 0

                def is_green_cell(r, c):
                    if r >= len(rows_fmt) or c >= len(rows_fmt[r].get('values', [])):
                        return False
                    fmt = rows_fmt[r]['values'][c].get('effectiveFormat', {})
                    bg = fmt.get('backgroundColor', {})
                    red = bg.get('red', 0) or 0
                    green = bg.get('green', 0) or 0
                    blue = bg.get('blue', 0) or 0
                    return green > 0.85 and green > red and green > blue

                def section_fact(marker):
                    start_row = None
                    for r in range(len(rows_val)):
                        if marker in safe_val(r, 1).upper():
                            start_row = r + 2
                            break
                    if start_row is None:
                        return 0

                    total_fact = 0
                    for r in range(start_row, len(rows_val)):
                        project = safe_val(r, 1)
                        if not project:
                            if r > start_row + 1:
                                break
                            continue
                        upper = project.upper()
                        if 'KPI' in upper or 'ВНЕ ПЛАНА' in upper or 'БЛОК СТАТИСТИКА' in upper:
                            break
                        stage_total = sum(parse_num(safe_val(r, c)) for c in range(5, 11))
                        if stage_total <= 0:
                            continue
                        total_fact += sum(
                            parse_num(safe_val(r, c))
                            for c in range(5, 11)
                            if is_green_cell(r, c)
                        )
                    return total_fact

                result['dev_fact'] = section_fact('ИСПОЛНИТЬ ОБЯЗАТЕЛЬСТВА')
                result['money_fact'] = section_fact('ПРИВЛЕЧЬ АВАНСЫ')
        except Exception:
            pass

    # Реализация: итоговая строка «Получено» из того же листа «Приходы».
    try:
        receipts_url = (
            'https://docs.google.com/spreadsheets/d/'
            '11f_FJivwUEPxEF2QgHExdo1O1QBllLjNcY_dfsz_ac4'
            '/export?format=csv&gid=2015821513'
        )
        req = urllib.request.Request(receipts_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            rows = list(csv.reader(io.StringIO(resp.read().decode('utf-8', errors='replace'))))

        def col(r, c):
            if r < len(rows) and c < len(rows[r]):
                return rows[r][c].strip().replace('\u00A0', ' ')
            return ''

        for r in range(4, len(rows)):
            if 'получено' in col(r, 1).lower():
                value = col(r, 4).replace(' ', '').replace(',', '.')
                try:
                    result['receipts_fact'] = int(float(value))
                except ValueError:
                    result['receipts_fact'] = 0
                break
    except Exception:
        pass

    return result


@st.cache_data(ttl=600, show_spinner=False)
def load_plan_summary():
    """Загружает карточки I и II из того же листа, что и страница «Планы».

    Источник I и II: закрытый лист «Разработка» через Google Sheets API.
    Это важно: именно там лежат итоговые строки руководителя и значения
    «перешло / новое», которые видит пользователь на странице «Планы».
    """
    DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
    DEV_SHEET_GID = 1010682300

    def clean(value):
        return str(value or '').strip().replace('\u00A0', ' ')

    def parse_num(value):
        value = clean(value).replace('"', '')
        if not value or value in ('—', '-'):
            return 0
        try:
            return int(float(value.replace(' ', '').replace(',', '.')))
        except ValueError:
            return 0

    def col(rows, row_idx, col_idx):
        if row_idx < 0 or row_idx >= len(rows) or col_idx >= len(rows[row_idx]):
            return ''
        return clean(rows[row_idx][col_idx])

    def load_dev_rows():
        access_token = _get_google_token()
        if not access_token:
            return []
        meta_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}'
        req = urllib.request.Request(meta_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())
        sheet_name = next(
            (sheet['properties']['title'] for sheet in info.get('sheets', [])
             if sheet.get('properties', {}).get('sheetId') == DEV_SHEET_GID),
            ''
        )
        if not sheet_name:
            return []
        encoded_name = urllib.parse.quote(sheet_name, safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{DEV_SHEET_ID}/values/{encoded_name}'
        req = urllib.request.Request(values_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()).get('values', [])

    def find_kpi(rows, label):
        label = label.upper()
        for row_idx, row in enumerate(rows):
            if label in col(rows, row_idx, 1).upper():
                return row_idx
        return -1

    def parse_dev_card(rows, kpi_label, next_kpi_label=''):
        start = find_kpi(rows, kpi_label)
        if start < 0:
            return {'total': 0, 'carry': 0, 'new': 0}
        end = find_kpi(rows, next_kpi_label) if next_kpi_label else len(rows)
        if end < 0:
            end = len(rows)

        total = 0
        carry = 0
        new = 0
        for row_idx in range(start, end):
            # Итог карточки находится в строке после «руководитель», колонка C.
            if col(rows, row_idx, 1).lower() == 'руководитель':
                total = parse_num(col(rows, row_idx + 1, 2))
                break
        for row_idx in range(start, end):
            if 'перешло с прошл' in col(rows, row_idx, 8).lower():
                carry = parse_num(col(rows, row_idx + 1, 8))
                new = parse_num(col(rows, row_idx + 1, 9))
                break

        # Во II блоке разбивка вынесена в отдельную строку:
        # колонки I и J = «перешло» и «новое», колонка K = итог.
        if carry == 0 and new == 0:
            for row_idx in range(start, end):
                candidate_carry = parse_num(col(rows, row_idx, 8))
                candidate_new = parse_num(col(rows, row_idx, 9))
                candidate_total = parse_num(col(rows, row_idx, 10))
                if candidate_carry > 0 and candidate_new > 0 and candidate_total == total:
                    carry = candidate_carry
                    new = candidate_new
                    break
        return {'total': total, 'carry': carry, 'new': new}

    try:
        dev_rows = load_dev_rows()
        if not dev_rows:
            return None

        dev = parse_dev_card(dev_rows, 'KPI 1', 'KPI 2')
        money = parse_dev_card(dev_rows, 'KPI 2')
        month_label = col(dev_rows, 1, 1)
        if month_label:
            month_label = f'План на месяц · {month_label}'

        # III блок: план по реализации — ячейка K2 листа «Приходы»
        # исходный файл: 11f_FJivwUEPxEF2QgHExdo1O1QBllLjNcY_dfsz_ac4, gid=2015821513
        agent_total = 0
        receipts_url = ('https://docs.google.com/spreadsheets/d/'
                        '11f_FJivwUEPxEF2QgHExdo1O1QBllLjNcY_dfsz_ac4'
                        '/export?format=csv&gid=2015821513')
        req = urllib.request.Request(receipts_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as resp:
            real_rows = list(csv.reader(io.StringIO(resp.read().decode('utf-8', errors='replace'))))
        # K2 = строка 2 (индекс 1), колонка K (индекс 10)
        if len(real_rows) > 1 and len(real_rows[1]) > 10:
            agent_total = parse_num(real_rows[1][10])

        return {
            'month_label': month_label,
            'dev': dev,
            'money': money,
            'agent': {'total': agent_total},
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
# LOAD ALL DATA
# ═══════════════════════════════════════════════════════
opiu = load_opiu()
wallets_raw = load_wallets()
expenses_control, expenses_control_total, expenses_control_month, last_dds_date = load_expenses_control()
money_cal, money_next, money_details = load_money_calendar()
receipts_cal, receipts_pct, receipt_details = load_receipts_data()
expenses_cal, cal_month, cal_year = load_expenses_calendar()
plan_data = load_plan_summary()
car_progress = load_car_progress()
plan_facts = load_plan_facts()
ar_total = load_ar_total()
dev_kpi_pct, money_kpi_pct = load_dev_kpi()
today = date.today()

if opiu is None:
    st.error("Не удалось загрузить ОПИУ. Проверьте Google Sheets.")
    st.stop()

# ── Compute current month values ──────────────────────
revenue = opiu['revenue']
eat = opiu['eat']
overruns = opiu['overruns']
eat_v1 = opiu['eat_v1']
eat_v2 = opiu['eat_v2']
eat_v3 = opiu['eat_v3']
months_2026 = opiu['months_2026']

# Если ОПИУ содержит несколько лет, выбираем последний заполненный месяц 2026 года.
# Индекс колонки ОПИУ: 2025 занимает 0-12, 2026 начинается с 13.
current_month_idx = 0
if len(revenue) > 13:
    for i in range(len(revenue) - 1, 12, -1):
        if revenue[i] != 0:
            current_month_idx = i
            break

if current_month_idx == 0:
    for i in range(len(revenue) - 1, -1, -1):
        if revenue[i] != 0:
            current_month_idx = i
            break

current_revenue = revenue[current_month_idx] if current_month_idx < len(revenue) else 0
current_eat = eat[current_month_idx] if current_month_idx < len(eat) else 0
current_overruns = overruns[current_month_idx] if current_month_idx < len(overruns) else 0
eat_v1_cur = eat_v1[current_month_idx] if current_month_idx < len(eat_v1) else 0
eat_v2_cur = eat_v2[current_month_idx] if current_month_idx < len(eat_v2) else 0
eat_v3_cur = eat_v3[current_month_idx] if current_month_idx < len(eat_v3) else 0

if 13 <= current_month_idx < 25:
    month_num = current_month_idx - 12
    current_month_names = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
    current_month_label = f"{current_month_names[month_num - 1]} 2026"
else:
    current_month_label = "2026"

# ── Wallets ───────────────────────────────────────────
MAIN_WALLETS = [
    'Рас/счет', 'Карта', 'Цифра банк р/с', 'Рас/счет 2 Точка',
    'Рас/счет "Райф"', 'Резервный фонд', 'Копилка',
]

def wallet_value(*names):
    for name in names:
        if name in wallets_raw:
            return wallets_raw[name]
    return 0

main_wallets = {
    'Рас/счет': wallet_value('Рас/счет'),
    'Карта': wallet_value('Карта'),
    'Цифра банк р/с': wallet_value('Цифра банк р/с'),
    'Рас/счет 2 Точка': wallet_value('Рас/счет 2 Точка', 'Рас/счет 2 "Точка"'),
    'Рас/счет "Райф"': wallet_value(
        'Рас/счет "Райф"',
        'Рас/счет "Райф',
        'Расчет "Райф"',
        'Расчёт Райф',
        'Расчет Райф',
        'Расчетный счет Райф',
        'Расчётный счёт Райф',
    ),
    'Резервный фонд': wallet_value('Резервный фонд'),
    'Копилка': wallet_value('Копилка'),
}
total_cash = sum(main_wallets.values())
working_wallets = {
    k: v for k, v in main_wallets.items()
    if k in ['Рас/счет', 'Карта', 'Цифра банк р/с', 'Рас/счет 2 Точка', 'Рас/счет "Райф"']
}
fund_wallets = {k: v for k, v in main_wallets.items() if k in ['Резервный фонд', 'Копилка']}
working_total = sum(working_wallets.values())
fund_total = sum(fund_wallets.values())

# ── Calendar month name ───────────────────────────────
month_names = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]
cal_month_name = month_names[cal_month - 1]

# ── Helpers ───────────────────────────────────────────
def fmt_rub(val):
    if abs(val) < 1000:
        return f"{int(val):,} ₽".replace(',', ' ')
    if abs(val) < 1_000_000:
        return f"{int(val):,} ₽".replace(',', ' ')
    m = val / 1_000_000
    return f"{m:.1f} млн ₽".replace('.', ',')


def fmt_rub_short(val):
    if abs(val) < 1000:
        return f"{int(val):,} ₽".replace(',', ' ')
    if abs(val) < 1_000_000:
        return f"{int(val):,} ₽".replace(',', ' ')
    m = val / 1_000_000
    return f"{m:.2f} млн ₽".replace('.', ',').replace('.', ',')


def clean_period_label(label):
    """Оставляет только месяц и год для крупной подписи дашборда."""
    label = (label or '').strip()
    prefix = 'План на месяц ·'
    if label.startswith(prefix):
        label = label[len(prefix):].strip()
    return label or f"{cal_month_name} {cal_year}"


dashboard_period = clean_period_label(plan_data.get('month_label') if plan_data else '')

# ═══════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════

# ── Header ────────────────────────────────────────────
st.markdown(f"""
<div class="hero-title">
    <img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:10px;">
    Ключевые показатели студии
</div>
<div class="hero-subtitle">
    {dashboard_period}
</div>
""", unsafe_allow_html=True)

CAR_IMAGE_DATA = "data:image/jpeg;base64,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jiexLdxunj6eCk0zwSNzIak4VKZGiCWZUhsaFxYV2giUmxQqIbFFgmyCPKHTyV129hqujtE50X3yJV3OjhEvVbb6FH9O9TEbS+Cbm+fkfvAhJ+S2ZB334xGUqtm/QSRrJ01zLiNkEBkhoLNs5In9A2iIXIoduAbmLNhOMDQ9RuYpAvyTUBy0LIa7kFiDckqzU8yf6jIRYyBUy4CrAJwRqRXQkjp0RX8+RHcqmZjWfMaQXT6k16QfoQetxF6BfcZDQ/Avcy/wMCZa419lbBuq/IlRmb0jqJp6gUIbKHSfnybHJotV36e47FqCascy5mLJzYyWEkPJGmD7EHsMeFreo1nqqDN7ThnCwnbJM7ep8Fd2dJH9/Jmcl/kzeV8x9Q5qOTk/C+p+v14agZH0HwR9L8EfS/BH0/wR9L8EfQfBH1Xxwx+P1Pw+pP4fY/ofg+6L7/5DJ5r/ACRVl/tzK2UjabaO+0Hfk9wySybiw+xE1yWbsEWginAq42kCZ0UvV1GwUZnlhy3u32+3lF5b2Q5yGmroxaFRo4LiSs2JHzFBOUVqPDk1mRzH6gngknmNhCyIRAhkQIECBAh4wIECBAgQIEMjYSyZtCWaJBa3QTYnZldV6yiUt3zFXdjNOnAlUvJkSFCyeUWg9LUu8RUOohVz2D6pwA03Y1mJfC0yeRIlkSJEyZMnwbTabTYbDYbDYbDYbDYbDYbDYbDYbCRIkSJEzSNEmUQNZTLXULB6hkiz3WM3KNGpkReUaJCbAmwJMB6B6B6R6BtkNsjQNI0jQNI0jQNE0zTNE0TRNM0zTNM0zSNI0jQNA0jSNI0DQNI0jQJZE8ieQtAtBoiTIS5C0i0C0CwsJeZghECJEgQyNI0jQRoGkbBoGkaRpGgaCNBGgjQNI0DQNBGgjQRpI0jSRoGgaRpeArQIECJAgR/2l//aAAwDAQACAAMAAAAQ888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888kYg8YYgUYI88M888888888888888888888888o9IERxB5N2S27f9M8888888888888888888888ZNB9u/DfXDHRJxZ3U88888888888888884w8scd9eq62bbr2SZp+9Z9U4w0888888888884YYUQp6CC69qFpNN5p15hZKooAM08888888888s8sYcdNtVFt5wgAQ95hxNcxs8I8c88888888884swc8sw8YUE0oww8ws80s8w0gcM8888888888844oc8cQk8s840sAUo8Y4oocMwUMw8888888888U4o4Qw8Y8M0s0sIM888IMcIoY8o088888888880c08IkU8oAAIQg04wkEwgcIscos88888888888c480c4AcsM084AAEsMMMYAYcME8I88888888880w04Ucs0sswwgoM400c8I4k88kMs88888888880Eg44gwYNss4kssE8oU4scUAsw4s8888888888U80YIcIAc08cMcw0sgw8kgskIQYM8888888888o4g0UMU44w0css8MU4okoQYkMcs8888888888scoocAccYYQ08owskc88Y444Is88o88888888888ME8cswkcQgwU4AM4Aocoscok8U08888888884Q4c4Mc44U88wwwwwww88cUMYUQs8U888888888s80448o4MEkoUM88kQ4cYY88oQ8c88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888888//xAAeEQADAAEEAwAAAAAAAAAAAAAAAREQIEBQgCEwcP/aAAgBAwEBPxD5PS4pdFLxC3kIiIiIRLgV61toQhMToP4l1vf/xAAYEQEBAQEBAAAAAAAAAAAAAAARAIBBcP/aAAgBAgEBPxD3VmZnJy7m/wD/xAArEAEAAgECBQMFAQEBAQEAAAABABEhMVFBYXGBkaGx0RBAweHw8VAgMID/2gAIAQEAAT8Q/wD22oGcS6wWwS6yjhb2RBBJsfM9tMQWn3U4CeX6JRuiO34n6M+IjQHYivGdIvr55/twennm/wDrD6r1E9kJKdM50/MP8NRtdkv+J+M5jFEouFh3X3Qjw2/9Ee444i2Jd0Lug5sMpocLYmIf3TXG7xbjFbxe8VvHmjz/AEqbPMruTlPM5TzKbfMOR5g4tvB7wW8FvBQppD2Ed5p/OrDgrmhZlI+k6CH5h0R2Jw5f80ax9OK2JUkuLyfNEWgcwe8DqHu/EDx7BYPx8FQT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"

# ── Временная шкала цели «Машина» ─────────────────────
slider_left = 2.0 + car_progress * 0.90
st.markdown(f"""
<div class="car-progress-wrap" aria-label="Положение на временной шкале цели Машина">
    <div class="car-progress-track">
        <div class="car-progress-line"></div>
        <div class="car-progress-slider" style="left:{slider_left:.2f}%;"></div>
        <img class="car-progress-image" src="{CAR_IMAGE_DATA}" alt="Машина">
    </div>
</div>
""", unsafe_allow_html=True)

# ── БЛОК 1: План на месяц ─────────────────────────────
if plan_data:
    st.markdown('<div class="section-title">▸ План на месяц</div>', unsafe_allow_html=True)
    dev, money, agent = plan_data['dev'], plan_data['money'], plan_data['agent']
    def pct_color(value):
        if value < 50: return ORANGE
        if value <= 80: return WARNING
        return SUCCESS
    p1, p2, p3 = st.columns(3)
    plan_cards = [
        ('I. Разработка', dev['total'], dev.get('carry', 0), dev.get('new', 0), dev_kpi_pct, plan_facts.get('dev_fact', 0), 'закрыть этапы'),
        ('II. Привлечь деньги', money['total'], money.get('carry', 0), money.get('new', 0), money_kpi_pct, plan_facts.get('money_fact', 0), 'поступления'),
        ('III. Реализация', agent['total'], None, None, receipts_pct, plan_facts.get('receipts_fact', 0), 'агентские / перепродажи'),
    ]
    for column, (title, total, carry, new, pct, fact, subtitle) in zip((p1, p2, p3), plan_cards):
        with column:
            extra = ''
            if carry is not None and new is not None:
                extra = f'<div class="plan-card-sm-sub">перешло: {fmt_rub(carry)} · новое: {fmt_rub(new)}</div>'
            st.markdown(f"""
            <div class="plan-card-sm">
                <div class="plan-card-sm-title">{title}</div>
                <div class="plan-card-sm-pct-row">
                    <div class="plan-card-sm-pct" style="color:{pct_color(pct)}">{pct:.1f}%</div>
                    <div class="plan-card-sm-fact">{fmt_rub(fact)} факт</div>
                </div>
                <div class="plan-card-sm-val">план: {fmt_rub(total)}</div>
                <div class="plan-card-sm-sub">{subtitle}</div>
                {extra}
            </div>
            """, unsafe_allow_html=True)

st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

# ── БЛОК 2: Дебиторская задолженность и счета ──────────
st.markdown('<div class="section-title">▸ Деньги бизнеса</div>', unsafe_allow_html=True)
debt_col, accounts_col = st.columns([1, 2.4])
with debt_col:
    st.markdown(f"""
    <div class="debt-card">
        <div class="wallet-header">📋 Дебиторская задолженность</div>
        <div class="debt-value">{fmt_rub(ar_total)}</div>
        <div class="metric-detail">сумма, которую должны получить от заказчиков</div>
    </div>
    """, unsafe_allow_html=True)
with accounts_col:
    ac1, ac2 = st.columns(2)
    with ac1:
        st.markdown(f"""
        <div class="wallet-block">
            <div class="wallet-header">💼 Рабочие счета</div>
            <div class="wallet-total">{fmt_rub(working_total)}</div>
            {"".join(f'<div class="wallet-row"><span class="wallet-name">{n}</span><span class="wallet-amount">{fmt_rub(v)}</span></div>' for n, v in working_wallets.items())}
        </div>
        """, unsafe_allow_html=True)
    with ac2:
        st.markdown(f"""
        <div class="wallet-block">
            <div class="wallet-header">🏦 Фонды бизнеса</div>
            <div class="wallet-total">{fmt_rub(fund_total)}</div>
            {"".join(f'<div class="wallet-row"><span class="wallet-name">{n}</span><span class="wallet-amount">{fmt_rub(v)}</span></div>' for n, v in fund_wallets.items())}
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

# ── БЛОК 3: Расходы на контроле ────────────────────────
if expenses_control:
    control_month = expenses_control_month or cal_month_name + ' ' + str(cal_year)
    date_suffix = f" · актуально на {last_dds_date}" if last_dds_date else ""
    control_rows_html = ''
    for item in expenses_control:
        label = item['label']
        spent = item['spent']
        limit = item['limit']
        over_limit = spent > limit > 0
        remaining = max(limit - spent, 0)
        overrun = max(spent - limit, 0)
        pct = (spent / limit * 100) if limit > 0 else 0
        pct_label = 'свыше лимита' if over_limit else f'{pct:.0f}%'
        balance_label = (
            f'<span class="control-overrun">перерасход {fmt_rub(overrun)}</span>'
            if over_limit
            else f'<span class="control-remaining">осталось {fmt_rub(remaining)}</span>'
        )
        control_rows_html += (
            f'<div class="control-row control-row-extended">'
            f'<span class="control-name">{html.escape(label)}</span>'
            f'<span class="control-spent">{fmt_rub(spent)}</span>'
            f'<span class="control-pct-cell"><b class="control-pct-inline">{pct_label}</b></span>'
            f'<span class="control-limit">лимит {fmt_rub(limit)}</span>'
            f'{balance_label}'
            f'</div>'
        )
    st.markdown(f'''<div class="section-title">▸ Расходы на контроле · {html.escape(control_month)}{date_suffix}</div>
    <div class="control-card">
        <div class="control-header">Расходы по контролируемым статьям{f" · актуально на {last_dds_date}" if last_dds_date else ""}</div>
        <div class="control-total">{fmt_rub(expenses_control_total)}</div>
        {control_rows_html}
    </div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

# ── БЛОК 4: Результаты предыдущего месяца ──────────────
st.markdown(f'<div class="section-title">▸ Результаты предыдущего месяца · {current_month_label}</div>', unsafe_allow_html=True)
c1, c2 = st.columns([1, 2])
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{fmt_rub(current_revenue)}</div>
        <div class="metric-label">Выручка за месяц</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    eat_color_current = ORANGE if current_eat < 0 else SUCCESS
    sc1_color = ORANGE if eat_v1_cur < 0 else SUCCESS
    sc2_color = ORANGE if eat_v2_cur < 0 else SUCCESS
    sc3_color = SUCCESS if eat_v3_cur >= 0 else ORANGE
    st.markdown(f"""
    <div class="profit-wide">
        <div class="profit-main" style="color:{eat_color_current}">{fmt_rub(current_eat)}</div>
        <div class="metric-label">Чистая прибыль</div>
        <div class="profit-scenarios">
            <div class="profit-scenario"><div class="profit-scenario-val" style="color:{sc1_color}">{fmt_rub(eat_v1_cur)}</div><div class="profit-scenario-label">Факт · все расходы и изъятия</div></div>
            <div class="profit-scenario"><div class="profit-scenario-val" style="color:{sc2_color}">{fmt_rub(eat_v2_cur)}</div><div class="profit-scenario-label">Без вывода собств.</div></div>
            <div class="profit-scenario"><div class="profit-scenario-val" style="color:{sc3_color}">{fmt_rub(eat_v3_cur)}</div><div class="profit-scenario-label">По плану · только плановые расходы</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
if current_overruns > 0:
    st.markdown(f'<div style="margin-top:1rem;"><span class="overrun-badge">⚠ Перерасходы месяца: {fmt_rub(current_overruns)}</span></div>', unsafe_allow_html=True)

st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)

# ── БЛОК 4: Календарь приходов и расходов ─────────────
st.markdown(f'<div class="section-title">▸ Календарь приходов и расходов · {cal_month_name} {cal_year}</div>', unsafe_allow_html=True)
calendar_mode = st.radio(
    "Вид календаря",
    ["Кратко", "Детально"],
    horizontal=True,
    label_visibility="collapsed",
    key="dashboard_calendar_mode",
)
if calendar_mode == "Кратко":
    st.markdown('<div class="calendar-view-label">Общие приходы, расходы и сальдо по дням</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="calendar-view-label">Проекты, поставщики и назначения платежей по каждому дню</div>', unsafe_allow_html=True)

cal_obj = calendar.Calendar(firstweekday=0)
weeks = cal_obj.monthdayscalendar(cal_year, cal_month)
dow = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
today_num = today.day if today.month == cal_month and today.year == cal_year else 0
html_cal = '<table class="cal-table' + (' detailed' if calendar_mode == "Детально" else '') + '"><thead><tr>'
html_cal += ''.join(f'<th>{d}</th>' for d in dow) + '</tr></thead><tbody>'

# Детализация расходов из основной таблицы листа «Расходы».
expense_details_by_day = {}
try:
    expense_url = 'https://docs.google.com/spreadsheets/d/14FFru1xtbOtcLDkjLC-t-Nawy9jPnHrcm-1KZ6coZiU/export?format=csv'
    req = urllib.request.Request(expense_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        expense_rows = list(csv.reader(io.StringIO(resp.read().decode('utf-8', errors='replace'))))
    for row in expense_rows[2:]:
        if len(row) <= 13:
            continue
        day_text = row[1].strip()
        try:
            day = int(day_text)
        except ValueError:
            continue
        group = row[2].strip()
        who = row[3].strip()
        article = row[7].strip()
        comment = row[12].strip()
        amount_text = row[13].replace('\u00A0', ' ').replace(',', '.').replace(' ', '')
        try:
            amount = float(amount_text) if amount_text else 0
        except ValueError:
            amount = 0
        if amount > 0:
            expense_details_by_day.setdefault(day, []).append({
                'amount': amount,
                'group': group,
                'who': who,
                'article': article,
                'comment': comment,
            })
except Exception:
    expense_details_by_day = {}

for week in weeks:
    html_cal += '<tr>'
    for d in week:
        if d == 0:
            html_cal += '<td class="empty"></td>'
            continue
        td_class = 'today' if d == today_num else ''
        num_class = 'today' if d == today_num else ''
        m, r, e = money_cal.get(d, 0), receipts_cal.get(d, 0), expenses_cal.get(d, 0)
        inc = m + r
        cell = f'<div class="cal-num {num_class}">{d}</div>'
        if inc > 0:
            # Общий приход остаётся единственным приходом с зелёной заливкой.
            cell += f'<div class="cal-inc">+{fmt_rub_short(inc)}</div>'
            if m > 0 and r > 0:
                cell += f'<div class="cal-split">+ {fmt_rub_short(m)} разр<br>+ {fmt_rub_short(r)} реал</div>'
            elif m > 0:
                cell += f'<div class="cal-split">+ {fmt_rub_short(m)} разр</div>'
            else:
                cell += f'<div class="cal-split">+ {fmt_rub_short(r)} реал</div>'
        else:
            cell += '<div class="cal-split" style="visibility:hidden">—</div>'
        if e > 0:
            cell += f'<div class="cal-exp">−{fmt_rub_short(e)}</div>'
        else:
            cell += '<div class="cal-exp" style="visibility:hidden">—</div>'

        if calendar_mode == "Детально":
            details = []
            for item in money_details.get(d, []):
                status = 'получено' if item.get('received') else item.get('reason', '')
                label = ' · '.join(x for x in (item.get('project'), status) if x)
                details.append(f'<div class="cal-detail-line income"><span>{html.escape(label)}</span><strong>{fmt_rub_short(item["amount"])}</strong></div>')
            for item in receipt_details.get(d, []):
                label = ' · '.join(x for x in (item.get('project'), item.get('supplier'), item.get('description')) if x)
                details.append(f'<div class="cal-detail-line income"><span>{html.escape(label)}</span><strong>{fmt_rub_short(item["amount"])}</strong></div>')
            for item in expense_details_by_day.get(d, []):
                label = ' · '.join(x for x in (item.get('group'), item.get('who'), item.get('article'), item.get('comment')) if x)
                details.append(f'<div class="cal-detail-line expense"><span>{html.escape(label)}</span><strong>−{fmt_rub_short(item["amount"])}</strong></div>')
            cell += ''.join(details)

        html_cal += f'<td class="{td_class}">{cell}</td>'
    html_cal += '</tr>'
html_cal += '</tbody></table>'
st.markdown(html_cal, unsafe_allow_html=True)

# ── Недельная сводка под календарём ────────────────────
# Каждая неделя повторяет строки календаря. Пустые дни дают нулевые значения.
weekly_lines = []
for week_idx, week in enumerate(weeks, start=1):
    week_income = sum(money_cal.get(d, 0) + receipts_cal.get(d, 0) for d in week if d)
    week_expense = sum(expenses_cal.get(d, 0) for d in week if d)
    week_net = week_income - week_expense
    days_in_week = [d for d in week if d]
    first_day = days_in_week[0] if days_in_week else 0
    last_day = days_in_week[-1] if days_in_week else 0
    is_current_week = today_num and first_day <= today_num <= last_day
    current_class = ' current' if is_current_week else ''
    net_class = 'positive' if week_net >= 0 else 'negative'
    net_sign = '+' if week_net >= 0 else '−'
    weekly_lines.append(
        f'<div class="weekly-line{current_class}">'
        f'<span class="weekly-label">Неделя {week_idx}</span>'
        f'<span class="weekly-value income">приход +{fmt_rub_short(week_income)}</span>'
        f'<span class="weekly-value expense">расход −{fmt_rub_short(week_expense)}</span>'
        f'<span class="weekly-value {net_class}">сальдо {net_sign}{fmt_rub_short(abs(week_net))}</span>'
        '</div>'
    )

st.markdown(
    '<div class="weekly-summary">'
    '<div class="weekly-summary-title">Итого по неделям</div>'
    + ''.join(weekly_lines)
    + '</div>',
    unsafe_allow_html=True,
)

st.markdown(f"""
<div style="text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid {GRAY};">
    <span style="font-size:0.7rem; color:#ccc;">данные из Google Sheets · обновляется автоматически</span>
</div>
""", unsafe_allow_html=True)

