import streamlit as st
import urllib.request
import csv
import io
import calendar
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="Расходы — Коченевских", page_icon="📅", layout="wide")

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


# ─── форматер чисел ───
def fmt(n):
    if n is None:
        return "0"
    return f"{n:,.0f}".replace(",", " ")

# ─── бренд ───
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GRAY = "#E6E6E6"

SHEET_ID = "14FFru1xtbOtcLDkjLC-t-Nawy9jPnHrcm-1KZ6coZiU"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.markdown(f"""
<style>
    .stApp {{ background: #ffffff; }}
    h1, h2, h3 {{ color: {GRAPHITE}; font-family: 'Inter', sans-serif; }}
    .page-title {{ font-size: 22px; font-weight: 700; color: {GRAPHITE}; font-family: 'Inter', sans-serif; margin-bottom: 24px; }}
    .logo-block {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }}
    .logo-block img {{ height: 24px; }}
    .logo-block span {{ font-size: 15px; color: #888; font-family: 'Inter', sans-serif; }}
    .metric-card {{
        background: #fff;
        border-radius: 14px;
        padding: 18px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid {GRAY};
        text-align: center;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .metric-label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
    .metric-value {{ font-size: 24px; font-weight: 700; color: {GRAPHITE}; }}
    .metric-value.red {{ color: {ORANGE}; }}
    .cal-table {{ width: 100%; border-collapse: separate; border-spacing: 4px; }}
    .cal-table th {{ text-align: center; font-size: 12px; color: #999; padding: 6px 0; font-weight: 400; }}
    .cal-table td {{ 
        background: #fff; border: 1px solid {GRAY}; border-radius: 10px; 
        padding: 10px 8px; text-align: center; vertical-align: top; width: 14.2%;
    }}
    .cal-table td.today {{ border: 2px solid {ORANGE}; background: #fff9f7; }}
    .cal-table td.empty {{ background: #fafafa; border: 1px dashed #e8e8e8; }}
    .cal-num {{ font-size: 17px; font-weight: 700; color: {GRAPHITE}; }}
    .cal-num.today {{ color: {ORANGE}; }}
    .cal-exp {{ font-size: 16px; font-weight: 800; color: {ORANGE}; margin-top: 3px; }}
    .cal-bal {{ font-size: 12px; color: #aaa; }}
    .cal-names {{ font-size: 12px; color: {GRAPHITE}; margin-top: 3px; line-height: 1.3; }}
    .summary-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    .summary-table td {{ padding: 10px 14px; border-bottom: 1px solid {GRAY}; font-size: 15px; }}
    .summary-table .group-header {{ font-weight: 700; font-size: 13px; color: #999; text-transform: uppercase; padding-top: 16px; }}
    .summary-table .amount {{ text-align: right; font-weight: 600; }}
    .summary-table .total-row td {{ font-weight: 700; border-top: 2px solid {GRAPHITE}; }}
    .group-badge {{
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 12px; font-weight: 600; margin-right: 6px;
    }}
    .group-FOT {{ background: #FFE8E0; color: #C0392B; }}
    .group-VC {{ background: #FFEDCC; color: #E67E22; }}
    .group-ZATR {{ background: {SKY}; color: #2C3E50; }}
    .group-DOP {{ background: {MINT}; color: #2C3E50; }}
    .detail-row {{ padding: 10px 0; border-bottom: 1px solid {GRAY}; }}
    .detail-total {{ font-size: 20px; font-weight: 700; color: {ORANGE}; }}
    .section-title {{ font-size: 18px; font-weight: 700; color: {GRAPHITE}; margin: 28px 0 14px 0; }}
</style>
""", unsafe_allow_html=True)


# ─── загрузка данных ───
@st.cache_data(ttl=300)
def load_all():
    try:
        raw = urllib.request.urlopen(CSV_URL, timeout=30).read().decode("utf-8", errors="replace")
    except Exception:
        return None

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)
    return rows


def parse_expenses(rows):
    today = date.today()

    # месяц/год из D1, E1 (row 0, cols 3, 4)
    try:
        sheet_month = int(rows[0][3].strip()) if len(rows[0]) > 3 else today.month
    except (ValueError, IndexError):
        sheet_month = today.month
    try:
        sheet_year = int(rows[0][4].strip()) if len(rows[0]) > 4 else today.year
    except (ValueError, IndexError):
        sheet_year = today.year

    month = sheet_month
    year = sheet_year

    cal = {}
    details = {}
    groups_data = []
    articles_data = []
    main_table = []

    for i, row in enumerate(rows):
        # ─── календарь Q, R, T (16, 17, 19) ───
        if len(row) > 19:
            day_cal = row[16].strip()
            try:
                day_num = int(day_cal)
            except ValueError:
                pass
            else:
                exp_str = row[17].strip().replace("\u00a0", " ").replace(",", ".").replace(" ", "")
                bal_str = row[19].strip().replace("\u00a0", " ").replace(",", ".").replace(" ", "")
                try:
                    expense = float(exp_str) if exp_str else 0
                except ValueError:
                    expense = 0
                try:
                    balance = float(bal_str) if bal_str else 0
                except ValueError:
                    balance = 0
                cal[day_num] = {"expense": expense, "balance": balance}

        # ─── детализация A–H (0–7) ───
        if len(row) >= 5:
            day_str = row[0].strip()
            try:
                day_num = int(day_str)
            except ValueError:
                pass
            else:
                group = row[1].strip() if len(row) > 1 else ""
                desc = row[2].strip() if len(row) > 2 else ""
                amount = 0
                for j in range(4, min(len(row), 8)):
                    val = row[j].strip().replace("\u00a0", " ").replace(",", ".").replace(" ", "")
                    try:
                        amount += float(val)
                    except ValueError:
                        pass
                if group:
                    if day_num not in details:
                        details[day_num] = []
                    details[day_num].append({"group": group, "desc": desc, "amount": amount})

        # ─── группы Q:R (16–17), строки 36–41 ───
        if 35 <= i <= 40:
            q = row[16].strip() if len(row) > 16 else ""
            r = row[17].strip().replace("\u00a0", " ").replace(",", ".").replace(" ", "") if len(row) > 17 else ""
            try:
                amt = float(r) if r else None
            except ValueError:
                amt = None
            groups_data.append({"name": q, "amount": amt})

        # ─── статьи Q:R (16–17), строки 45–49 ───
        if 44 <= i <= 48:
            q = row[16].strip() if len(row) > 16 else ""
            r = row[17].strip().replace("\u00a0", " ").replace(",", ".").replace(" ", "") if len(row) > 17 else ""
            try:
                amt = float(r) if r else None
            except ValueError:
                amt = None
            articles_data.append({"name": q, "amount": amt})

        # ─── основная таблица B–N (1–13), строки 1+ ───
        if i >= 1 and len(row) > 13:
            b = row[1].strip() if len(row) > 1 else ""
            if b and b not in ("число мес", ""):
                main_table.append({
                    "day": b,
                    "group": row[2].strip() if len(row) > 2 else "",
                    "who": row[3].strip() if len(row) > 3 else "",
                    "dept": row[4].strip() if len(row) > 4 else "",
                    "role": row[5].strip() if len(row) > 5 else "",
                    "deadline": row[6].strip() if len(row) > 6 else "",
                    "article": row[7].strip() if len(row) > 7 else "",
                    "fixed": row[8].strip().replace("\u00a0", " ") if len(row) > 8 else "",
                    "variable": row[9].strip().replace("\u00a0", " ") if len(row) > 9 else "",
                    "debt": row[10].strip().replace("\u00a0", " ") if len(row) > 10 else "",
                    "refund": row[11].strip().replace("\u00a0", " ") if len(row) > 11 else "",
                    "comment": row[12].strip() if len(row) > 12 else "",
                    "total": row[13].strip().replace("\u00a0", " ") if len(row) > 13 else "",
                })

    return cal, details, groups_data, articles_data, main_table, month, year, today


rows = load_all()
if rows is None:
    st.error("Не удалось загрузить данные. Проверь подключение к Google Sheets.")
    st.stop()

cal, details, groups_data, articles_data, main_table, month, year, today = parse_expenses(rows)

# ─── русские названия месяцев ───
month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
               "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
month_short = ["янв", "фев", "мар", "апр", "май", "июн",
               "июл", "авг", "сен", "окт", "ноя", "дек"]

# ─── заголовок ───
st.markdown(f"""
<div class="logo-block">
    <img src="https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png">
</div>
<div class="page-title">Расходы бюро (планируемые)</div>
""", unsafe_allow_html=True)

# ─── метрики ───
today_num = today.day
today_exp = cal.get(today_num, {}).get("expense", 0)
today_remaining = cal.get(today_num, {}).get("balance", 0)
month_total = sum(d["expense"] for d in cal.values())

# ─── расходы сегодня по срокам ───
today_exact = 0
today_moveable = 0
for row in main_table:
    try:
        if int(row["day"]) == today_num:
            total_str = row["total"].replace("\u00a0", " ").replace(",", ".").replace(" ", "")
            amt = float(total_str) if total_str else 0
            deadline = row["deadline"].strip().lower()
            if "точно" in deadline:
                today_exact += amt
            elif "можно" in deadline or "перенести" in deadline:
                today_moveable += amt
    except (ValueError, KeyError):
        pass

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">СЕГОДНЯ</div><div class="metric-value">{today_num} {month_short[month - 1]}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">РАСХОДЫ СЕГОДНЯ</div><div class="metric-value red">{fmt(today_exp)} ₽</div><div style="font-size:12px;color:#888;margin-top:4px;">точно в дату: {fmt(today_exact)} ₽ &nbsp;·&nbsp; можно перенести: {fmt(today_moveable)} ₽</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">ОСТАЛОСЬ ДО КОНЦА МЕСЯЦА</div><div class="metric-value">{fmt(today_remaining)} ₽</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">ВСЕГО ЗА МЕСЯЦ</div><div class="metric-value">{fmt(month_total)} ₽</div></div>""", unsafe_allow_html=True)

# ─── месяц ───
st.markdown(f"### {month_names[month - 1]} {year}")

# ─── переключатель календаря ───
cal_mode = st.radio(
    "Вид",
    ["Расходы, руб.", "Кому / За что"],
    horizontal=True,
    label_visibility="collapsed"
)

# ─── данные для режима ЗП по ФИО ───
salary_by_day = {}
for row in main_table:
    try:
        d_sal = int(row["day"])
    except (ValueError, KeyError):
        continue
    who = row["who"].strip()
    if who and who not in ("—", "-", ""):
        if d_sal not in salary_by_day:
            salary_by_day[d_sal] = []
        if who not in salary_by_day[d_sal]:
            salary_by_day[d_sal].append(who)

# ─── календарь ───
cal_obj = calendar.Calendar(firstweekday=0)
weeks = cal_obj.monthdayscalendar(year, month)
dow = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

html = '<table class="cal-table"><thead><tr>'
for d in dow:
    html += f'<th>{d}</th>'
html += '</tr></thead><tbody>'

for week in weeks:
    html += '<tr>'
    for d in week:
        if d == 0:
            html += '<td class="empty"></td>'
        else:
            td_class = 'today' if d == today_num else ''
            num_class = 'today' if d == today_num else ''

            if cal_mode == "Расходы, руб.":
                exp = cal.get(d, {}).get("expense", 0)
                bal = cal.get(d, {}).get("balance", 0)
                exp_html = f'<div class="cal-exp">{fmt(exp)} ₽</div>' if exp else ''
                bal_html = f'<div class="cal-bal">ост. {fmt(bal)}</div>' if bal else ''
                cell_content = f'<div class="cal-num {num_class}">{d}</div>{exp_html}{bal_html}'
            else:
                names = salary_by_day.get(d, [])
                if names:
                    names_html = "<br>".join(names)
                    cell_content = f'<div class="cal-num {num_class}">{d}</div><div class="cal-names">{names_html}</div>'
                else:
                    cell_content = f'<div class="cal-num {num_class}">{d}</div>'

            html += f'<td class="{td_class}">{cell_content}</td>'
    html += '</tr>'

html += '</tbody></table>'
st.markdown(html, unsafe_allow_html=True)

# ─── итоги по неделям ───
weekly_totals = []
for wk_idx, week in enumerate(weeks, 1):
    wk_sum = sum(cal.get(d, {}).get("expense", 0) for d in week if d != 0)
    if wk_sum > 0:
        weekly_totals.append((wk_idx, wk_sum))

if weekly_totals:
    st.markdown("---")
    st.markdown('<div class="section-title">Расходы по неделям</div>', unsafe_allow_html=True)
    wk_html = '<table class="summary-table"><tbody>'
    wk_all = 0
    for wk_idx, wk_sum in weekly_totals:
        wk_all += wk_sum
        wk_html += f'<tr><td>Неделя {wk_idx}</td><td class="amount">{fmt(wk_sum)} ₽</td></tr>'
    wk_html += f'<tr class="total-row"><td>Итого</td><td class="amount">{fmt(wk_all)} ₽</td></tr>'
    wk_html += '</tbody></table>'
    st.markdown(wk_html, unsafe_allow_html=True)

# ─── сводка по группам и статьям ───
st.markdown('<div class="section-title">Группы расходов</div>', unsafe_allow_html=True)

grp_html = '<table class="summary-table"><tbody>'
grp_total = 0
for item in groups_data:
    name = item["name"]
    amt = item["amount"]
    if amt is not None:
        grp_total += amt
        grp_html += f'<tr><td>{name}</td><td class="amount">{fmt(amt)} ₽</td></tr>'
    else:
        grp_html += f'<tr class="group-header"><td colspan="2">{name}</td></tr>'
grp_html += f'<tr class="total-row"><td>Итого</td><td class="amount">{fmt(grp_total)} ₽</td></tr>'
grp_html += '</tbody></table>'
st.markdown(grp_html, unsafe_allow_html=True)

st.markdown('<div class="section-title">Статьи расходов</div>', unsafe_allow_html=True)

art_html = '<table class="summary-table"><tbody>'
art_total = 0
for item in articles_data:
    name = item["name"]
    amt = item["amount"]
    if amt is not None:
        art_total += amt
        art_html += f'<tr><td>{name}</td><td class="amount">{fmt(amt)} ₽</td></tr>'
    else:
        art_html += f'<tr class="group-header"><td colspan="2">{name}</td></tr>'
art_html += f'<tr class="total-row"><td>Итого</td><td class="amount">{fmt(art_total)} ₽</td></tr>'
art_html += '</tbody></table>'
st.markdown(art_html, unsafe_allow_html=True)

# ─── основная таблица ───
st.markdown("---")
st.markdown('<div class="section-title">Все расходы</div>', unsafe_allow_html=True)

if main_table:
    df = pd.DataFrame(main_table)
    df.columns = ["День", "Группа", "Кому / За что", "Отдел", "Должность",
                   "Срок", "Статья", "Фиксы", "Переменная", "Долг",
                   "Возмещения", "Коммент", "Итого"]

    # фильтры
    fc1, fc2, fc3, fc4 = st.columns(4)

    # safe sorted unique — всё к строкам
    groups_list = sorted(set(str(x) for x in df["Группа"].dropna().unique()))
    depts_list = sorted(set(str(x) for x in df["Отдел"].dropna().unique()))
    articles_list = sorted(set(str(x) for x in df["Статья"].dropna().unique()))
    days_list = sorted(set(str(x) for x in df["День"].dropna().unique()),
                       key=lambda x: int(x) if x.isdigit() else 99)

    with fc1:
        filter_group = st.multiselect("Группа", groups_list)
    with fc2:
        filter_dept = st.multiselect("Отдел", depts_list)
    with fc3:
        filter_article = st.multiselect("Статья", articles_list)
    with fc4:
        filter_day = st.multiselect("День", days_list)

    filtered = df.copy()
    # при фильтрации тоже сравниваем как строки
    if filter_group:
        filtered = filtered[filtered["Группа"].astype(str).isin(filter_group)]
    if filter_dept:
        filtered = filtered[filtered["Отдел"].astype(str).isin(filter_dept)]
    if filter_article:
        filtered = filtered[filtered["Статья"].astype(str).isin(filter_article)]
    if filter_day:
        filtered = filtered[filtered["День"].astype(str).isin(filter_day)]

    # ─── парсим итого в число ───
    def parse_total(s):
        if not s:
            return 0
        s = str(s).replace("\xa0", " ").replace(",", ".").replace(" ", "")
        try:
            return float(s)
        except ValueError:
            return 0

    filtered["Итого_num"] = filtered["Итого"].apply(parse_total)
    filtered["Сократить"] = False

    # ─── data_editor с чекбоксами ───
    display_cols = ["День", "Группа", "Кому / За что", "Отдел", "Должность",
                    "Срок", "Статья", "Фиксы", "Переменная", "Долг",
                    "Возмещения", "Коммент", "Итого", "Сократить"]

    edited = st.data_editor(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "День": st.column_config.TextColumn("День", width="small"),
            "Группа": st.column_config.TextColumn("Группа", width="small"),
            "Отдел": st.column_config.TextColumn("Отдел", width="small"),
            "Статья": st.column_config.TextColumn("Статья", width="medium"),
            "Итого": st.column_config.TextColumn("Итого", width="small"),
            "Сократить": st.column_config.CheckboxColumn("Сократить", width="small"),
        },
        disabled=[c for c in display_cols if c != "Сократить"],
    )

    # ─── итоговая строка ───
    # маска сокращения из edited, суммы из filtered (где есть Итого_num)
    cut_mask = edited["Сократить"] == True
    total_all = filtered["Итого_num"].sum()
    cut_amount = filtered.loc[cut_mask[cut_mask].index, "Итого_num"].sum()
    final_amount = total_all - cut_amount

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Всего расходов", f"{fmt(total_all)} ₽")
    with c2:
        st.metric("К сокращению", f"{fmt(cut_amount)} ₽", delta=f"-{fmt(cut_amount)} ₽" if cut_amount > 0 else None)
    with c3:
        st.metric("После сокращения", f"{fmt(final_amount)} ₽")

    # ─── процент и перспектива до конца года ───
    if cut_amount > 0 and total_all > 0:
        cut_pct = cut_amount / total_all * 100
        remaining = 12 - month
        yearly_saving = cut_amount * remaining if remaining > 0 else 0
        if remaining > 0:
            st.markdown(f"""
            <div style="background:{SKY}; border-radius:10px; padding:0.8rem 1.5rem; margin-top:0.5rem;
                        display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.9rem; color:{GRAPHITE}; font-weight:500;">
                    Сокращение: <strong>{cut_pct:.1f}%</strong> от расходов месяца
                </span>
                <span style="font-size:0.9rem; color:{GRAPHITE}; font-weight:500;">
                    В перспективе до конца года: <strong>{fmt(yearly_saving)} ₽</strong>
                    &nbsp;<span style="font-size:0.75rem; color:#666;">({remaining} мес. × {fmt(cut_amount)} ₽)</span>
                </span>
            </div>
            """, unsafe_allow_html=True)

    st.caption(f"Показано {len(filtered)} из {len(df)} строк")
else:
    st.markdown("*Нет данных*")

# ─── футер ───
st.markdown(f"""<div style="text-align: center; color: #aaa; font-size: 12px; margin-top: 32px;">Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>""", unsafe_allow_html=True)
