"""
Страница «Дебиторская задолженность» · Коченевских бюро
Текущая дебиторка: итог + фильтры + таблица + промежуточный итог.
"""
import streamlit as st
import pandas as pd
import urllib.request
import csv
import io
from datetime import datetime, date, timedelta

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

st.set_page_config(page_title="Дебиторка · Коченевских", page_icon="◈", layout="wide")

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
    header {{ visibility: visible !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}

    h2 {{ color: {GRAPHITE}; font-weight: 300; }}

    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px;
        margin: 8px 0 24px 0;
    }}

    .total-card {{
        background: linear-gradient(135deg, #FFF8F6 0%, #FFFFFF 100%);
        border: 2px solid {ORANGE};
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
    }}
    .total-label {{
        font-size: 0.85rem;
        font-weight: 500;
        color: #999;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }}
    .total-value {{
        font-size: 3rem;
        font-weight: 700;
        color: {GRAPHITE};
        letter-spacing: -0.02em;
        line-height: 1.1;
    }}
    .total-date {{
        font-size: 0.8rem;
        color: #bbb;
        margin-top: 0.4rem;
    }}
    .overdue-line {{
        font-size: 0.9rem;
        color: {ORANGE};
        font-weight: 500;
        margin-top: 0.3rem;
    }}
    .new-projects-line {{
        font-size: 0.95rem;
        color: {GRAPHITE};
        font-weight: 600;
        margin-top: 0.65rem;
        padding-top: 0.65rem;
        border-top: 1px solid {GREY};
    }}
    .new-projects-value {{
        color: {ORANGE};
    }}

    /* sub-total after filtering */
    .subtotal-bar {{
        background: {SKY};
        border-radius: 10px;
        padding: 0.7rem 1.5rem;
        margin-top: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .subtotal-label {{
        font-size: 0.8rem;
        font-weight: 500;
        color: {GRAPHITE};
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}
    .subtotal-value {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {GRAPHITE};
    }}

    /* dataframe styling */
    div[data-testid="stDataFrame"] table {{
        border-collapse: separate !important;
        border-spacing: 0 !important;
        width: 100% !important;
    }}
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
        border-bottom: 1px solid {GREY} !important;
        color: {GRAPHITE} !important;
    }}

    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }}
</style>
""", unsafe_allow_html=True)

# ── Данные ──────────────────────────────────────────────────────
SHEET_ID = "14FFru1xtbOtcLDkjLC-t-Nawy9jPnHrcm-1KZ6coZiU"
GID = "1273919189"


def clean(s):
    return s.replace("\xa0", " ").strip()


def parse_amount(s):
    s = s.replace("\xa0", " ").strip()
    if not s or s in ("—", "-"):
        return None
    s = s.replace("₽", "").replace("р.", "").strip()
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def is_first_stage(stage):
    """Возвращает True только для первого этапа, а не для этапов 10, 11 и т.п."""
    normalized = clean(str(stage)).lower().replace("ё", "е")
    return normalized in ("1", "1 этап", "этап 1", "i", "i этап")


def fmt_amount(val):
    if val is None:
        return "—"
    return f"{int(val):,} ₽".replace(",", " ")


def parse_date(s):
    try:
        parts = s.split(".")
        return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, IndexError):
        return None


def add_business_days(start_date, days):
    current = start_date
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current


def is_overdue(date_str, today):
    d = parse_date(date_str)
    if d is None:
        return False
    due = add_business_days(d, 5)
    return due < today


MONTH_NAMES = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
               7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}


@st.cache_data(ttl=1800)
def load_receivables():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    total_str = ""
    if len(rows) > 0 and len(rows[0]) > 6:
        total_str = rows[0][6].strip()

    data = []
    for row in rows[2:]:
        if not row or len(row) < 19:
            continue
        doc_num = row[0].strip()
        if not doc_num:
            continue

        amount_str = clean(row[6]) if len(row) > 6 else ""
        amount_val = parse_amount(amount_str)

        project = clean(row[13]) if len(row) > 13 else ""
        if project == "-":
            project = ""

        contract = clean(row[15]) if len(row) > 15 else ""
        if contract == "-":
            contract = ""

        stage = clean(row[16]) if len(row) > 16 else ""
        if stage == "-":
            stage = ""

        comment = clean(row[18]) if len(row) > 18 else ""
        date_str = clean(row[1]) if len(row) > 1 else ""
        customer = clean(row[14]) if len(row) > 14 and clean(row[14]) else ""

        data.append({
            "date_str": date_str,
            "month": int(clean(row[2])) if len(row) > 2 and clean(row[2]) else 0,
            "month_name": MONTH_NAMES.get(int(clean(row[2])), "—") if len(row) > 2 and clean(row[2]) else "—",
            "year": int(clean(row[3])) if len(row) > 3 and clean(row[3]) else 0,
            "amount_val": amount_val,
            "amount_display": fmt_amount(amount_val),
            "project": project if project else "—",
            "customer": customer if customer else "—",
            "contract": contract if contract else "—",
            "stage": stage if stage else "—",
            "is_first_stage": is_first_stage(stage),
            "comment": comment,
        })

    return total_str, data


total_str, rows = load_receivables()
today = date.today()

# ── Overdue flag ────────────────────────────────────────────────
for r in rows:
    r["overdue"] = "!" if (r["amount_val"] and is_overdue(r["date_str"], today)) else ""

# ── Считаем общий overdue (до фильтрации) ─────────────────────
overdue_total_all = sum(r["amount_val"] for r in rows if r["overdue"] == "!" and r["amount_val"])
new_projects_total = sum(
    r["amount_val"] for r in rows
    if r["is_first_stage"] and r["amount_val"]
)

# ── Рендер ─────────────────────────────────────────────────────
st.markdown(
    f'<h2 style="font-weight:300;color:{GRAPHITE};margin-bottom:0;">'
    f'<img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">'
    f'Текущая дебиторская задолженность</h2>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ── Итог (общий) ───────────────────────────────────────────────
total_val = parse_amount(total_str)
total_display = fmt_amount(total_val)
today_str = today.strftime("%d.%m.%Y")

st.markdown(f"""
<div class="total-card">
    <div class="total-label">Дебиторская задолженность на {today_str}</div>
    <div class="total-value">{total_display}</div>
    <div class="total-date">{len(rows)} неоплаченных счетов</div>
    <div class="overdue-line">ДЗ более 5 рабочих дней: {fmt_amount(overdue_total_all)}</div>
    <div class="new-projects-line">ДЗ по новым проектам (продажи): <span class="new-projects-value">{fmt_amount(new_projects_total)}</span></div>
</div>
""", unsafe_allow_html=True)

# ── Фильтры ────────────────────────────────────────────────────
st.markdown("### Фильтры")

f1, f2, f3, f4, f5 = st.columns(5)

with f1:
    all_months = sorted(set(r["month_name"] for r in rows if r["month_name"] != "—"),
                        key=lambda m: list(MONTH_NAMES.values()).index(m) if m in MONTH_NAMES.values() else 99)
    sel_months = st.multiselect("Месяц", all_months, default=[])

with f2:
    all_projects = sorted(set(r["project"] for r in rows))
    sel_projects = st.multiselect("Проект", all_projects, default=[])

with f3:
    all_customers = sorted(set(r["customer"] for r in rows))
    sel_customers = st.multiselect("Заказчик", all_customers, default=[])

with f4:
    all_stages = sorted(
        set(r["stage"] for r in rows),
        key=lambda value: (0, int(value)) if value.isdigit() else (1, value.lower()),
    )
    sel_stages = st.multiselect("Этап", all_stages, default=[])

with f5:
    only_overdue = st.checkbox("Только просроченные", value=False)

# ── Применяем фильтры ──────────────────────────────────────────
filtered = rows.copy()

if sel_months:
    filtered = [r for r in filtered if r["month_name"] in sel_months]

if sel_projects:
    filtered = [r for r in filtered if r["project"] in sel_projects]

if sel_customers:
    filtered = [r for r in filtered if r["customer"] in sel_customers]

if sel_stages:
    filtered = [r for r in filtered if r["stage"] in sel_stages]

if only_overdue:
    filtered = [r for r in filtered if r["overdue"] == "!"]

# ── Таблица ────────────────────────────────────────────────────
if not filtered:
    st.info("Нет счетов, соответствующих фильтрам.")
else:
    df = pd.DataFrame(filtered)

    display_cols = [
        "date_str", "month", "year", "amount_display",
        "project", "customer", "contract", "stage", "comment", "overdue"
    ]
    df_display = df[display_cols].copy()

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date_str": st.column_config.TextColumn("Дата", width="small"),
            "month": st.column_config.NumberColumn("Месяц", width="small"),
            "year": st.column_config.NumberColumn("Год", width="small"),
            "amount_display": st.column_config.TextColumn("Сумма", width="small"),
            "project": st.column_config.TextColumn("Проект", width="medium"),
            "customer": st.column_config.TextColumn("Заказчик", width="medium"),
            "contract": st.column_config.TextColumn("№ договора", width="small"),
            "stage": st.column_config.TextColumn("Этап", width="small"),
            "comment": st.column_config.TextColumn("Комментарий", width="large"),
            "overdue": st.column_config.TextColumn("!", width="small"),
        },
    )

    # ── Промежуточный итог ─────────────────────────────────────
    sub_amount = sum(r["amount_val"] for r in filtered if r["amount_val"])
    sub_count = len(filtered)
    sub_overdue = sum(r["amount_val"] for r in filtered if r["overdue"] == "!" and r["amount_val"])

    st.markdown(f"""
    <div class="subtotal-bar">
        <div>
            <div class="subtotal-label">Отфильтровано: {sub_count} счетов</div>
            <div style="font-size:0.75rem;color:#666;margin-top:2px;">
                из них просрочено: {fmt_amount(sub_overdue)}
            </div>
        </div>
        <div class="subtotal-value">{fmt_amount(sub_amount)}</div>
    </div>
    """, unsafe_allow_html=True)
