"""
Страница «НДС 5%» · Коченевских бюро
Сверка НДС за 1 квартал 2026: банковские поступления → реестр → Эльба.
СТРОГОЕ сопоставление: ТОЧНАЯ сумма, приоритет УПД→СФ, исключение "Счет".
"""
import streamlit as st
import urllib.request
import urllib.parse
import json
import re
import os
from datetime import date, datetime
from collections import defaultdict
import pandas as pd
import io

# ── Бренд ───────────────────────────────────────────────────────
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GRAY = "#E6E6E6"
WHITE = "#FFFFFF"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

st.set_page_config(page_title="НДС 5% · Коченевских", page_icon="◈", layout="wide")

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


# ── CSS ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: {WHITE}; }}
    #MainMenu {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    h2 {{ color: {GRAPHITE}; font-weight: 300; }}

    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px;
        margin: 8px 0 24px 0;
    }}

    .metric-box {{
        background: {WHITE};
        border: 1px solid {GRAY};
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }}
    .metric-val {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {GRAPHITE};
        line-height: 1.2;
    }}
    .metric-val.orange {{ color: {ORANGE}; }}
    .metric-lbl {{
        font-size: 0.7rem;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.3rem;
    }}

    .summary-card {{
        background: linear-gradient(135deg, #FFF8F6 0%, #FFFFFF 100%);
        border: 2px solid {ORANGE};
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }}
    .summary-label {{
        font-size: 0.8rem;
        font-weight: 500;
        color: #999;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .summary-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {GRAPHITE};
    }}

    .anomaly-box {{
        background: #FFF8F6;
        border-left: 4px solid {ORANGE};
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
    }}
    .anomaly-ok {{
        background: #F4FBF0;
        border-left: 4px solid #27AE60;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
    }}
    .anomaly-warn {{
        background: #FFFCF2;
        border-left: 4px solid #F39C12;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
    }}

    .status-ok {{ color: #27AE60; font-weight: 600; }}
    .status-warn {{ color: #F39C12; font-weight: 600; }}
    .status-bad {{ color: {ORANGE}; font-weight: 600; }}

    div[data-testid="stDataFrame"] thead th {{
        background: {GRAPHITE} !important;
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        padding: 0.7rem 0.9rem !important;
    }}
    div[data-testid="stDataFrame"] tbody td {{
        font-size: 0.85rem !important;
        padding: 0.55rem 0.9rem !important;
        border-bottom: 1px solid {GRAY} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Google OAuth ─────────────────────────────────────────────────
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

SHEET_ID = "1MHhVqgl6IVvscxMaI2_HHjptRrPVpOEaZ_YQtaMkJwc"
GIDS = {
    "register": 422160848,
    "bank": 1714546390,
    "elba1": 557139802,
    "elba2": 965310817,
}

@st.cache_data(ttl=600, show_spinner="Загружаю данные из Google Sheets...")
def load_all_sheets():
    """Load all 4 sheets via Google Sheets API."""
    access_token = _get_google_token()
    if not access_token:
        return None

    try:
        # 1. Get spreadsheet metadata (sheet names by gid)
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())

        gid_to_name = {}
        for s in info.get('sheets', []):
            gid_to_name[s['properties']['sheetId']] = s['properties']['title']

        # 2. Load each sheet's values
        sheets_data = {}
        for key, gid in GIDS.items():
            sheet_name = gid_to_name.get(gid)
            if not sheet_name:
                sheets_data[key] = []
                continue

            encoded_name = urllib.parse.quote(sheet_name, safe='')
            values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{encoded_name}'
            req = urllib.request.Request(values_url)
            req.add_header('Authorization', f'Bearer {access_token}')
            with urllib.request.urlopen(req, timeout=60) as resp:
                values_data = json.loads(resp.read())
            sheets_data[key] = values_data.get('values', [])

        return sheets_data
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return None

# ── Helpers ─────────────────────────────────────────────────────
def parse_date(d):
    """Parse date string like '14.01.2026' to date object."""
    if not d or not d.strip():
        return None
    d = d.strip()
    for fmt in ['%d.%m.%Y', '%d.%m.%y']:
        try:
            return datetime.strptime(d, fmt).date()
        except ValueError:
            continue
    return None

def parse_amount(a):
    """Parse amount string like ' 1 818,00 ₽' or '3044,00 р.' to float."""
    if not a or not a.strip():
        return 0.0
    a = a.strip()
    a = re.sub(r'[₽р.\s]', '', a)
    a = a.replace(',', '.')
    try:
        return float(a)
    except ValueError:
        return 0.0

def is_q1_2026(d):
    """Check if date is in Q1 2026."""
    return d is not None and d.year == 2026 and 1 <= d.month <= 3

def vat_from_total(total):
    """VAT at 5% = amount * 5/105."""
    return round(total * 5.0 / 105.0, 2)

def fmt(v):
    """Format number for display."""
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.1f} млн ₽".replace('.', ',')
    return f"{int(v):,} ₽".replace(',', ' ')

def safe_col(row, idx):
    """Safely get column value."""
    if idx < len(row):
        return row[idx].strip().replace('\u00A0', ' ')
    return ''

# ── STRICT DOC TYPE CLASSIFICATION ──────────────────────────────
# Document types to INCLUDE as valid VAT documents
VAT_VALID_TYPES = {
    'УПД.реализация', 'УПД.проекты',
    'СФ аванс', 'СФ', 'СФ продажа', 'СФ розница',
    'Акт',
    'счёт-фактура', 'Счёт-фактура',
    'Дилерский счет', 'Дилерский счёт',
}

# Document types to EXCLUDE
EXCLUDED_KEYWORDS = ['лиз строка', 'счет', 'счёт']

# УПД types (first priority)
UPD_TYPES = {'УПД.реализация', 'УПД.проекты', 'УПД'}
# СФ types (second priority)
SF_TYPES = {'СФ', 'СФ аванс', 'СФ продажа', 'СФ розница', 'счёт-фактура', 'Счёт-фактура'}


def is_excluded_doc(doc_type):
    """Check if document type is excluded (лиз строка*, Счет plain)."""
    dt_lower = doc_type.strip().lower()
    for kw in EXCLUDED_KEYWORDS:
        if dt_lower.startswith(kw) or kw in dt_lower:
            return True
    return False


def is_valid_vat_doc(doc_type):
    """Check if document type is a valid VAT-relevant document."""
    dt_clean = doc_type.strip()
    if is_excluded_doc(dt_clean):
        return False
    dt_lower = dt_clean.lower()
    for vt in VAT_VALID_TYPES:
        if vt.lower() in dt_lower or dt_lower in vt.lower():
            return True
    if dt_lower in SF_TYPES or dt_lower in UPD_TYPES or 'акт' in dt_lower or 'фактур' in dt_lower:
        return True
    return False


def classify_doc(doc_type):
    """Return doc category: 'УПД', 'СФ', or 'Счет'."""
    dt_lower = doc_type.strip().lower()
    for up in UPD_TYPES:
        if up.lower() in dt_lower:
            return 'УПД'
    for sf in SF_TYPES:
        if sf.lower() in dt_lower or 'фактур' in dt_lower or 'сф' in dt_lower:
            return 'СФ'
    if 'акт' in dt_lower:
        return 'СФ'
    if is_excluded_doc(doc_type):
        return 'Счет'
    return 'other'


def extract_terms(s):
    """Extract key terms for matching."""
    if not s:
        return set()
    words = re.findall(r'[а-яёa-z0-9]+', s.lower())
    stop = {'ип', 'ооо', 'г', 'ул', 'д', 'пер', 'жк', 'р', 'счет', 'сф', 'упд',
            'акт', 'ндс', 'без', 'для', 'от', 'на', 'по', 'и', 'в', 'за', 'к', 'с', 'аванс'}
    return set(w for w in words if len(w) > 2 and w not in stop)


def extract_counterparty_name(val):
    if not val:
        return ""
    val = str(val).strip()
    val = ' '.join(val.split()).lower()
    for prefix in ['ооо ', 'ао ', 'ип ', 'зао ', 'пао ']:
        if val.startswith(prefix):
            val = val[len(prefix):]
    return val


# ── Load data ───────────────────────────────────────────────────
sheets = load_all_sheets()

if sheets is None:
    st.error("Не удалось загрузить данные. Проверьте подключение к Google Sheets.")
    st.stop()

register_raw = sheets.get("register", [])
bank_raw = sheets.get("bank", [])
elba1_raw = sheets.get("elba1", [])
elba2_raw = sheets.get("elba2", [])

# ── Parse Register ──────────────────────────────────────────────
all_registry_docs = []
schet_entries = []

for i, row in enumerate(register_raw[1:], start=2):
    if len(row) < 5:
        continue
    amt = parse_amount(safe_col(row, 6))
    doc_type = safe_col(row, 4)
    doc_num = safe_col(row, 0)

    doc = {
        'row': i,
        'doc_num': doc_num,
        'doc_date': parse_date(safe_col(row, 1)),
        'doc_month': safe_col(row, 2),
        'doc_year': safe_col(row, 3),
        'doc_type': doc_type,
        'responsible': safe_col(row, 5),
        'amount': amt,
        'payment_date': parse_date(safe_col(row, 7)) if safe_col(row, 7) else None,
        'payment_to': safe_col(row, 8),
        'for_vat': safe_col(row, 9),
        'project': safe_col(row, 14),
        'client_name': safe_col(row, 15),
        'contract_num': safe_col(row, 16),
        'stage_num': safe_col(row, 17),
        'comment': safe_col(row, 19),
        'quarter': safe_col(row, 23) if len(row) > 23 else '',
        'vat': vat_from_total(amt),
    }

    if is_excluded_doc(doc_type):
        if classify_doc(doc_type) == 'Счет':
            schet_entries.append(doc)
        continue

    if is_valid_vat_doc(doc_type):
        doc['doc_category'] = classify_doc(doc_type)
        all_registry_docs.append(doc)

# ── Parse Bank Statement ────────────────────────────────────────
bank_payments = []
for i, row in enumerate(bank_raw[1:], start=2):
    if len(row) < 12:
        continue
    amt_str = safe_col(row, 3)
    amt = parse_amount(amt_str)
    pay_type = safe_col(row, 11)
    bank_payments.append({
        'row': i,
        'month': safe_col(row, 0),
        'date': parse_date(safe_col(row, 2)),
        'amount': amt,
        'direction': safe_col(row, 5),
        'counterparty': safe_col(row, 6),
        'project': safe_col(row, 7),
        'article': safe_col(row, 10),
        'payment_type': pay_type,
        'is_receipt': 'Поступление' in pay_type or 'поступление' in pay_type.lower(),
    })

# ── Parse Elba ──────────────────────────────────────────────────
def parse_elba(raw_data, sheet_label):
    docs = []
    for i, row in enumerate(raw_data[1:], start=2):
        if len(row) < 11:
            continue
        amt = parse_amount(safe_col(row, 10))
        vat_amt = parse_amount(safe_col(row, 11))
        docs.append({
            'row': i,
            'sheet': sheet_label,
            'doc_date': parse_date(safe_col(row, 0)),
            'doc_number': safe_col(row, 1),
            'doc_type': safe_col(row, 2),
            'order': safe_col(row, 3),
            'group': safe_col(row, 4),
            'counterparty': safe_col(row, 5),
            'item_name': safe_col(row, 6),
            'amount': amt,
            'vat_amount': vat_amt,
            'vat_rate': safe_col(row, 12),
            'status': safe_col(row, 13),
        })
    return docs

elba1_docs = parse_elba(elba1_raw, "Эльба Q1")
elba2_docs = parse_elba(elba2_raw, "Эльба Q2")

# ── Q1 Filtering ────────────────────────────────────────────────
q1_bank = [d for d in bank_payments if is_q1_2026(d['date']) and d['is_receipt']]

# VAT-relevant registry docs
vat_real_types = ['УПД.реализация', 'УПД.проекты', 'СФ розница', 'СФ продажа', 'Акт']
vat_advance_types = ['СФ аванс']

q1_obligations = [d for d in all_registry_docs if d['doc_type'] in vat_real_types and is_q1_2026(d['doc_date'])]
q1_advances = [d for d in all_registry_docs if d['doc_type'] in vat_advance_types and is_q1_2026(d['doc_date'])]

# Elba Q1 VAT 5%
elba_vat5_q1 = [d for d in elba1_docs if d['vat_rate'] == 'НДС 5%']
elba_real_vat = [d for d in elba_vat5_q1 if d['doc_type'] in ('счёт-фактура', 'УПД', 'Акт для Физического лица', 'Акт для ИП/Юрлица')]
elba_schet_vat = [d for d in elba_vat5_q1 if d['doc_type'] == 'Счёт']

# ── Calculations ────────────────────────────────────────────────
total_bank_receipts = sum(d['amount'] for d in q1_bank)
total_bank_vat = vat_from_total(total_bank_receipts)

obl_total = sum(d['amount'] for d in q1_obligations)
obl_vat = vat_from_total(obl_total)

adv_total = sum(d['amount'] for d in q1_advances)
adv_vat = vat_from_total(adv_total)

correct_q1_vat = obl_vat + adv_vat

elba_vat_total_all = sum(d['vat_amount'] for d in elba_vat5_q1)
elba_vat_total_real = sum(d['vat_amount'] for d in elba_real_vat)
elba_vat_total_schet = sum(d['vat_amount'] for d in elba_schet_vat)

# ── STRICT Matching: Bank Receipts → Registry → Elba ────────────
receipt_matches = []
used_registry = set()

for br in q1_bank:
    if br['amount'] <= 0:
        continue

    # ── Step 1: Find EXACT amount matches in registry ───────────
    exact_matches = []
    for idx, rd in enumerate(all_registry_docs):
        if idx in used_registry:
            continue
        if abs(br['amount'] - rd['amount']) < 0.01:  # EXACT match only
            exact_matches.append((idx, rd))

    # Prioritize: УПД first, then СФ
    upd_exact = [(i, d) for i, d in exact_matches if d.get('doc_category') == 'УПД']
    sf_exact = [(i, d) for i, d in exact_matches if d.get('doc_category') == 'СФ']

    best_reg = None
    reg_status = "⚠ нет док-та"

    if upd_exact:
        best_reg = pick_best_exact_match(br, upd_exact)
        used_registry.add(best_reg[0])
        reg_status = "✓ УПД"
    elif sf_exact:
        best_reg = pick_best_exact_match(br, sf_exact)
        used_registry.add(best_reg[0])
        reg_status = "✓ СФ"
    else:
        # No exact match → check for close match to flag discrepancy
        close_match = None
        for idx, rd in enumerate(all_registry_docs):
            if idx in used_registry:
                continue
            if br['amount'] > 0 and rd['amount'] > 0:
                ratio = abs(br['amount'] - rd['amount']) / max(br['amount'], rd['amount'])
                if ratio <= 0.05:
                    r_terms = extract_terms((br['project'] or '') + ' ' + (br['counterparty'] or ''))
                    d_terms = extract_terms((rd['project'] or '') + ' ' + (rd['client_name'] or ''))
                    if len(r_terms & d_terms) >= 1:
                        if close_match is None or ratio < close_match[2]:
                            close_match = (idx, rd, ratio)

        if close_match:
            best_reg = close_match
            used_registry.add(close_match[0])
            reg_status = "⚠ сумма не совпадает"
        elif br['amount'] >= 1:
            # Check for plain Счет-only
            schet_for_amount = [s for s in schet_entries if abs(br['amount'] - s['amount']) < 0.01]
            if schet_for_amount:
                reg_status = "⚠ только Счет"
                best_reg = (None, schet_for_amount[0])

    # ── Step 2: Match to Elba ──────────────────────────────────
    best_elba = None
    elba_status = "—"
    elba_vat_val = 0.0

    reg_doc = best_reg[1] if best_reg else None
    if reg_doc:
        best_elba_score = 0
        for ed in elba_real_vat:
            # EXACT amount match
            if abs(reg_doc['amount'] - ed['amount']) > 0.01:
                continue
            score = 0
            # Counterparty overlap
            cp_reg = extract_counterparty_name(reg_doc.get('client_name', ''))
            cp_elba = extract_counterparty_name(ed['counterparty'])
            if cp_reg and cp_elba:
                if cp_reg == cp_elba:
                    score += 20
                elif cp_reg in cp_elba or cp_elba in cp_reg:
                    score += 15
                else:
                    common = set(cp_reg.split()) & set(cp_elba.split())
                    if common:
                        score += 5
            # Project/description overlap
            r_terms = extract_terms((reg_doc['project'] or '') + ' ' + (reg_doc.get('client_name', '') or ''))
            e_terms = extract_terms((ed['item_name'] or '') + ' ' + (ed['counterparty'] or ''))
            overlap = len(r_terms & e_terms)
            if overlap >= 2:
                score += 10
            elif overlap >= 1:
                score += 5
            # Doc type compatibility
            rd_lower = reg_doc['doc_type'].lower()
            ed_lower = ed['doc_type'].lower()
            if 'упд' in rd_lower and 'упд' in ed_lower:
                score += 10
            elif ('сф' in rd_lower or 'фактур' in rd_lower) and ('счёт-фактур' in ed_lower or 'сф' in ed_lower):
                score += 10
            if score > best_elba_score:
                best_elba_score = score
                best_elba = ed
        if best_elba and best_elba_score >= 5:
            elba_status = "✓"
            elba_vat_val = best_elba['vat_amount']
        else:
            elba_status = "⚠ НЕТ В ЭЛЬБЕ"
    else:
        # No registry doc — try matching receipt directly to Elba
        for ed in elba_real_vat:
            if abs(br['amount'] - ed['amount']) < 0.01:
                cp_rec = extract_counterparty_name(br['counterparty'])
                cp_elba = extract_counterparty_name(ed['counterparty'])
                if cp_rec and cp_elba and (cp_rec == cp_elba or cp_rec in cp_elba or cp_elba in cp_rec):
                    best_elba = ed
                    elba_vat_val = ed['vat_amount']
                    elba_status = "⚠ есть в Эльбе"
                    break

    # ── Overall status ──────────────────────────────────────────
    if '✓' in reg_status and elba_status == "✓":
        overall = "✓ ПОЛНОСТЬЮ"
        status_class = 'status-ok'
    elif 'только Счет' in reg_status:
        overall = "⚠ ТОЛЬКО СЧЕТ"
        status_class = 'status-warn'
    elif 'сумма не совпадает' in reg_status:
        overall = "⚠ СУММА НЕ СОВПАДАЕТ"
        status_class = 'status-warn'
    elif 'нет док-та' in reg_status:
        overall = "❌ НЕТ ДОК-ТА"
        status_class = 'status-bad'
    elif elba_status != "✓" and elba_status != '—':
        overall = "⚠ НЕТ В ЭЛЬБЕ"
        status_class = 'status-warn'
    else:
        overall = "⚠ ТРЕБУЕТСЯ ПРОВЕРКА"
        status_class = 'status-warn'

    receipt_matches.append({
        'date': br['date'],
        'amount': br['amount'],
        'project': br['project'] or '—',
        'counterparty': br['counterparty'] or '—',
        'reg_type': reg_doc['doc_type'] if reg_doc else '—',
        'reg_num': reg_doc['doc_num'] if reg_doc else '—',
        'reg_amount': reg_doc['amount'] if reg_doc else 0,
        'reg_status': reg_status,
        'elba_type': best_elba['doc_type'] if best_elba else '—',
        'elba_num': best_elba['doc_number'] if best_elba else '—',
        'elba_vat': elba_vat_val,
        'elba_status': elba_status,
        'status': overall,
        'status_class': status_class,
    })


def pick_best_exact_match(receipt, candidates):
    """Among EXACT amount matches, pick the one with best project/counterparty overlap."""
    if len(candidates) == 1:
        return candidates[0]
    best = candidates[0]
    best_score = -1
    r_terms = extract_terms((receipt['project'] or '') + ' ' + (receipt['counterparty'] or ''))
    for idx, doc in candidates:
        score = 0
        d_terms = extract_terms((doc['project'] or '') + ' ' + (doc.get('client_name', '') or ''))
        overlap = len(r_terms & d_terms)
        score += overlap * 5
        if receipt['date'] and doc['doc_date']:
            diff = abs((receipt['date'] - doc['doc_date']).days)
            if diff <= 7:
                score += 3
            elif diff <= 30:
                score += 1
        if score > best_score:
            best_score = score
            best = (idx, doc)
    return best


# ── Anomalies ───────────────────────────────────────────────────
# 1. Receipts without advance invoices
advance_needed = []
for d in all_registry_docs:
    if d['payment_date'] and is_q1_2026(d['payment_date']):
        if d['doc_date'] and not is_q1_2026(d['doc_date']):
            has_advance = False
            for ed in elba1_docs:
                if ed['doc_type'] == 'счёт-фактура' and 'аванс' in ed['item_name'].lower():
                    if abs(ed['amount'] - d['amount']) < d['amount'] * 0.05:
                        has_advance = True
                        break
            if not has_advance:
                advance_needed.append(d)

# 2. Unmatched Elba (real VAT docs not matched to registry)
used_elba_for_anomaly = set()
for rm in receipt_matches:
    if rm.get('elba_status') == '✓' and rm.get('elba_type') not in ('—', ''):
        for i, ed in enumerate(elba_real_vat):
            if ed['doc_number'] == rm['elba_num']:
                used_elba_for_anomaly.add(i)
                break

unmatched_elba = [ed for i, ed in enumerate(elba_real_vat) if i not in used_elba_for_anomaly]

# 3. Double-count check: Elba Счёт vs real docs
double_counted = []
for sc in elba_schet_vat:
    for rd in elba_real_vat:
        if abs(sc['amount'] - rd['amount']) < 1 and sc['doc_date'] == rd['doc_date']:
            double_counted.append((sc, rd))
            break


# ═══════════════════════════════════════════════════════════════════
# UI RENDER
# ═══════════════════════════════════════════════════════════════════

# ── Header ──────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:0.5rem;">
    <img src="{LOGO_URL}" style="height:22px;">
    <h2 style="margin:0;font-weight:300;">НДС 5% · Сверка 1 квартал 2026</h2>
</div>
<p style="color:#999;font-size:0.8rem;margin-top:0;margin-bottom:0;">Коченевских бюро · поступления → реестр → Эльба · СТРОГОЕ сопоставление</p>
""", unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: Summary Cards
# ═══════════════════════════════════════════════════════════════════
st.markdown("### I. Сводка")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-box">
        <div class="metric-val">{fmt(total_bank_receipts)}</div>
        <div class="metric-lbl">Поступления Q1 · {len(q1_bank)} операций</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-box">
        <div class="metric-val">{fmt(total_bank_vat)}</div>
        <div class="metric-lbl">НДС 5% от поступлений (расчётно)</div>
    </div>""", unsafe_allow_html=True)
with c3:
    matched_count = sum(1 for r in receipt_matches if '✓' in r['status'])
    mismatch_count = sum(1 for r in receipt_matches if 'СУММА' in r['status'])
    missing_count = sum(1 for r in receipt_matches if 'НЕТ ДОК-ТА' in r['status'])
    st.markdown(f"""<div class="metric-box">
        <div class="metric-val">{matched_count}</div>
        <div class="metric-lbl">Полных совпадений (УПД/СФ)</div>
    </div>""", unsafe_allow_html=True)
with c4:
    total_issues = mismatch_count + missing_count + len(unmatched_elba)
    st.markdown(f"""<div class="metric-box">
        <div class="metric-val orange">{total_issues}</div>
        <div class="metric-lbl">Аномалий / расхождений</div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 2: Receipt-to-document Matching Table
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### II. Сопоставление: поступления → реестр → Эльба")
st.markdown("*Точное совпадение сумм. Приоритет: УПД → СФ. Счёт исключён.*")

if receipt_matches:
    df_matches = pd.DataFrame(receipt_matches)
    df_matches = df_matches.sort_values('date', ascending=True)

    df_matches['date_str'] = df_matches['date'].apply(lambda d: d.strftime('%d.%m.%Y') if d else '—')
    df_matches['amount_fmt'] = df_matches['amount'].apply(fmt)
    df_matches['reg_info'] = df_matches.apply(
        lambda r: f"{r['reg_type']} №{r['reg_num']}" if r['reg_num'] != '—' else '—', axis=1)
    df_matches['elba_info'] = df_matches.apply(
        lambda r: f"{r['elba_type']} №{r['elba_num']} (НДС {fmt(r['elba_vat'])})" if r['elba_num'] != '—' else '—', axis=1)

    display_cols = ['date_str', 'amount_fmt', 'counterparty', 'project', 'reg_info', 'reg_status', 'elba_info', 'status']
    col_names = {
        'date_str': 'Дата',
        'amount_fmt': 'Сумма',
        'counterparty': 'Контрагент',
        'project': 'Проект',
        'reg_info': 'Документ реестра',
        'reg_status': 'Статус реестра',
        'elba_info': 'Документ Эльбы',
        'status': 'ИТОГ',
    }

    df_display = df_matches[display_cols].rename(columns=col_names)

    st.dataframe(df_display, use_container_width=True, hide_index=True,
                 column_config={
                     'Дата': st.column_config.TextColumn('Дата', width='small'),
                     'Сумма': st.column_config.TextColumn('Сумма', width='small'),
                     'Контрагент': st.column_config.TextColumn('Контрагент', width='medium'),
                     'Проект': st.column_config.TextColumn('Проект', width='medium'),
                     'Документ реестра': st.column_config.TextColumn('Документ реестра', width='medium'),
                     'Статус реестра': st.column_config.TextColumn('Статус реестра', width='small'),
                     'Документ Эльбы': st.column_config.TextColumn('Документ Эльбы', width='large'),
                     'ИТОГ': st.column_config.TextColumn('ИТОГ', width='small'),
                 })

    # Stats summary
    ok_count = sum(1 for r in receipt_matches if '✓ ПОЛНОСТЬЮ' in r['status'])
    amt_mismatch = sum(1 for r in receipt_matches if 'СУММА' in r['status'])
    no_doc = sum(1 for r in receipt_matches if 'НЕТ ДОК-ТА' in r['status'])
    no_elba = sum(1 for r in receipt_matches if 'НЕТ В ЭЛЬБЕ' in r['status'])
    schet_only = sum(1 for r in receipt_matches if 'ТОЛЬКО СЧЕТ' in r['status'])

    st.markdown(f"""
    <div style="display:flex; gap:20px; margin-top:0.5rem; font-size:0.85rem; flex-wrap:wrap;">
        <span class="status-ok">✓ Полное совпадение: {ok_count}</span>
        <span class="status-warn">⚠ Сумма не совпадает: {amt_mismatch}</span>
        <span class="status-warn">⚠ Только Счёт: {schet_only}</span>
        <span class="status-bad">❌ Нет док-та: {no_doc}</span>
        <span class="status-warn">⚠ Нет в Эльбе: {no_elba}</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Нет данных о поступлениях за Q1 2026.")

# ═══════════════════════════════════════════════════════════════════
# SECTION 3: Anomalies
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### III. Аномалии и расхождения")

anomaly_tabs = st.tabs([
    "Поступления без СФ на аванс",
    "Документы Эльбы без реестра",
    "Двойной учёт Счёт↔УПД",
    "Сводка по статусам",
])

with anomaly_tabs[0]:
    st.markdown("**Поступления в Q1, обязательства по которым закрываются позже — нужен счёт-фактура на аванс.**")
    if advance_needed:
        adv_rows = []
        for d in sorted(advance_needed, key=lambda x: (x['payment_date'] or date.min, -x['amount'])):
            found_in_elba = False
            for ed in elba1_docs:
                if ed['doc_type'] == 'счёт-фактура' and 'аванс' in ed['item_name'].lower():
                    if abs(ed['amount'] - d['amount']) < d['amount'] * 0.05:
                        found_in_elba = True
                        break

            adv_rows.append({
                'Оплата': d['payment_date'].strftime('%d.%m.%Y') if d['payment_date'] else '—',
                'Сумма': d['amount'],
                'Документ': f"{d['doc_type']} №{d['doc_num']}",
                'Дата документа': d['doc_date'].strftime('%d.%m.%Y') if d['doc_date'] else '—',
                'Проект': d['project'][:50] or '—',
                'Клиент': d['client_name'][:30] or '—',
                'СФ аванс в Эльбе': '✓ Есть' if found_in_elba else '✗ НЕТ',
            })

        df_adv = pd.DataFrame(adv_rows)
        df_adv['Сумма_ф'] = df_adv['Сумма'].apply(fmt)
        st.dataframe(df_adv[['Оплата', 'Сумма_ф', 'Документ', 'Дата документа', 'Проект', 'Клиент', 'СФ аванс в Эльбе']],
                     use_container_width=True, hide_index=True)

        no_adv_count = sum(1 for r in adv_rows if 'НЕТ' in r['СФ аванс в Эльбе'])
        no_adv_total = sum(r['Сумма'] for r in adv_rows if 'НЕТ' in r['СФ аванс в Эльбе'])
        if no_adv_count > 0:
            st.markdown(f"""
            <div class="anomaly-box">
                <strong>⚠ {no_adv_count} платежей без СФ на аванс</strong> на сумму {fmt(no_adv_total)}.
                Потенциальный неучтённый НДС: <strong>{fmt(vat_from_total(no_adv_total))}</strong>.
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="anomaly-ok">✓ Все поступления Q1 имеют соответствующие документы.</div>',
                     unsafe_allow_html=True)

with anomaly_tabs[1]:
    st.markdown("**Документы с НДС 5% в Эльбе Q1, для которых нет точного соответствия в реестре.**")
    if unmatched_elba:
        ue_rows = []
        for d in sorted(unmatched_elba, key=lambda x: (x['doc_date'] or date.min, -x['amount'])):
            ue_rows.append({
                'Дата': d['doc_date'].strftime('%d.%m.%Y') if d['doc_date'] else '—',
                'Тип': d['doc_type'],
                '№': d['doc_number'],
                'Сумма': d['amount'],
                'НДС': d['vat_amount'],
                'Контрагент': d['counterparty'][:35] if d['counterparty'] else '—',
                'Наименование': d['item_name'][:50] if d['item_name'] else '—',
            })
        df_ue = pd.DataFrame(ue_rows)
        df_ue['Сумма_ф'] = df_ue['Сумма'].apply(fmt)
        df_ue['НДС_ф'] = df_ue['НДС'].apply(fmt)

        st.dataframe(df_ue[['Дата', 'Тип', '№', 'Сумма_ф', 'НДС_ф', 'Контрагент', 'Наименование']],
                     use_container_width=True, hide_index=True)

        ue_total = sum(d['amount'] for d in unmatched_elba)
        ue_vat_total = sum(d['vat_amount'] for d in unmatched_elba)

        st.markdown(f"""
        <div class="anomaly-warn">
            <strong>⚠ {len(unmatched_elba)} документов без точного совпадения</strong> на сумму {fmt(ue_total)} (НДС: {fmt(ue_vat_total)}).
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="anomaly-ok">✓ Все документы Эльбы имеют соответствие в реестре.</div>',
                     unsafe_allow_html=True)

with anomaly_tabs[2]:
    st.markdown("**Одно обязательство может быть учтено в Эльбе дважды: как Счёт и как УПД/СФ.**")
    if double_counted:
        dc_rows = []
        for sc, rd in double_counted:
            dc_rows.append({
                'Дата': sc['doc_date'].strftime('%d.%m.%Y') if sc['doc_date'] else '—',
                'Счёт · сумма': sc['amount'],
                'Счёт · НДС': sc['vat_amount'],
                'УПД/СФ · сумма': rd['amount'],
                'УПД/СФ · НДС': rd['vat_amount'],
                'Контрагент': sc['counterparty'][:35] if sc['counterparty'] else '—',
            })
        df_dc = pd.DataFrame(dc_rows)
        for col in ['Счёт · сумма', 'Счёт · НДС', 'УПД/СФ · сумма', 'УПД/СФ · НДС']:
            df_dc[f'{col}_ф'] = df_dc[col].apply(fmt)

        dc_vat_total = sum(r['Счёт · НДС'] for r in dc_rows)
        st.dataframe(df_dc[['Дата', 'Счёт · сумма_ф', 'Счёт · НДС_ф', 'УПД/СФ · сумма_ф', 'УПД/СФ · НДС_ф', 'Контрагент']],
                     use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div class="anomaly-box">
            <strong>⚠ Найдено {len(double_counted)} случаев двойного учёта!</strong>
            <br>Одно и то же обязательство проведено как Счёт и как УПД/СФ — НДС посчитан дважды.
            <br>Избыточный НДС: <strong>{fmt(dc_vat_total)}</strong>.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="anomaly-ok">✓ Двойной учёт не обнаружен.</div>', unsafe_allow_html=True)

with anomaly_tabs[3]:
    st.markdown("**Сводка всех статусов сопоставления.**")
    status_counts = defaultdict(int)
    status_amounts = defaultdict(float)
    for rm in receipt_matches:
        s = rm['status']
        status_counts[s] += 1
        status_amounts[s] += rm['amount']

    summary_rows = []
    for s in sorted(status_counts.keys()):
        summary_rows.append({
            'Статус': s,
            'Кол-во': status_counts[s],
            'Сумма': fmt(status_amounts[s]),
        })
    if summary_rows:
        df_sum = pd.DataFrame(summary_rows)
        st.dataframe(df_sum, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 4: Q1 VAT Calculation
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### IV. Расчёт НДС за 1 квартал 2026")

v1, v2 = st.columns(2)

with v1:
    st.markdown("**Правильный расчёт НДС (по реестру)**")
    st.markdown(f"""
    <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
        <tr>
            <td style="padding:8px 0;">Завершённые обязательства Q1 (УПД, Акты, СФ)</td>
            <td style="text-align:right;padding:8px 0;">{len(q1_obligations)} док.</td>
            <td style="text-align:right;padding:8px 0;font-weight:600;">{fmt(obl_total)}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;color:{ORANGE};">НДС с обязательств (5/105)</td>
            <td style="text-align:right;padding:8px 0;"></td>
            <td style="text-align:right;padding:8px 0;font-weight:700;color:{ORANGE};">{fmt(obl_vat)}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;">СФ на аванс (выставлены в Q1)</td>
            <td style="text-align:right;padding:8px 0;">{len(q1_advances)} док.</td>
            <td style="text-align:right;padding:8px 0;font-weight:600;">{fmt(adv_total)}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;color:{ORANGE};">НДС с авансов (5/105)</td>
            <td style="text-align:right;padding:8px 0;"></td>
            <td style="text-align:right;padding:8px 0;font-weight:700;color:{ORANGE};">{fmt(adv_vat)}</td>
        </tr>
        <tr style="border-top:2px solid {GRAPHITE};">
            <td style="padding:10px 0;font-weight:700;font-size:1.1rem;">ИТОГО НДС К УПЛАТЕ</td>
            <td style="text-align:right;padding:10px 0;"></td>
            <td style="text-align:right;padding:10px 0;font-weight:700;font-size:1.2rem;color:{ORANGE};">{fmt(correct_q1_vat)}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

with v2:
    st.markdown("**НДС в Эльбе (отчёт Q1)**")
    st.markdown(f"""
    <table style="width:100%; border-collapse:collapse; font-size:0.9rem;">
        <tr>
            <td style="padding:8px 0;">Все документы с НДС 5%</td>
            <td style="text-align:right;padding:8px 0;">{len(elba_vat5_q1)} строк</td>
            <td style="text-align:right;padding:8px 0;font-weight:600;">{fmt(elba_vat_total_all)}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;">Счёт-фактура + УПД + Акты (реальные)</td>
            <td style="text-align:right;padding:8px 0;">{len(elba_real_vat)} строк</td>
            <td style="text-align:right;padding:8px 0;font-weight:600;">{fmt(elba_vat_total_real)}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;color:#999;">Счёт (НЕ документы НДС)</td>
            <td style="text-align:right;padding:8px 0;color:#999;">{len(elba_schet_vat)} строк</td>
            <td style="text-align:right;padding:8px 0;font-weight:600;color:#999;">{fmt(elba_vat_total_schet)}</td>
        </tr>
        <tr style="border-top:2px solid {GRAPHITE};">
            <td style="padding:10px 0;font-weight:700;font-size:1.1rem;">НДС Эльба (реальные док.)</td>
            <td style="text-align:right;padding:10px 0;"></td>
            <td style="text-align:right;padding:10px 0;font-weight:700;font-size:1.2rem;">{fmt(elba_vat_total_real)}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

# ── Difference Summary ──────────────────────────────────────────
diff_real = elba_vat_total_real - correct_q1_vat
diff_all = elba_vat_total_all - correct_q1_vat

if abs(diff_real) < 10:
    diff_color = '#27AE60'
    diff_icon = '✅'
    diff_text = 'Сходится'
elif diff_real > 0:
    diff_color = ORANGE
    diff_icon = '⚠️'
    diff_text = 'Эльба завышает'
else:
    diff_color = '#F39C12'
    diff_icon = '⚠️'
    diff_text = 'Эльба занижает'

st.markdown(f"""
<div class="summary-card" style="margin-top:1.5rem;">
    <div class="summary-label">Сверка НДС · Q1 2026</div>
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:20px;">
        <div>
            <div style="font-size:0.85rem; color:#999;">Правильный НДС (реестр)</div>
            <div style="font-size:1.6rem; font-weight:700;">{fmt(correct_q1_vat)}</div>
        </div>
        <div style="font-size:1.5rem; color:#999;">→</div>
        <div>
            <div style="font-size:0.85rem; color:#999;">Эльба (реальные док.)</div>
            <div style="font-size:1.6rem; font-weight:700;">{fmt(elba_vat_total_real)}</div>
        </div>
        <div style="font-size:1.5rem; color:#999;">→</div>
        <div>
            <div style="font-size:0.85rem; color:#999;">Эльба (все записи)</div>
            <div style="font-size:1.6rem; font-weight:700; color:{ORANGE};">{fmt(elba_vat_total_all)}</div>
        </div>
        <div style="font-size:1.5rem; color:{diff_color};">{diff_icon}</div>
        <div>
            <div style="font-size:0.85rem; color:#999;">Расхождение (реальные)</div>
            <div style="font-size:1.4rem; font-weight:700; color:{diff_color};">{fmt(diff_real)}</div>
        </div>
    </div>
    <div style="margin-top:1rem; font-size:0.85rem; color:{GRAPHITE};">
        <strong>{diff_icon} {diff_text}:</strong>
        {f'Разница {fmt(abs(diff_real))} между реестром и реальными документами Эльбы.' if abs(diff_real) >= 10 else 'Реальные документы НДС в Эльбе совпадают с реестром.'}
        {f'<br>⚠️ Если считать все записи Эльбы (включая Счёт), переплата НДС составит <strong>{fmt(diff_all)}</strong> ({diff_all/correct_q1_vat*100:.0f}% завышения).' if diff_all > 0 else ''}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Key Recommendations ─────────────────────────────────────────
st.markdown("---")
st.markdown("### V. Рекомендации")

receipts_ok = ok_count
receipts_missing_doc = no_doc
receipts_mismatch = amt_mismatch
receipts_no_elba = no_elba
receipts_schet = schet_only

recs = [
    ("🔴 Критично", f"Эльба учитывает {len(elba_schet_vat)} записей типа «Счёт» с НДС {fmt(elba_vat_total_schet)}. "
     f"Счёт — это платёжный документ, а не документ НДС. Удалите Счёт из расчёта НДС в Эльбе."),
    ("🟡 Важно", f"Из {len(q1_bank)} поступлений Q1: {receipts_ok} полностью совпали (✓), {receipts_missing_doc} без док-та (❌), "
     f"{receipts_mismatch} с расхождением суммы (⚠), {receipts_schet} только Счёт (⚠)."),
    ("🟡 Важно", f"{len(unmatched_elba)} документов Эльбы не нашли точного соответствия в реестре. Проверьте их."),
    ("🟡 Важно", f"Убедитесь, что СФ на аванс выставлены для всех платежей Q1, "
     f"где обязательство закрывается в Q2+. Сейчас {len(advance_needed)} сомнительных случаев."),
    ("🟢 Рекомендация", f"При подаче декларации по НДС за Q1 используйте только "
     "счёт-фактуры, УПД и Акты. Не включайте Счёт."),
    ("🟢 Рекомендация", f"Все сопоставления используют ТОЧНОЕ совпадение сумм. Приоритет: УПД → СФ. "
     "Суммы в банке, реестре и Эльбе должны совпадать до копейки."),
]

for severity, text in recs:
    st.markdown(f'<div style="padding:0.5rem 0; font-size:0.9rem;"><strong>{severity}:</strong> {text}</div>',
                unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:right; color:#bbb; font-size:0.75rem; margin-top:2rem;">
    Актуально на {datetime.now().strftime('%d.%m.%Y %H:%M')} · данные из Google Sheets · СТРОГОЕ сопоставление v2
</div>
""", unsafe_allow_html=True)
