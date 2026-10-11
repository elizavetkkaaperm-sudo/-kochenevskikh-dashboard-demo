"""
Страница «Планы» · Коченевских бюро
План на месяц: разработка, деньги, реализация, продажи.
+ Детализация по проектам (Разработка) — из листа «Разработка»
+ Детализация по проектам (Реализация) — из Приходов
"""
import streamlit as st
import pandas as pd
import urllib.request
import urllib.parse
import csv
import io
import json
import calendar
import html as html_lib
from datetime import date

# ── Авторизация ─────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице.")
    st.stop()

# ── Бренд ───────────────────────────────────────────────────────
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

st.set_page_config(page_title="Планы · Коченевских", page_icon="◈", layout="wide")

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
    div[data-testid="stHorizontalBlock"] {{
        align-items: stretch !important;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {{
        height: 100%;
    }}
    h1 {{ color: {GRAPHITE}; font-weight: 600; font-size: 1.8rem; }}
    h2 {{ color: {GRAPHITE}; font-weight: 500; font-size: 1.2rem; }}
    h3 {{ color: {GRAPHITE}; font-weight: 600; font-size: 1rem; }}
    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px; margin: 8px 0 24px 0;
    }}
    .plan-card {{
        background: {WHITE};
        border: 1px solid {GREY};
        border-radius: 12px;
        padding: 24px 20px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-self: stretch;
        flex: 1;
    }}
    .plan-card-title {{
        font-size: 0.8rem;
        font-weight: 500;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }}
    .plan-card-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {GRAPHITE};
    }}
    .plan-card-sub {{
        font-size: 0.8rem;
        color: #aaa;
        margin-top: 4px;
    }}
    .plan-detail-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }}
    .plan-detail-table th {{
        background: {GRAPHITE};
        color: white;
        padding: 8px 12px;
        text-align: left;
    }}
    .plan-detail-table th:last-child, .plan-detail-table th:nth-last-child(2) {{ text-align: right; }}
    .plan-detail-table td {{
        padding: 6px 12px;
        border-bottom: 1px solid {GREY};
    }}
    .plan-detail-table td:last-child, .plan-detail-table td:nth-last-child(2) {{ text-align: right; font-weight: 500; }}
    .plan-detail-table tbody tr:hover {{ background: #fafafa; }}
    .block-label {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 6px;
    }}
    .block-dev {{ background: #FFF0EE; color: {ORANGE}; }}
    .block-money {{ background: #E8F5E9; color: #2E7D32; }}
    .block-agent {{ background: #EEF5FF; color: #1565C0; }}
    .block-sales {{ background: #F3E5F5; color: #7B1FA2; }}
    .closed-cell {{ background: #E8F5E9; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; color: #2E7D32; }}
    .empty-cell {{ color: #ccc; }}

    /* Карточки реализации */
    .receipt-stat-card {{
        background: {WHITE};
        border: 1px solid {GREY};
        border-radius: 10px;
        padding: 20px 14px;
        text-align: center;
        height: 100%;
    }}
    .receipt-stat-value {{
        font-size: 1.6rem;
        font-weight: 700;
    }}
    .receipt-stat-label {{
        font-size: 0.7rem;
        color: #888;
        margin-top: 2px;
    }}
    .receipt-breakdown {{
        font-size: 0.75rem;
        color: {GRAPHITE};
        margin-top: 8px;
        line-height: 1.5;
    }}

    /* Календарь приходов */
    .receipts-calendar {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}
    .receipts-calendar th {{
        background: {GRAPHITE};
        color: white;
        padding: 8px 4px;
        text-align: center;
        font-size: 0.75rem;
        font-weight: 500;
    }}
    .receipts-calendar td {{
        border: 1px solid {GREY};
        padding: 8px 6px;
        vertical-align: top;
        height: 82px;
        font-size: 0.7rem;
    }}
    .receipts-calendar .day-num {{
        font-weight: 600;
        font-size: 0.85rem;
        color: {GRAPHITE};
        margin-bottom: 6px;
    }}
    .receipts-calendar .day-today {{
        border: 2px solid {ORANGE} !important;
    }}
    .receipts-calendar .day-today .day-num {{
        color: {ORANGE};
        font-weight: 700;
    }}
    .receipts-calendar .day-total {{
        font-weight: 700;
        font-size: 0.85rem;
        color: {ORANGE};
        cursor: pointer;
    }}
    .receipts-calendar .day-cell:hover {{
        background: #FFF5F3;
    }}

    /* Tooltip */
    .tooltip-wrapper {{
        position: relative;
        display: inline-block;
        cursor: pointer;
    }}
    .tooltip-wrapper .tooltip-text {{
        visibility: hidden;
        opacity: 0;
        background: #333;
        color: #fff;
        font-size: 0.7rem;
        border-radius: 8px;
        padding: 10px 12px;
        position: absolute;
        z-index: 100;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%);
        white-space: normal;
        min-width: 200px;
        max-width: 300px;
        text-align: left;
        line-height: 1.5;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        transition: opacity 0.15s;
        pointer-events: none;
    }}
    .tooltip-wrapper:hover .tooltip-text {{
        visibility: visible;
        opacity: 1;
    }}
    .tooltip-text .tt-line {{
        padding: 2px 0;
        border-bottom: 1px solid rgba(255,255,255,0.12);
    }}
    .tooltip-text .tt-line:last-child {{
        border-bottom: none;
    }}

    .tag-komplekt {{ background: #EEF5FF; color: #1565C0; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; }}
    .tag-stroyka {{ background: #F3E5F5; color: #7B1FA2; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; }}
    .tag-received {{ background: #E8F5E9; color: #2E7D32; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; }}
    .tag-pending {{ background: #FFF8E1; color: #F57F17; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; }}
    
    .pct-green {{ color: #2E7D32; font-weight: 600; }}
    .pct-neutral {{ color: #888; font-weight: 500; }}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ЗАГРУЗКА ЛИСТА «РАЗРАБОТКА» (новый источник)
# ═══════════════════════════════════════════════════════════════════

DEV_SHEET_ID = "1_avo4Z4zqQmee3MWwzKGWnnwYTfRlg0ehz5kRnyHQF0"
DEV_SHEET_GID = 1010682300

def _get_google_token():
    """Получить или обновить Google OAuth токен."""
    # Пробуем Streamlit secrets (для облака), затем локальный файл
    try:
        client_id = st.secrets["google_client_id"]
        client_secret = st.secrets["google_client_secret"]
        refresh_token = st.secrets["google_refresh_token"]
    except Exception:
        # Локальный запуск — читаем из файлов
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

    # Обновляем access token
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


def _is_green(bg_color):
    """Проверяет, зелёная ли заливка у ячейки."""
    if not bg_color:
        return False
    r = bg_color.get('red', 0) or 0
    g = bg_color.get('green', 0) or 0
    b = bg_color.get('blue', 0) or 0
    # Зелёный: green > 0.85, green > red, green > blue
    return g > 0.85 and g > r and g > b


@st.cache_data(ttl=600)
def load_dev_sheet():
    """Загружает лист «Разработка» через Google Sheets API с форматированием."""
    access_token = _get_google_token()
    if not access_token:
        return None, None, None

    sheet_id = DEV_SHEET_ID
    gid = DEV_SHEET_GID

    try:
        # 1. Получаем название листа
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            info = json.loads(resp.read())

        sheet_name = None
        for s in info.get('sheets', []):
            if s['properties']['sheetId'] == gid:
                sheet_name = s['properties']['title']
                break
        if not sheet_name:
            return None, None, None

        # 2. Получаем значения
        encoded_name = urllib.parse.quote(sheet_name, safe='')
        values_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_name}'
        req = urllib.request.Request(values_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            values_data = json.loads(resp.read())
        rows_val = values_data.get('values', [])

        # 3. Получаем форматирование (цвета фона).
        # Берём только нужный диапазон, иначе Google API возвращает
        # большой gridData и облачная страница иногда срывает загрузку.
        range_param = f"'{sheet_name}'!A1:U600"
        fields = 'sheets(data(rowData(values(effectiveFormat(backgroundColor)))))'
        fmt_url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?includeGridData=true&ranges={urllib.parse.quote(range_param, safe="")}&fields={urllib.parse.quote(fields, safe="()")}'
        req = urllib.request.Request(fmt_url)
        req.add_header('Authorization', f'Bearer {access_token}')
        with urllib.request.urlopen(req, timeout=30) as resp:
            fmt_data = json.loads(resp.read())

        rows_fmt = []
        try:
            rows_fmt = fmt_data['sheets'][0]['data'][0].get('rowData', [])
        except (KeyError, IndexError):
            pass

    except Exception:
        # Если любой API-запрос упал — возвращаем None, страница не крашится
        return None, None, None

    # 4. Парсим месяц из заголовка
    month_label = ""
    if len(rows_val) > 1:
        row1 = rows_val[1] if len(rows_val) > 1 else []
        title_part = row1[1].strip() if len(row1) > 1 else ""
        month_label = f"План на месяц · {title_part}" if title_part else ""

    # ── Вспомогательные функции ──
    def safe_val(r, c):
        if r >= len(rows_val) or c >= len(rows_val[r]):
            return ""
        return rows_val[r][c].strip().replace('\u00A0', ' ').replace('\\-', '-')

    def parse_num(s):
        if not isinstance(s, str):
            return 0
        s = s.strip().replace('\u00A0', ' ').replace('"', '')
        if not s or s in ('', '—', '-'):
            return 0
        s = s.replace(' ', '').replace(',', '.')
        try:
            return int(float(s))
        except ValueError:
            return 0

    def green_amount(r, c):
        """Возвращает сумму, если ячейка зелёная, иначе 0."""
        if r >= len(rows_fmt):
            return 0
        row = rows_fmt[r]
        if 'values' not in row or c >= len(row['values']):
            return 0
        fmt = row['values'][c].get('effectiveFormat', {})
        bg = fmt.get('backgroundColor', {})
        if _is_green(bg):
            return parse_num(safe_val(r, c))
        return 0

    # ── Таблица 1: «ИСПОЛНИТЬ ОБЯЗАТЕЛЬСТВА — ЗАКРЫТЬ ЭТАПЫ» ──
    dev_projects = []
    table1_start = None
    for r in range(len(rows_val)):
        cell = safe_val(r, 1)
        if 'ИСПОЛНИТЬ ОБЯЗАТЕЛЬСТВА' in cell.upper() or 'ИСПОЛНИТЬ ОБЯЗАТЕЛЬСТВА' in cell:
            table1_start = r + 2  # данные через 2 строки после заголовка
            break

    if table1_start:
        for r in range(table1_start, len(rows_val)):
            proj_name = safe_val(r, 1)
            if not proj_name:
                # Пустая строка — конец таблицы или пропуск
                if r > table1_start + 1:
                    break
                continue
            # Проверяем, не наткнулись ли на следующий блок
            if 'KPI' in safe_val(r, 1).upper() or 'ВНЕ ПЛАНА' in safe_val(r, 1).upper():
                break

            manager = safe_val(r, 2)
            designer = safe_val(r, 3)
            engineer = safe_val(r, 4)

            # Суммы этапов (колонки F-K = индексы 5-10)
            stage_total = 0
            green_total = 0
            for c in range(5, 11):
                amt = parse_num(safe_val(r, c))
                stage_total += amt
                green_total += green_amount(r, c)

            if stage_total > 0:
                dev_projects.append({
                    "Проект": proj_name,
                    "Проджект": manager,
                    "Дизайнер": designer,
                    "Проектировщик": engineer,
                    "Сумма": stage_total,
                    "Выполнена": green_total,
                })

    dev_total = sum(p["Сумма"] for p in dev_projects)
    dev_closed = sum(p["Выполнена"] for p in dev_projects)
    dev_pct = (dev_closed / dev_total * 100) if dev_total > 0 else 0

    # ── Таблица 2: «ПРИВЛЕЧЬ АВАНСЫ НА СЧЕТ» ──
    money_projects = []
    table2_start = None
    for r in range(len(rows_val)):
        cell = safe_val(r, 1)
        if 'ПРИВЛЕЧЬ АВАНСЫ' in cell.upper() or 'ПРИВЛЕЧЬ АВАНСЫ' in cell:
            table2_start = r + 2
            break

    if table2_start:
        for r in range(table2_start, len(rows_val)):
            proj_name = safe_val(r, 1)
            if not proj_name:
                if r > table2_start + 1:
                    break
                continue
            if 'БЛОК СТАТИСТИКА' in safe_val(r, 1).upper() or 'БЛОК СТАТИСТИКА' in safe_val(r, 0).upper():
                break

            manager = safe_val(r, 2)
            designer = safe_val(r, 3)
            engineer = safe_val(r, 4)

            # Суммы этапов (колонки F-K = индексы 5-10)
            stage_total = 0
            green_total = 0
            for c in range(5, 11):
                amt = parse_num(safe_val(r, c))
                stage_total += amt
                green_total += green_amount(r, c)

            if stage_total > 0:
                stage_names = []
                for c, name_col in [(5, 'I'), (6, 'II'), (7, 'III'), (8, 'IV'), (9, 'V'), (10, 'ФИНАЛ')]:
                    amt = parse_num(safe_val(r, c))
                    if amt > 0:
                        stage_names.append(f"{name_col} э")
                justification = " · ".join(stage_names) if stage_names else ""

                money_projects.append({
                    "Проект": proj_name,
                    "Проджект": manager,
                    "Дизайнер": designer,
                    "Проектировщик": engineer,
                    "Сумма": stage_total,
                    "Обоснование": justification,
                    "Получена": green_total,
                })

    money_total = sum(p["Сумма"] for p in money_projects)
    money_received = sum(p["Получена"] for p in money_projects)
    money_pct = (money_received / money_total * 100) if money_total > 0 else 0

    # ── KPI: проценты выполнения и разбивка перешло/новое ──
    def parse_pct(s):
        """Парсит строку вида '6,0%' в float."""
        if not isinstance(s, str):
            return 0
        try:
            return float(s.replace('%', '').replace(',', '.').strip())
        except ValueError:
            return 0

    dev_kpi_pct = 0
    dev_carry = 0
    dev_new = 0
    money_kpi_pct = 0
    money_carry = 0
    money_new = 0

    for r in range(len(rows_val)):
        c1 = safe_val(r, 1)

        # KPI 1 — процент выполнения разработки
        if 'KPI 1' in c1.upper():
            dev_kpi_pct = parse_pct(safe_val(r, 3))

        # KPI 1 — перешло / новое (ищем «перешло с прошл.мес» в колонке 8)
        if 'перешло с прошл' in safe_val(r, 8).lower():
            dev_carry = parse_num(safe_val(r + 1, 8))
            dev_new = parse_num(safe_val(r + 1, 9))

        # KPI 2 — процент выполнения привлечения денег
        if 'KPI 2' in c1.upper():
            money_kpi_pct = parse_pct(safe_val(r, 3))

        # KPI 2 — перешло / новое (ищем строку где в колонках 8 и 9 числа, а колонка 10 совпадает с money_total)
        if parse_num(safe_val(r, 8)) > 0 and parse_num(safe_val(r, 9)) > 0:
            if parse_num(safe_val(r, 10)) == money_total:
                money_carry = parse_num(safe_val(r, 8))
                money_new = parse_num(safe_val(r, 9))

    # ── KPI: сводка по проджектам ──
    def parse_kpi_managers(kpi_label):
        """Парсит таблицу проджектов после KPI-блока. Возвращает список словарей."""
        managers = []
        in_kpi = False
        in_table = False
        for r in range(len(rows_val)):
            c1 = safe_val(r, 1)
            if kpi_label in c1.upper():
                in_kpi = True
                continue
            if not in_kpi:
                continue
            # Нашли строку-заголовок «проджекты»
            if not in_table and 'проджект' in c1.lower():
                in_table = True
                continue
            if not in_table:
                continue
            name = safe_val(r, 1)
            if not name or 'руководитель' in name.lower():
                break
            plan = parse_num(safe_val(r, 2))
            fact = parse_num(safe_val(r, 3))
            pct = parse_pct(safe_val(r, 5))
            if plan > 0 or fact > 0:
                managers.append({
                    "Проджект": name,
                    "План": plan,
                    "Факт": fact,
                    "%": pct,
                })
        return managers

    dev_managers = parse_kpi_managers('KPI 1')
    money_managers = parse_kpi_managers('KPI 2')

    # ── Календарь закрытий (KPI 1) ──
    # Даты лежат в столбцах M-U (индексы 12-20) тех же строк 26-37
    # Порядок: P=Iэ, Q=IIэ, R=IIIэ, S=IVэ, T=Vэ, U=ФИНАЛ (индексы 15-20)
    # Сопоставляем с суммами этапов из F-K (индексы 5-10)
    dev_calendar = {}  # {день: [{"amount":..., "project":..., "stage":...}, ...]}
    for r in range(table1_start, min(table1_start + 20, len(rows_val))):
        proj_name = safe_val(r, 1)
        if not proj_name:
            continue
        # Проверяем, не вышли ли из таблицы
        if 'KPI' in safe_val(r, 1).upper() or 'ВНЕ ПЛАНА' in safe_val(r, 1).upper():
            break
        for stage_idx, (amount_col, date_col, stage_name) in enumerate([
            (5, 15, 'I э'), (6, 16, 'II э'), (7, 17, 'III э'),
            (8, 18, 'IV э'), (9, 19, 'V э'), (10, 20, 'Финал')
        ]):
            amt = parse_num(safe_val(r, amount_col))
            date_str = safe_val(r, date_col)
            if amt > 0 and date_str:
                # Парсим дату формата ДД.ММ
                parts = date_str.split('.')
                if len(parts) == 2:
                    try:
                        day = int(parts[0])
                        if day not in dev_calendar:
                            dev_calendar[day] = []
                        dev_calendar[day].append({
                            "amount": amt,
                            "project": proj_name,
                            "stage": stage_name,
                        })
                    except ValueError:
                        pass

    # ── Календарь поступлений (БЛОК СТАТИСТИКА ПРИХОДОВ) ──
    money_calendar = {}
    money_next_month_total = 0
    money_next_month_items = []
    stats_start = None
    for r in range(len(rows_val)):
        if 'БЛОК СТАТИСТИКА' in safe_val(r, 0).upper() or 'БЛОК СТАТИСТИКА' in safe_val(r, 1).upper():
            stats_start = r + 2
            break

    if stats_start:
        from datetime import date as dt_date
        current_month = dt_date.today().month
        next_month_num = 1 if current_month == 12 else current_month + 1
        for r in range(stats_start, len(rows_val)):
            proj_name = safe_val(r, 1)
            if not proj_name or 'ИТОГО' in safe_val(r, 0).upper():
                break
            amount = parse_num(safe_val(r, 2))
            date_str = safe_val(r, 8)
            status = safe_val(r, 4)
            if amount > 0 and date_str and 'оплачено' not in status.lower():
                parts = date_str.split('.')
                if len(parts) == 2:
                    try:
                        day = int(parts[0])
                        mon = int(parts[1])
                        if mon == current_month:
                            if day not in money_calendar:
                                money_calendar[day] = []
                            money_calendar[day].append({
                                "amount": amount,
                                "project": proj_name,
                            })
                        elif mon == next_month_num:
                            money_next_month_total += amount
                            money_next_month_items.append({
                                "amount": amount,
                                "project": proj_name,
                                "stage": safe_val(r, 3),
                                "status": status,
                                "comment": safe_val(r, 9) or safe_val(r, 10),
                                "date": date_str,
                            })
                    except ValueError:
                        pass

    dev_section = {
        "total": dev_total,
        "closed": dev_closed,
        "pct": dev_pct,
        "kpi_pct": dev_kpi_pct,
        "carry": dev_carry,
        "new": dev_new,
        "managers": dev_managers,
        "calendar": dev_calendar,
        "projects": dev_projects,
    }
    money_section = {
        "total": money_total,
        "received": money_received,
        "pct": money_pct,
        "kpi_pct": money_kpi_pct,
        "carry": money_carry,
        "new": money_new,
        "managers": money_managers,
        "calendar": money_calendar,
        "next_month_total": money_next_month_total,
        "next_month_items": money_next_month_items,
        "projects": money_projects,
    }

    return dev_section, money_section, month_label


# ═══════════════════════════════════════════════════════════════════
# ЗАГРУЗКА СТАРОГО ЛИСТА ПЛАНОВ (для agent и sales)
# ═══════════════════════════════════════════════════════════════════

PLANS_SHEET_ID = "1J5wttPgifHlCWUf5SABupr93-0ckTxX55UX6JOEOtWA"
PLANS_URL = f"https://docs.google.com/spreadsheets/d/{PLANS_SHEET_ID}/export?format=csv"

@st.cache_data(ttl=600)
def load_plans_legacy():
    """Загружает старый лист Планов — только agent и sales."""
    req = urllib.request.Request(PLANS_URL)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    def parse_num(s):
        if not isinstance(s, str):
            return 0
        s = s.strip().replace('\u00A0', ' ').replace('"', '')
        if not s or s in ('', '—'):
            return 0
        s = s.replace(' ', '').replace(',', '.')
        try:
            return int(float(s))
        except ValueError:
            return 0

    def col(r, i):
        if r >= len(rows) or i >= len(rows[r]):
            return ""
        return rows[r][i].strip().replace('\u00A0', ' ').replace('\\-', '-')

    sections = {}

    # Резервный источник для разработки и привлечения денег.
    # Он нужен для облака, если OAuth к отдельному листу «Разработка» недоступен.
    def find_row(text, start=0):
        text = text.lower()
        for i in range(start, len(rows)):
            if text in col(i, 1).lower():
                return i
        return -1

    def parse_plan_projects(start_row, end_row, money_mode=False):
        projects = []
        for r in range(start_row, min(end_row, len(rows))):
            name = col(r, 1)
            if not name:
                continue
            if money_mode:
                amount = parse_num(col(r, 2))
                if amount > 0:
                    projects.append({
                        "Проект": name,
                        "Проджект": "",
                        "Дизайнер": "",
                        "Проектировщик": "",
                        "Сумма": amount,
                        "Обоснование": col(r, 3),
                        "Получена": 0,
                    })
            else:
                amount = sum(parse_num(col(r, c)) for c in range(5, 11))
                if amount > 0:
                    projects.append({
                        "Проект": name,
                        "Проджект": col(r, 2),
                        "Дизайнер": col(r, 3),
                        "Проектировщик": col(r, 4),
                        "Сумма": amount,
                        "Выполнена": 0,
                    })
        return projects

    dev_row = find_row("исполнить обязательства")
    dev_total = parse_num(col(dev_row, 3)) if dev_row >= 0 else 0
    dev_carry = parse_num(col(dev_row + 1, 3)) if dev_row >= 0 else 0
    dev_new = parse_num(col(dev_row + 2, 3)) if dev_row >= 0 else 0
    dev_projects = parse_plan_projects(dev_row + 4, 27, money_mode=False) if dev_row >= 0 else []
    sections["dev"] = {
        "total": dev_total,
        "closed": 0,
        "pct": 0,
        "kpi_pct": 0,
        "carry": dev_carry,
        "new": dev_new,
        "managers": [],
        "calendar": {},
        "projects": dev_projects,
    }

    money_row = find_row("привлечь деньги")
    money_total = parse_num(col(money_row, 3)) if money_row >= 0 else 0
    money_carry = parse_num(col(money_row + 1, 3)) if money_row >= 0 else 0
    money_new = parse_num(col(money_row + 2, 3)) if money_row >= 0 else 0
    money_projects = parse_plan_projects(money_row + 6, 57, money_mode=True) if money_row >= 0 else []
    sections["money"] = {
        "total": money_total,
        "received": 0,
        "pct": 0,
        "kpi_pct": 0,
        "carry": money_carry,
        "new": money_new,
        "managers": [],
        "calendar": {},
        "next_month_total": 0,
        "next_month_items": [],
        "projects": money_projects,
    }

    # Реализация и продажи остаются в старой таблице планов.
    agent_total = parse_num(col(59, 3))
    sections["agent"] = {"total": agent_total}

    sales_contracts = parse_num(col(64, 3))
    sales_advances = parse_num(col(65, 3))
    sections["sales"] = {
        "contracts": sales_contracts,
        "advances": sales_advances,
        "total": sales_contracts + sales_advances,
    }

    return sections


# ═══════════════════════════════════════════════════════════════════
# ЗАГРУЗКА ПРИХОДОВ
# ═══════════════════════════════════════════════════════════════════

RECEIPTS_SHEET_ID = "11f_FJivwUEPxEF2QgHExdo1O1QBllLjNcY_dfsz_ac4"
RECEIPTS_GID = "2015821513"
RECEIPTS_URL = f"https://docs.google.com/spreadsheets/d/{RECEIPTS_SHEET_ID}/export?format=csv&gid={RECEIPTS_GID}"

@st.cache_data(ttl=600)
def load_receipts():
    req = urllib.request.Request(RECEIPTS_URL)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode('utf-8')

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    def parse_num(s):
        if not isinstance(s, str):
            return 0
        s = s.strip().replace('\u00A0', ' ').replace('"', '')
        if not s or s in ('', '—'):
            return 0
        s = s.replace(' ', '').replace(',', '.')
        try:
            return int(float(s))
        except ValueError:
            return 0

    def col(r, i):
        if r >= len(rows) or i >= len(rows[r]):
            return ""
        return rows[r][i].strip().replace('\u00A0', ' ').replace('\\-', '-')

    month_name = col(1, 7).strip()
    update_date = col(2, 2).strip()

    all_transactions = []
    # Ищем начало данных — строка с заголовком «ПЛАН дата получения»
    data_start = 6
    for r in range(4, min(30, len(rows))):
        if 'план дата получения' in col(r, 1).lower():
            data_start = r + 2  # пропускаем строку с номерами колонок
            break

    for r in range(data_start, len(rows)):
        if not rows[r] or len(rows[r]) < 5:
            continue

        # В актуальном листе колонка A пустая, а данные начинаются с B.
        # В старой версии в A стоял флаг TRUE/FALSE. Поддерживаем оба формата:
        # пустая ячейка A означает активную строку, FALSE — исключённую.
        active_marker = col(r, 0).upper()
        if active_marker not in ('', 'TRUE', 'FALSE'):
            continue
        active = active_marker != 'FALSE'

        plan_date = col(r, 1)
        fact_date = col(r, 2)
        received = col(r, 3)
        amount = parse_num(col(r, 4))
        direction = col(r, 5)
        pay_format = col(r, 6)
        project_acct = col(r, 7)
        project_name = col(r, 8)
        deal_type = col(r, 9)
        responsible = col(r, 10)
        supplier = col(r, 11)
        description = col(r, 12)
        group = col(r, 13)
        manager_comment = col(r, 14)

        if amount > 0 and (active or received == 'да'):
            all_transactions.append({
                "active": active,
                "plan_date": plan_date,
                "fact_date": fact_date,
                "received": received == "да",
                "amount": amount,
                "direction": direction,
                "pay_format": pay_format,
                "project_acct": project_acct,
                "project_name": project_name,
                "deal_type": deal_type,
                "responsible": responsible,
                "supplier": supplier,
                "description": description,
                "group": group,
                "manager_comment": manager_comment,
            })

    # ── Поиск итогов по меткам (устойчиво к добавлению строк) ──
    def find_row(keyword, start=4):
        for r in range(start, len(rows)):
            c1 = col(r, 1).lower()
            if keyword in c1:
                return r
        return -1

    total_plan = 0
    komplekt_plan = 0
    stroyka_plan = 0
    total_received = 0
    komplekt_received = 0
    stroyka_received = 0
    total_remaining = 0
    pct_complete = 0

    # При плане отдела
    r_plan = find_row('при плане отдела')
    if r_plan >= 0:
        total_plan = parse_num(col(r_plan, 4))

    # Получено
    r_recv = find_row('получено')
    if r_recv >= 0:
        total_received = parse_num(col(r_recv, 4))
        # Комплектация и Стройка — следующие две строки
        komplekt_received = parse_num(col(r_recv + 1, 4))
        stroyka_received = parse_num(col(r_recv + 2, 4))

    # Осталось до плана
    r_rem = find_row('осталось до плана')
    if r_rem >= 0:
        total_remaining = parse_num(col(r_rem, 4))

    # Выполнение плана
    r_pct = find_row('выполнение плана')
    if r_pct >= 0:
        pct_str = col(r_pct, 4).replace('%', '').strip()
        try:
            pct_complete = float(pct_str.replace(',', '.'))
        except ValueError:
            pct_complete = 0

    calendar_days = {}
    for t in all_transactions:
        if t['active'] and not t['received'] and t['plan_date'] and t['plan_date'] != 'без даты':
            try:
                day = int(t['plan_date'])
                if day not in calendar_days:
                    calendar_days[day] = []
                calendar_days[day].append({
                    "amount": t['amount'],
                    "direction": t['direction'],
                    "project": t['project_name'] or t['project_acct'] or '',
                    "supplier": t['supplier'] or '',
                    "description": t['description'] or '',
                })
            except ValueError:
                pass

    today = date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    weekly = {}
    for week_idx, week_days in enumerate(cal, start=1):
        week_total = 0
        week_count = 0
        for d in week_days:
            if d > 0 and d in calendar_days:
                week_total += sum(item['amount'] for item in calendar_days[d])
                week_count += len(calendar_days[d])
        if week_total > 0:
            weekly[week_idx] = {"total": week_total, "count": week_count}

    return {
        "month_name": month_name,
        "update_date": update_date,
        "transactions": all_transactions,
        "total_plan": total_plan,
        "total_received": total_received,
        "total_remaining": total_remaining,
        "pct_complete": pct_complete,
        "komplekt_plan": komplekt_plan,
        "komplekt_received": komplekt_received,
        "stroyka_plan": stroyka_plan,
        "stroyka_received": stroyka_received,
        "calendar_days": calendar_days,
        "weekly": weekly,
    }


# ═══════════════════════════════════════════════════════════════════
# ЗАГРУЗКА ВСЕХ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════

dev, money, month_label = load_dev_sheet()
legacy = load_plans_legacy()
receipts = load_receipts()

# ── Вспомогательные ─────────────────────────────────────────────
def fmt_rub(v):
    if v == 0:
        return "—"
    return f"{v:,.0f} ₽".replace(",", " ")

def fmt_num(v):
    if v == 0:
        return "0"
    return f"{v:,.0f}".replace(",", " ")

def pct_color(value):
    """Цвет выполнения: до 50% красный, 50-80% оранжевый, выше 80% зелёный."""
    if value < 50:
        return ORANGE
    if value <= 80:
        return "#F57F17"
    return "#2E7D32"

# ── Заголовок ───────────────────────────────────────────────────
st.markdown(f'<h2 style="font-weight:300;color:#252525;"><img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">{month_label or "Планы бюро"}</h2>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# КАРТОЧКИ
# ═══════════════════════════════════════════════════════════════════

d_t = dev.get("total", 0) if dev else 0
m_t = money.get("total", 0) if money else 0
# Реализация берётся из актуального листа «Приходы», а не из старого листа Планов.
a_t = receipts.get("total_plan", 0) if receipts else 0
s_t = legacy.get("sales", {}).get("total", 0)

grand_total = d_t + m_t + a_t + s_t

# Значения для карточек
dev_carry = dev.get("carry", 0) if dev else 0
dev_new = dev.get("new", 0) if dev else 0
dev_kpi_pct = dev.get("kpi_pct", 0) if dev else 0
money_carry = money.get("carry", 0) if money else 0
money_new = money.get("new", 0) if money else 0
money_kpi_pct = money.get("kpi_pct", 0) if money else 0
receipts_pct = receipts.get("pct_complete", 0)
# Доля перенесённых поступлений в общем плане «Привлечь деньги».
next_month_total = money.get("next_month_total", 0) if money else 0
next_month_share = (next_month_total / m_t * 100) if m_t > 0 else 0

st.markdown(f"""
<div style="display:flex; gap:16px; align-items:stretch;">
    <div class="plan-card" style="flex:1;">
        <div class="plan-card-title"><span class="block-label block-dev">I</span> Разработка</div>
        <div class="plan-card-value">{fmt_rub(d_t)}</div>
        <div class="plan-card-sub">закрыть этапы</div>
        <div class="plan-card-sub">перешло: {fmt_rub(dev_carry)} · новое: {fmt_rub(dev_new)}</div>
        <div class="plan-card-sub" style="color:{pct_color(dev_kpi_pct)};font-size:1.25rem;font-weight:700;">{dev_kpi_pct:.1f}%</div>
    </div>
    <div class="plan-card" style="flex:1;">
        <div class="plan-card-title"><span class="block-label block-money">II</span> Привлечь деньги</div>
        <div class="plan-card-value">{fmt_rub(m_t)}</div>
        <div class="plan-card-sub">поступления</div>
        <div class="plan-card-sub">перешло: {fmt_rub(money_carry)} · новое: {fmt_rub(money_new)}</div>
        <div class="plan-card-sub" style="color:{pct_color(money_kpi_pct)};font-size:1.25rem;font-weight:700;">{money_kpi_pct:.1f}%</div>
        <div class="plan-card-sub" style="color:{ORANGE};">из общего плана: {next_month_share:.1f}% · уже перенесено на следующий месяц</div>
    </div>
    <div class="plan-card" style="flex:1;">
        <div class="plan-card-title"><span class="block-label block-agent">III</span> Реализация</div>
        <div class="plan-card-value">{fmt_rub(a_t)}</div>
        <div class="plan-card-sub">агентские / перепродажи</div>
        <div class="plan-card-sub" style="color:{pct_color(receipts_pct)};font-size:1.25rem;font-weight:700;">{receipts_pct:.1f}%</div>
    </div>
    <div class="plan-card" style="flex:1;">
        <div class="plan-card-title"><span class="block-label block-sales">IV</span> Продажи</div>
        <div class="plan-card-value">{fmt_rub(s_t)}</div>
        <div class="plan-card-sub">договоры: {fmt_rub(legacy.get('sales', {}).get('contracts', 0))}</div>
        <div class="plan-card-sub">авансы: {fmt_rub(legacy.get('sales', {}).get('advances', 0))}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f"""
<div style="text-align:center; margin: 16px 0;">
    <span style="font-size:0.85rem;color:#888;">ОБЩИЙ ПЛАН НА МЕСЯЦ</span><br>
    <span style="font-size:2.2rem;font-weight:700;color:{GRAPHITE};">{fmt_rub(grand_total)}</span>
</div>
""", unsafe_allow_html=True)

# ── Дерево расшифровки ──────────────────────────────────────────
advances = legacy.get('sales', {}).get('advances', 0)
contracts = legacy.get('sales', {}).get('contracts', 0)
receipts_total = m_t + a_t + advances  # деньги + реализация + авансы
closing_total = d_t                    # закрыть этапы = уже получены
# Процент: (привлечь деньги + реализация) / общий план, без авансов
receipts_pct = ((m_t + a_t) / grand_total * 100) if grand_total > 0 else 0

st.markdown(f"""
<div style="display:flex; gap:16px; margin: 8px 0 24px 0;">
    <div style="flex:1; background:{WHITE}; border:1px solid {GREY}; border-radius:16px; padding:24px;">
        <div style="font-size:1.1rem; font-weight:600; color:{GRAPHITE}; margin-bottom:2px;">Поступления на счёт в банк</div>
        <div style="font-size:0.8rem; color:#aaa; margin-bottom:12px;">от новых и завершенных обязательств</div>
        <div style="font-size:1.6rem; font-weight:700; color:{GRAPHITE}; margin-bottom:16px;">{fmt_rub(receipts_total)}</div>
        <div style="display:flex; flex-direction:column; gap:6px;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#555;">
                <span>Привлечь деньги</span>
                <span style="font-weight:500;">{fmt_rub(m_t)}</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#555;">
                <span>Реализация</span>
                <span style="font-weight:500;">{fmt_rub(a_t)}</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#555;">
                <span>Авансы</span>
                <span style="font-weight:500;">{fmt_rub(advances)}</span>
            </div>
        </div>
    </div>
    <div style="flex:1; background:{WHITE}; border:1px solid {GREY}; border-radius:16px; padding:24px;">
        <div style="font-size:1.1rem; font-weight:600; color:{GRAPHITE}; margin-bottom:2px;">Только закрытие обязательств</div>
        <div style="font-size:0.8rem; color:#aaa; margin-bottom:12px;">эти деньги уже получены</div>
        <div style="font-size:1.6rem; font-weight:700; color:{GRAPHITE};">{fmt_rub(closing_total)}</div>
    </div>
    <div style="flex:1; background:{WHITE}; border:1px solid {GREY}; border-radius:16px; padding:24px;">
        <div style="font-size:1.1rem; font-weight:600; color:{GRAPHITE}; margin-bottom:2px;">Новые обязательства</div>
        <div style="font-size:0.8rem; color:#aaa; margin-bottom:12px;">договоры в работе</div>
        <div style="font-size:1.6rem; font-weight:700; color:{GRAPHITE};">{fmt_rub(contracts)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ДЕТАЛИЗАЦИЯ ПО ПРОЕКТАМ (РАЗРАБОТКА)
# ═══════════════════════════════════════════════════════════════════

if dev is None or money is None:
    st.warning("Не удалось загрузить лист «Разработка». Проверьте доступ к Google API.")
else:
    st.markdown("### ▸ Детализация по проектам (Разработка)")

    tab1, tab2 = st.tabs(["Разработка — закрыть этапы", "Привлечь деньги"])

    with tab1:
        # KPI-сводка по проджектам
        dev_managers = dev.get("managers", [])
        if dev_managers:
            st.markdown("#### KPI 1 · по проджектам")
            df_mgr = pd.DataFrame(dev_managers)
            html = '<table class="plan-detail-table"><thead><tr>'
            html += '<th>Проджект</th><th>План</th><th>Факт</th><th>% выполнения</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_mgr.iterrows():
                pct_val = row["%"]
                pct_color = "#2E7D32" if pct_val >= 50 else "#F57F17" if pct_val >= 25 else ORANGE
                html += '<tr>'
                html += f'<td>{row["Проджект"]}</td>'
                html += f'<td>{fmt_rub(row["План"])}</td>'
                html += f'<td>{fmt_rub(row["Факт"])}</td>'
                html += f'<td style="color:{pct_color};font-weight:600;">{pct_val:.1f}%</td>'
                html += '</tr>'
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Таблица проектов с фильтрами
        st.markdown("#### Закрыть этапы · по проектам")
        dev_projects = dev.get("projects", [])
        if dev_projects:
            df_dev = pd.DataFrame(dev_projects)
            # Фильтры
            all_proj = sorted(set(df_dev["Проект"].dropna()))
            all_designers = sorted(set(df_dev["Дизайнер"].dropna()))
            all_engineers = sorted(set(df_dev["Проектировщик"].dropna()))
            all_mgrs = sorted(set(df_dev["Проджект"].dropna()))

            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                f_proj = st.multiselect("Проект", all_proj, default=[], key="f_dev_proj")
            with fc2:
                f_mgr = st.multiselect("Проджект", all_mgrs, default=[], key="f_dev_mgr")
            with fc3:
                f_des = st.multiselect("Дизайнер", all_designers, default=[], key="f_dev_des")
            with fc4:
                f_eng = st.multiselect("Проектировщик", all_engineers, default=[], key="f_dev_eng")

            # Применяем фильтры
            if f_proj:
                df_dev = df_dev[df_dev["Проект"].isin(f_proj)]
            if f_mgr:
                df_dev = df_dev[df_dev["Проджект"].isin(f_mgr)]
            if f_des:
                df_dev = df_dev[df_dev["Дизайнер"].isin(f_des)]
            if f_eng:
                df_dev = df_dev[df_dev["Проектировщик"].isin(f_eng)]

            df_dev = df_dev.sort_values("Сумма", ascending=False)

            html = '<table class="plan-detail-table"><thead><tr>'
            html += '<th>Проект</th><th>Проджект</th><th>Дизайнер</th><th>Проектировщик</th><th>Сумма</th><th>Выполнена</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_dev.iterrows():
                html += '<tr>'
                html += f'<td>{row["Проект"]}</td>'
                html += f'<td>{row["Проджект"]}</td>'
                html += f'<td>{row["Дизайнер"]}</td>'
                html += f'<td>{row["Проектировщик"]}</td>'
                html += f'<td>{fmt_rub(row["Сумма"])}</td>'
                closed = row["Выполнена"]
                if closed > 0:
                    html += f'<td><span class="closed-cell">Этап закрыт</span> {fmt_rub(closed)}</td>'
                else:
                    html += '<td><span class="empty-cell">—</span></td>'
                html += '</tr>'

            total_sum = df_dev["Сумма"].sum()
            total_closed = df_dev["Выполнена"].sum()
            pct = (total_closed / total_sum * 100) if total_sum > 0 else 0

            html += f'<tr style="font-weight:700;border-top:2px solid {GRAPHITE};">'
            html += f'<td colspan="4">ИТОГО ({len(df_dev)})</td>'
            html += f'<td>{fmt_rub(total_sum)}</td>'
            html += f'<td>{fmt_rub(total_closed)} <span class="pct-green">{pct:.1f}%</span></td>'
            html += '</tr>'
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("Нет данных по проектам разработки.")

    with tab2:
        # KPI-сводка по проджектам
        money_managers = money.get("managers", [])
        if money_managers:
            st.markdown("#### KPI 2 · по проджектам")
            df_mgr = pd.DataFrame(money_managers)
            html = '<table class="plan-detail-table"><thead><tr>'
            html += '<th>Проджект</th><th>План</th><th>Факт</th><th>% выполнения</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_mgr.iterrows():
                pct_val = row["%"]
                pct_color = "#2E7D32" if pct_val >= 50 else "#F57F17" if pct_val >= 25 else ORANGE
                html += '<tr>'
                html += f'<td>{row["Проджект"]}</td>'
                html += f'<td>{fmt_rub(row["План"])}</td>'
                html += f'<td>{fmt_rub(row["Факт"])}</td>'
                html += f'<td style="color:{pct_color};font-weight:600;">{pct_val:.1f}%</td>'
                html += '</tr>'
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Таблица проектов с фильтрами
        st.markdown("#### Привлечь деньги · по проектам")
        money_projects = money.get("projects", [])
        if money_projects:
            df_money = pd.DataFrame(money_projects)
            # Фильтры
            all_proj = sorted(set(df_money["Проект"].dropna()))
            all_mgrs = sorted(set(df_money["Проджект"].dropna()))
            all_designers = sorted(set(df_money["Дизайнер"].dropna()))
            all_engineers = sorted(set(df_money["Проектировщик"].dropna()))

            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                f_proj2 = st.multiselect("Проект", all_proj, default=[], key="f_money_proj")
            with fc2:
                f_mgr2 = st.multiselect("Проджект", all_mgrs, default=[], key="f_money_mgr")
            with fc3:
                f_des2 = st.multiselect("Дизайнер", all_designers, default=[], key="f_money_des")
            with fc4:
                f_eng2 = st.multiselect("Проектировщик", all_engineers, default=[], key="f_money_eng")

            if f_proj2:
                df_money = df_money[df_money["Проект"].isin(f_proj2)]
            if f_mgr2:
                df_money = df_money[df_money["Проджект"].isin(f_mgr2)]
            if f_des2:
                df_money = df_money[df_money["Дизайнер"].isin(f_des2)]
            if f_eng2:
                df_money = df_money[df_money["Проектировщик"].isin(f_eng2)]

            df_money = df_money.sort_values("Сумма", ascending=False)

            html = '<table class="plan-detail-table"><thead><tr>'
            html += '<th>Проект</th><th>Проджект</th><th>Дизайнер</th><th>Проектировщик</th><th>Обоснование</th><th>Сумма</th><th>Получена</th>'
            html += '</tr></thead><tbody>'
            for _, row in df_money.iterrows():
                html += '<tr>'
                html += f'<td>{row["Проект"]}</td>'
                html += f'<td>{row["Проджект"]}</td>'
                html += f'<td>{row["Дизайнер"]}</td>'
                html += f'<td>{row["Проектировщик"]}</td>'
                html += f'<td>{row["Обоснование"]}</td>'
                html += f'<td>{fmt_rub(row["Сумма"])}</td>'
                received = row["Получена"]
                if received > 0:
                    html += f'<td><span class="closed-cell">Получено</span> {fmt_rub(received)}</td>'
                else:
                    html += '<td><span class="empty-cell">—</span></td>'
                html += '</tr>'

            total_sum = df_money["Сумма"].sum()
            total_received = df_money["Получена"].sum()
            pct = (total_received / total_sum * 100) if total_sum > 0 else 0

            html += f'<tr style="font-weight:700;border-top:2px solid {GRAPHITE};">'
            html += f'<td colspan="5">ИТОГО ({len(df_money)})</td>'
            html += f'<td>{fmt_rub(total_sum)}</td>'
            html += f'<td>{fmt_rub(total_received)} <span class="pct-green">{pct:.1f}%</span></td>'
            html += '</tr>'
            html += '</tbody></table>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.caption("Нет данных по привлечению денег.")

    # ═══════════════════════════════════════════════════════════════
    # КАЛЕНДАРИ ЗАКРЫТИЙ И ПОСТУПЛЕНИЙ
    # ═══════════════════════════════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Календарь закрытий и поступлений")

    cal_tab1, cal_tab2 = st.tabs(["Разработка — закрыть этапы", "Привлечь деньги"])

    today = date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    def render_dev_cal(cal_data, title):
        """Рисует календарь на основе {день: [записи]}."""
        if not cal_data:
            st.caption(f"Нет данных для календаря «{title}».")
            return

        html_cal = '<table class="receipts-calendar"><thead><tr>'
        for dn in day_names:
            html_cal += f'<th>{dn}</th>'
        html_cal += '</tr></thead><tbody>'

        for week in cal:
            html_cal += '<tr>'
            for d in week:
                if d == 0:
                    html_cal += '<td></td>'
                else:
                    is_today = (d == today.day)
                    cell_class = 'day-cell day-today' if is_today else 'day-cell'
                    html_cal += f'<td class="{cell_class}">'
                    html_cal += f'<div class="day-num">{d}</div>'

                    if d in cal_data:
                        items = cal_data[d]
                        total = sum(item['amount'] for item in items)
                        # Tooltip
                        tooltip_lines = []
                        for item in items:
                            proj = item.get('project', '')
                            stage = item.get('stage', '')
                            label = f"{stage}: " if stage else ""
                            tooltip_lines.append(
                                f'<div class="tt-line">{label}{fmt_rub(item["amount"])}<br>'
                                f'<span style="color:#aaa;font-size:0.65rem;">{proj}</span></div>'
                            )
                        tooltip_html = "".join(tooltip_lines).replace('"', '&quot;').replace("'", "&#39;")
                        html_cal += '<div class="tooltip-wrapper">'
                        html_cal += f'<div class="day-total">{fmt_rub(total)}</div>'
                        html_cal += f'<div class="tooltip-text">{tooltip_html}</div>'
                        html_cal += '</div>'

                    html_cal += '</td>'
            html_cal += '</tr>'

        html_cal += '</tbody></table>'
        st.markdown(html_cal, unsafe_allow_html=True)
        st.caption("Наведите на сумму чтобы увидеть проекты и этапы.")

    with cal_tab1:
        dev_cal = dev.get("calendar", {}) if dev else {}
        render_dev_cal(dev_cal, "Закрытие этапов")

    with cal_tab2:
        money_cal = money.get("calendar", {}) if money else {}
        render_dev_cal(money_cal, "Поступления")
        next_m = money.get("next_month_total", 0) if money else 0
        next_items = money.get("next_month_items", []) if money else []
        if next_m > 0:
            tooltip_lines = []
            for item in next_items:
                project = html_lib.escape(str(item.get("project", "—")).strip() or "—")
                stage = html_lib.escape(str(item.get("stage", "—")).strip() or "—")
                planned_date = html_lib.escape(str(item.get("date", "—")).strip() or "—")
                comment = html_lib.escape(str(item.get("comment", "")).strip())
                comment_html = f'<br><span style="color:#c7c7c7;">{comment}</span>' if comment else ""
                tooltip_lines.append(
                    f'<div class="tt-line">{project}<br>'
                    f'<span style="color:#f3b0a8;">{stage} · {fmt_rub(item.get("amount", 0))} · план {planned_date}</span>'
                    f'{comment_html}</div>'
                )
            next_tooltip = "".join(tooltip_lines)
            next_label = (
                f'<span class="tooltip-wrapper next-month-tooltip">'
                f'<strong>{fmt_rub(next_m)}</strong>'
                f'<span class="tooltip-text">{next_tooltip}</span>'
                f'</span>'
            )
            st.markdown(
                f'<div style="margin-top:12px;font-size:0.9rem;color:{GRAPHITE};">'
                f'В следующем месяце ожидается: {next_label} '
                f'<span style="color:#888;">(не успеют получить в этом мес)</span></div>'
                f'<div style="font-size:0.75rem;color:#999;margin-top:4px;">Наведите на сумму, чтобы увидеть проекты, этапы и комментарии.</div>',
                unsafe_allow_html=True
            )

st.markdown("<br><br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ДЕТАЛИЗАЦИЯ ПО ПРОЕКТАМ (РЕАЛИЗАЦИЯ) — оставляем без изменений
# ═══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("### ▸ Детализация по проектам (Реализация)")

update_date = receipts.get('update_date', '')
if update_date:
    st.caption(f"Актуально на {update_date}")

rec_month = receipts['month_name'] or '—'
pct = receipts['pct_complete']
pct_color = "#2E7D32" if pct >= 50 else "#F57F17" if pct >= 25 else ORANGE

# ── 3 карточки ──
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="receipt-stat-card">
        <div class="receipt-stat-label">ПЛАН НА {rec_month}</div>
        <div class="receipt-stat-value" style="color:{GRAPHITE};">{fmt_rub(receipts['total_plan'])}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="receipt-stat-card">
        <div class="receipt-stat-label">ПОЛУЧЕНО</div>
        <div class="receipt-stat-value" style="color:{pct_color};">{fmt_rub(receipts['total_received'])}</div>
        <div style="font-size:0.75rem;color:#888;margin-top:2px;">{pct:.1f}% плана</div>
        <div class="receipt-breakdown">
            К: {fmt_rub(receipts['komplekt_received'])} · С: {fmt_rub(receipts['stroyka_received'])}
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="receipt-stat-card">
        <div class="receipt-stat-label">ОСТАЛОСЬ ДО ПЛАНА</div>
        <div class="receipt-stat-value" style="color:{GRAPHITE};">{fmt_rub(receipts['total_remaining'])}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Календарь ──
st.markdown("#### Календарь предстоящих поступлений")

today = date.today()
cal = calendar.monthcalendar(today.year, today.month)
day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
calendar_days = receipts['calendar_days']

def build_tooltip(items):
    lines = []
    for item in items:
        proj = item['project'] or item['supplier'] or item['description'] or '—'
        d_tag = 'К' if item['direction'] == 'КОМПЛЕКТАЦИЯ' else 'С'
        lines.append(f'<div class="tt-line">{d_tag}: {fmt_rub(item["amount"])}<br><span style="color:#aaa;font-size:0.65rem;">{proj}</span></div>')
    return "".join(lines)

html_cal = '<table class="receipts-calendar"><thead><tr>'
for dn in day_names:
    html_cal += f'<th>{dn}</th>'
html_cal += '</tr></thead><tbody>'

for week in cal:
    html_cal += '<tr>'
    for d in week:
        if d == 0:
            html_cal += '<td></td>'
        else:
            is_today = (d == today.day)
            cell_class = 'day-cell day-today' if is_today else 'day-cell'
            html_cal += f'<td class="{cell_class}">'
            html_cal += f'<div class="day-num">{d}</div>'

            if d in calendar_days:
                items = calendar_days[d]
                total = sum(item['amount'] for item in items)
                tooltip_html = build_tooltip(items)
                tooltip_html_escaped = tooltip_html.replace('"', '&quot;').replace("'", "&#39;")
                html_cal += '<div class="tooltip-wrapper">'
                html_cal += f'<div class="day-total">{fmt_rub(total)}</div>'
                html_cal += f'<div class="tooltip-text">{tooltip_html}</div>'
                html_cal += '</div>'

            html_cal += '</td>'
    html_cal += '</tr>'

html_cal += '</tbody></table>'
st.markdown(html_cal, unsafe_allow_html=True)

st.caption("В календаре — только ожидаемые поступления. Наведите на сумму чтобы увидеть проекты.")

# ── Понедельная разбивка ──
weekly = receipts['weekly']
if weekly:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### По неделям (сколько ещё планируется получить)")

    week_cols = st.columns(len(weekly))
    for i, (wk, data) in enumerate(sorted(weekly.items())):
        with week_cols[i]:
            st.markdown(f"""
            <div class="receipt-stat-card">
                <div class="receipt-stat-label">НЕДЕЛЯ {wk}</div>
                <div class="receipt-stat-value" style="color:{ORANGE};font-size:1.1rem;">{fmt_rub(data['total'])}</div>
                <div style="font-size:0.7rem;color:#888;">{data['count']} пост.</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Таблица всех сделок ──
st.markdown("#### Все сделки реализации")

all_tx = receipts['transactions']
received_tx = [t for t in all_tx if t['received']]
pending_tx = [t for t in all_tx if not t['received'] and t['active']]

st.caption("Фильтры таблицы")

all_dates = sorted(set(
    (t['fact_date'] or t['plan_date'] or 'без даты')
    for t in all_tx
    if (t['fact_date'] or t['plan_date'])
), key=lambda x: (99 if x == 'без даты' else int(x) if x.isdigit() else 99))

all_projects = sorted(set(
    (t['project_name'] or t['project_acct'] or '—')
    for t in all_tx
    if (t['project_name'] or t['project_acct'])
))

all_suppliers = sorted(set(
    (t['supplier'] or '—')
    for t in all_tx
    if t['supplier']
))

all_directions = ['КОМПЛЕКТАЦИЯ', 'СТРОЙКА']

f1, f2, f3, f4 = st.columns(4)
with f1:
    filter_date = st.multiselect("Дата", all_dates, default=[], key="f_date")
with f2:
    filter_project = st.multiselect("Проект", all_projects, default=[], key="f_proj")
with f3:
    filter_supplier = st.multiselect("Поставщик", all_suppliers, default=[], key="f_sup")
with f4:
    filter_direction = st.multiselect("Направление", all_directions, default=[], key="f_dir")

def apply_filters(transactions):
    result = transactions
    if filter_date:
        result = [t for t in result if (t['fact_date'] or t['plan_date'] or 'без даты') in filter_date]
    if filter_project:
        result = [t for t in result if (t['project_name'] or t['project_acct'] or '—') in filter_project]
    if filter_supplier:
        result = [t for t in result if (t['supplier'] or '—') in filter_supplier]
    if filter_direction:
        result = [t for t in result if t['direction'] in filter_direction]
    return result

received_tx = apply_filters(received_tx)
pending_tx = apply_filters(pending_tx)

tab_r, tab_p = st.tabs([f"Получено ({len(received_tx)})", f"Ожидается ({len(pending_tx)})"])

def render_tx_table(transactions, show_received):
    if not transactions:
        st.caption("Нет данных.")
        return

    html = '<table class="plan-detail-table"><thead><tr>'
    html += '<th>Дата</th><th>Проект</th><th>Направление</th><th>Поставщик / За что</th><th>Группа</th><th>Сумма</th>'
    html += '</tr></thead><tbody>'

    if show_received:
        transactions = sorted(transactions, key=lambda t: t['fact_date'] or '99', reverse=True)
    else:
        def sort_key(t):
            d = t['plan_date']
            if not d or d == 'без даты':
                return 99
            try:
                return int(d)
            except ValueError:
                return 99
        transactions = sorted(transactions, key=sort_key)

    for t in transactions:
        date_str = t['fact_date'] if show_received else t['plan_date']
        if not date_str:
            date_str = "—"
        project = t['project_name'] or t['project_acct'] or t['supplier'] or "—"
        direction = t['direction']
        direction_tag = '<span class="tag-komplekt">К</span>' if direction == 'КОМПЛЕКТАЦИЯ' else '<span class="tag-stroyka">С</span>'

        html += '<tr>'
        html += f'<td>{date_str}</td>'
        html += f'<td>{project}</td>'
        html += f'<td>{direction_tag} {direction}</td>'
        html += f'<td>{t["supplier"] or t["description"] or "—"}</td>'
        html += f'<td>{t["group"] or "—"}</td>'
        html += f'<td>{fmt_rub(t["amount"])}</td>'
        html += '</tr>'

    total = sum(t['amount'] for t in transactions)
    html += f'<tr style="font-weight:700;border-top:2px solid {GRAPHITE};">'
    html += f'<td colspan="5">ИТОГО</td>'
    html += f'<td>{fmt_rub(total)}</td>'
    html += '</tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

with tab_r:
    render_tx_table(received_tx, show_received=True)

with tab_p:
    render_tx_table(pending_tx, show_received=False)

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Данные из Google Sheets · обновляются автоматически")
