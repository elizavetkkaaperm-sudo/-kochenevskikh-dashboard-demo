"""
Страница «Деньги» · Коченевских бюро
Балансы реальных кошельков на последнюю дату из ДДС по ЗП.
"""
import streamlit as st
import pandas as pd
import urllib.request
import re
from datetime import datetime

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице.")
    st.stop()

# Брендовые цвета
ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"
GREEN_BG = "#f6fbf0"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

st.set_page_config(page_title="Деньги · Коченевских", page_icon="◈", layout="wide")

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
    .section-divider {{
        height: 4px;
        background: linear-gradient(90deg, {ORANGE}, {MINT}, {SKY});
        border-radius: 2px; margin: 8px 0 24px 0;
    }}
    .balance-card {{
        background: {WHITE};
        border: 1px solid {GREY};
        border-radius: 16px;
        padding: 28px 24px;
        text-align: center;
    }}
    .balance-card .account-name {{
        font-size: 0.85rem; color: #888; margin-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.03em;
    }}
    .balance-card .account-value {{
        font-size: 2rem; font-weight: 700; color: {GRAPHITE};
    }}
    .balance-total {{
        background: {GREEN_BG};
        border: 1px solid #d4e8c0;
        border-radius: 16px;
        padding: 28px 24px;
        text-align: center;
    }}
    .balance-total .account-name {{ color: #888; font-size: 0.85rem; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.03em; }}
    .balance-total .account-value {{ color: {GRAPHITE}; font-size: 2.4rem; font-weight: 700; }}
    .balance-total .account-sub {{ color: #888; font-size: 0.8rem; }}
</style>
""", unsafe_allow_html=True)

# Источники
SPREADSHEET_ID = "1wYz8yG9QXFyDfdonNOikdsT9dEWOJ2Weqaf9L2aq6rw"
DDS_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"


def clean_number(s):
    if not isinstance(s, str):
        return 0
    s = s.replace("\u00A0", "").replace(" ", "").replace(",", ".").strip()
    try:
        return int(float(s))
    except (ValueError, OverflowError):
        return 0


def fmt_money(v):
    return f"{v:,.0f} ₽".replace(",", " ")


def canonical_wallet_name(name):
    """Приводит варианты написания кошелька из таблицы к одному имени."""
    text = str(name).strip().lower().replace("ё", "е")
    text = re.sub(r'["“”„«»]', "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if "райф" in text:
        return 'Рас/счет "Райф"'
    # Не путать рабочий счёт Точка с «Копилка налоги Точка».
    if "точка" in text and ("рас/счет" in text or "расчет" in text):
        return 'Рас/счет 2 "Точка"'
    if text == "рас/счет":
        return "Рас/счет"
    if text == "карта":
        return "Карта"
    if text == "резервный фонд":
        return "Резервный фонд"
    if text == "копилка":
        return "Копилка"
    if text == "цифра банк р/с":
        return "Цифра банк р/с"
    return str(name).strip().strip('"')


# Канонические названия. Разные варианты из таблицы приводятся к одному ключу,
# поэтому один и тот же счёт не появляется на странице дважды.
WALLET_WHITELIST = [
    "Рас/счет",
    "Карта",
    "Резервный фонд",
    'Рас/счет 2 "Точка"',
    "Копилка",
    "Цифра банк р/с",
    'Рас/счет "Райф"',
]

# Как показывать на сайте
WALLET_DISPLAY = {
    "Рас/счет": "Р/с счет тинь",
    "Карта": "Карта тинь блэк",
    "Резервный фонд": "Резервный фонд",
    "Копилка": "Налоговая копилка",
    'Рас/счет 2 "Точка"': "Р/с счет точка",
    "Цифра банк р/с": "Р/с счет цифра",
    'Рас/счет "Райф"': "Р/с счёт Райф",
}

# Группы кошельков
WALLET_GROUPS = {
    "💼 Рабочие счета": [
        "Рас/счет", "Карта", 'Рас/счет 2 "Точка"', "Цифра банк р/с",
        'Рас/счет "Райф"',
    ],
    "🏦 Фонды бизнеса": ["Копилка", "Резервный фонд"],
}


@st.cache_data(ttl=600)
def load_data():
    with urllib.request.urlopen(DDS_URL) as f:
        raw = pd.read_csv(f, header=None, dtype=str)

    # Парсим верхний блок как пары «название → сумма».
    # Ищем по каждой соседней паре, а не через фиксированный шаг 2.
    # В разных версиях таблицы служебные ячейки сдвигают начало пар.
    all_balances = {}
    for row_idx in range(min(3, len(raw))):
        cols = [str(raw.iloc[row_idx, j]).strip() for j in range(len(raw.columns))]
        for i in range(len(cols) - 1):
            raw_name = cols[i].replace("\\u00A0", " ").strip()
            val_str = cols[i + 1].replace("\\u00A0", " ").strip()
            if not raw_name or raw_name.lower() in ("nan", "итого"):
                continue
            if not val_str or val_str.lower() == "nan":
                continue

            name = canonical_wallet_name(raw_name)
            if name not in WALLET_WHITELIST:
                continue

            # Не выбрасываем нулевые счета. Они тоже должны быть видны.
            # Если название встретилось несколько раз, сохраняем первое
            # найденное значение, чтобы не создать вторую карточку.
            if name not in all_balances:
                all_balances[name] = clean_number(val_str)

    balances = all_balances

    # Последняя дата из колонки C
    header_idx = None
    for i in range(len(raw)):
        if isinstance(raw.iloc[i, 0], str) and raw.iloc[i, 0].strip() == "Месяц":
            header_idx = i
            break

    latest_date = None
    if header_idx is not None:
        for i in range(header_idx + 1, len(raw)):
            d = str(raw.iloc[i, 2]).strip()
            if d and d != "nan":
                try:
                    parsed = datetime.strptime(d, "%d.%m.%Y")
                    if latest_date is None or parsed > latest_date:
                        latest_date = parsed
                except ValueError:
                    continue

    return balances, latest_date


balances, latest_date = load_data()
total = sum(balances.values())

# Заголовок
st.markdown(
    f'<h2 style="font-weight:300;color:#252525;">'
    f'<img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:8px;">'
    f'Деньги</h2>',
    unsafe_allow_html=True
)
date_str = latest_date.strftime("%d.%m.%Y") if latest_date else "—"
st.markdown(f'<p style="color:#999;font-size:0.8rem;">на {date_str}</p>', unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# Итого
st.markdown(f"""
<div class="balance-card">
    <div class="account-name">Всего средств</div>
    <div class="account-value" style="font-size:2.4rem">{fmt_money(total)}</div>
    <div style="color:#888;font-size:0.8rem">{len(balances)} кошельков</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Группы кошельков
for group_name, group_wallets in WALLET_GROUPS.items():
    group_items = {k: v for k, v in balances.items() if k in group_wallets}
    if not group_items:
        continue
    group_total = sum(group_items.values())

    st.markdown(f"### {group_name}")
    st.markdown(f"""
    <div class="balance-card balance-total" style="margin-bottom:16px">
        <div class="account-name">{group_name}</div>
        <div class="account-value">{fmt_money(group_total)}</div>
        <div class="account-sub">{len(group_items)} кошелька</div>
    </div>
    """, unsafe_allow_html=True)

    items = list(group_items.keys())
    rows = [items[i:i+3] for i in range(0, len(items), 3)]
    for row_items in rows:
        cols = st.columns(3)
        for idx, name in enumerate(row_items):
            with cols[idx]:
                bal = group_items[name]
                display_name = WALLET_DISPLAY.get(name, name)
                st.markdown(f"""
                <div class="balance-card">
                    <div class="account-name">{display_name}</div>
                    <div class="account-value">{fmt_money(bal)}</div>
                </div>
                """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# Таблица
st.markdown("### ▸ Детализация")

table_data = []
for name, bal in sorted(balances.items(), key=lambda x: x[1], reverse=True):
    table_data.append({"Кошелёк": WALLET_DISPLAY.get(name, name), "Остаток": fmt_money(bal)})

st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Данные из Google Sheets · обновляются автоматически")
