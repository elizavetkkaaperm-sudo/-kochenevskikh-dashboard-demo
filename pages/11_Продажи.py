"""
Страница «Продажи» · Коченевских бюро

Читает данные amoCRM через долгосрочный токен. Прогноз сделок не смешивается
с фактическими деньгами из ДДС.

Необходимые Streamlit Secrets:
AMOCRM_DOMAIN = "kochenevskikh.amocrm.ru"
AMOCRM_LONG_TOKEN = "..."
"""
import html
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st


# ── Настройка страницы ───────────────────────────────────────────
st.set_page_config(
    page_title="Продажи · Коченевских",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="auto",
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



# ── Авторизация ──────────────────────────────────────────────────
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
SUCCESS = "#2E7D32"
WARNING = "#E65100"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"


# ── CSS ─────────────────────────────────────────────────────────
st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * {{ font-family: 'Inter', -apple-system, sans-serif !important; }}
    .stApp {{ background: {WHITE}; }}
    #MainMenu {{ visibility: hidden; }}
    header {{ visibility: visible !important; background: transparent !important; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 1.5rem !important; }}

    .hero-title {{
        font-size: 2.35rem; font-weight: 300; color: {GRAPHITE};
        letter-spacing: -0.03em; margin-bottom: 0.25rem;
    }}
    .hero-subtitle {{
        font-size: 0.9rem; color: #999; letter-spacing: 0.04em;
        text-transform: uppercase; margin-bottom: 1.4rem;
    }}
    .section-line {{ height: 1px; background: {GREY}; margin: 1.65rem 0; }}
    .section-title {{
        font-size: 1.05rem; font-weight: 700; color: {GRAPHITE};
        margin-bottom: 0.85rem;
    }}
    .section-note {{ font-size: 0.78rem; color: #999; margin: -0.45rem 0 0.9rem 0; }}

    .metric-card {{
        background: {WHITE}; border: 1px solid {GREY}; border-radius: 12px;
        padding: 1.2rem 1.35rem; min-height: 106px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.035);
    }}
    .metric-card.accent {{ background: linear-gradient(135deg, #FFF8F6 0%, #FFFFFF 100%); border-color: #F7B8AE; }}
    .metric-value {{ font-size: 1.85rem; font-weight: 650; color: {GRAPHITE}; line-height: 1.12; letter-spacing: -0.025em; }}
    .metric-value.orange {{ color: {ORANGE}; }}
    .metric-value.green {{ color: {SUCCESS}; }}
    .metric-label {{ font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.45rem; }}
    .metric-sub {{ font-size: 0.74rem; color: #aaa; margin-top: 0.25rem; }}

    .summary-card {{
        border: 1px solid {GREY}; border-radius: 14px; padding: 1.35rem 1.45rem;
        background: {WHITE}; box-shadow: 0 2px 8px rgba(0,0,0,0.035);
    }}
    .summary-title {{ font-size: 0.74rem; color: #999; text-transform: uppercase; letter-spacing: 0.04em; }}
    .summary-value {{ font-size: 2rem; font-weight: 650; color: {GRAPHITE}; margin-top: 0.3rem; }}
    .summary-text {{ font-size: 0.82rem; color: #777; line-height: 1.45; margin-top: 0.35rem; }}
    .summary-text strong {{ color: {GRAPHITE}; }}
    .small-note {{ font-size: 0.76rem; color: #999; line-height: 1.45; }}

    .risk-card {{
        background: #FFF8F6; border: 1px solid #FFD6D0; border-radius: 12px;
        padding: 1rem 1.2rem; color: {GRAPHITE};
    }}
    .risk-title {{ color: {ORANGE}; font-weight: 650; margin-bottom: 0.35rem; }}
    .vk-card {{
        background: linear-gradient(135deg, #F6FAFF 0%, #FFFFFF 100%);
        border: 1px solid {SKY}; border-radius: 14px; padding: 1.35rem 1.45rem;
    }}
    .vk-title {{ font-size: 0.78rem; color: #5B78A2; text-transform: uppercase; letter-spacing: 0.04em; }}
    .vk-value {{ font-size: 1.8rem; font-weight: 650; color: {GRAPHITE}; margin-top: 0.25rem; }}
    .vk-sub {{ font-size: 0.76rem; color: #8B9BB2; margin-top: 0.25rem; }}

    @media (max-width: 640px) {{
        .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
        .hero-title {{ font-size: 1.55rem; }}
        .metric-value {{ font-size: 1.55rem; }}
        .summary-value {{ font-size: 1.55rem; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)


# ── Форматирование ──────────────────────────────────────────────
def fmt_int(value):
    try:
        return f"{int(round(float(value))):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def fmt_rub(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.1f} млн ₽".replace(".", ",")
    return f"{int(round(number)):,} ₽".replace(",", " ")


def parse_timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value)).date()
    except (TypeError, ValueError, OSError):
        return None


def clean_text(value):
    return " ".join(str(value or "").replace("\n", " ").split())


def secret_value(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or "").strip()


# ── Универсальный GET без вывода секретов ────────────────────────
def get_json(url, headers=None, timeout=25):
    request = urllib.request.Request(url, method="GET")
    request.add_header("User-Agent", "KochenevskikhDashboard/1.0")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError("Сервис отклонил доступ. Проверь подключение и права интеграции.") from None
        if exc.code == 429:
            raise RuntimeError("Сервис временно ограничил частоту запросов. Попробуй обновить страницу позже.") from None
        raise RuntimeError("Сервис вернул ошибку при загрузке данных.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("Сервис сейчас не отвечает. Попробуй обновить страницу позже.") from None


# ── amoCRM ───────────────────────────────────────────────────────
def amo_url(domain, path, params=None):
    base = f"https://{domain.strip().rstrip('/')}/api/v4{path}"
    if params:
        base += "?" + urllib.parse.urlencode(params, doseq=True)
    return base


def amo_get(domain, token, path, params=None):
    return get_json(
        amo_url(domain, path, params),
        headers={"Authorization": f"Bearer {token}"},
    )


@st.cache_data(ttl=300, show_spinner=False)
def load_amo_data(domain, token):
    if not domain or not token:
        raise RuntimeError("В Secrets не заполнены данные подключения amoCRM.")

    pipelines_response = amo_get(domain, token, "/leads/pipelines")
    pipelines = {}
    for pipeline in pipelines_response.get("_embedded", {}).get("pipelines", []):
        pipeline_id = int(pipeline.get("id", 0))
        statuses = {}
        for status in pipeline.get("_embedded", {}).get("statuses", []):
            status_id = int(status.get("id", 0))
            statuses[status_id] = {
                "name": clean_text(status.get("name")) or "Без названия",
                "type": int(status.get("type", 0) or 0),
                "sort": int(status.get("sort", 0) or 0),
            }
        pipelines[pipeline_id] = {
            "name": clean_text(pipeline.get("name")) or "Без названия",
            "sort": int(pipeline.get("sort", 0) or 0),
            "statuses": statuses,
        }

    leads = []
    for page in range(1, 21):
        response = amo_get(domain, token, "/leads", {"limit": 250, "page": page})
        page_items = response.get("_embedded", {}).get("leads", [])
        if not page_items:
            break
        leads.extend(page_items)
        if len(page_items) < 250:
            break

    return {"pipelines": pipelines, "leads": leads, "limited": len(leads) >= 5000}


def custom_fields(lead):
    result = {}
    for field in lead.get("custom_fields_values") or []:
        name = clean_text(field.get("field_name"))
        values = field.get("values") or []
        if not name or not values:
            continue
        value_parts = []
        for item in values:
            value = item.get("value")
            if value not in (None, ""):
                value_parts.append(clean_text(value))
        if value_parts:
            result[name] = ", ".join(value_parts)
    return result


def lead_view(lead, pipelines):
    pipeline_id = int(lead.get("pipeline_id", 0) or 0)
    status_id = int(lead.get("status_id", 0) or 0)
    pipeline = pipelines.get(pipeline_id, {})
    status = pipeline.get("statuses", {}).get(status_id, {})
    return {
        "id": int(lead.get("id", 0) or 0),
        "name": clean_text(lead.get("name")) or "Без названия",
        "price": float(lead.get("price", 0) or 0),
        "pipeline_id": pipeline_id,
        "pipeline_name": pipeline.get("name", "Воронка не определена"),
        "status_id": status_id,
        "status_name": status.get("name", "Этап не определён"),
        "status_type": status.get("type", 0),
        "created": parse_timestamp(lead.get("created_at")),
        "updated": parse_timestamp(lead.get("updated_at")),
        "closed": parse_timestamp(lead.get("closed_at")),
        "custom": custom_fields(lead),
    }


def build_amo_stats(data, today):
    pipelines = data.get("pipelines", {})
    views = [lead_view(lead, pipelines) for lead in data.get("leads", [])]
    active = [item for item in views if item["status_type"] not in (1, 2)]
    won = [item for item in views if item["status_type"] == 1 and item["closed"] and item["closed"].year == today.year and item["closed"].month == today.month]
    new_leads = [item for item in views if item["created"] and item["created"].year == today.year and item["created"].month == today.month]
    stale_border = today - timedelta(days=7)
    stale = [item for item in active if item["updated"] and item["updated"] < stale_border]

    funnel = defaultdict(lambda: {"count": 0, "amount": 0.0, "pipeline": "", "stage": ""})
    for item in active:
        key = (item["pipeline_id"], item["status_id"])
        funnel[key]["count"] += 1
        funnel[key]["amount"] += item["price"]
        funnel[key]["pipeline"] = item["pipeline_name"]
        funnel[key]["stage"] = item["status_name"]

    funnel_rows = []
    for key, item in funnel.items():
        pipeline = pipelines.get(key[0], {})
        status = pipeline.get("statuses", {}).get(key[1], {})
        funnel_rows.append({
            "Воронка": item["pipeline"],
            "Этап": item["stage"],
            "Сделок": item["count"],
            "Сумма": item["amount"],
            "_sort_pipeline": pipeline.get("sort", 0),
            "_sort_stage": status.get("sort", 0),
        })
    funnel_rows.sort(key=lambda row: (row["_sort_pipeline"], row["_sort_stage"], row["Этап"]))

    expected_field_names = []
    for item in views:
        for field_name in item["custom"]:
            name = field_name.lower()
            if any(word in name for word in ("оплат", "платеж", "платёж", "срок оплаты", "дата оплаты")):
                expected_field_names.append(field_name)
    expected_field_names = list(dict.fromkeys(expected_field_names))

    return {
        "views": views,
        "active": active,
        "won": won,
        "new_leads": new_leads,
        "stale": stale,
        "funnel_rows": funnel_rows,
        "expected_field_names": expected_field_names,
        "limited": bool(data.get("limited")),
    }


# ── Заголовок ────────────────────────────────────────────────────
today = date.today()
period_label = today.strftime("%B %Y")
months_ru = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
period_label = f"{months_ru[today.month - 1]} {today.year}"
st.markdown(
    f"""
<div class="hero-title">
    <img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:10px;">
    Продажи
</div>
<div class="hero-subtitle">Воронка, потенциал сделок и статистика сообщества · {period_label}</div>
""",
    unsafe_allow_html=True,
)


# ── Загрузка amoCRM ──────────────────────────────────────────────
amo_domain = secret_value("AMOCRM_DOMAIN")
amo_token = secret_value("AMOCRM_LONG_TOKEN")

try:
    with st.spinner("Загружаю данные amoCRM..."):
        amo_data = load_amo_data(amo_domain, amo_token)
    amo = build_amo_stats(amo_data, today)
except RuntimeError as exc:
    st.error(str(exc))
    amo = None

if amo is not None:
    active_amount = sum(item["price"] for item in amo["active"])
    won_amount = sum(item["price"] for item in amo["won"])

    st.markdown('<div class="section-title">▸ Продажи сейчас</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Данные из amoCRM. Сумма активных сделок показывает потенциал продаж, а не деньги на счёте.</div>',
        unsafe_allow_html=True,
    )
    m1, m2, m3, m4 = st.columns(4)
    cards = [
        (m1, fmt_int(len(amo["active"])), "активных сделок", fmt_rub(active_amount), "accent", "orange"),
        (m2, fmt_rub(active_amount), "потенциал воронки", "все незакрытые сделки", "", ""),
        (m3, fmt_int(len(amo["new_leads"])), "новых заявок", "в текущем месяце", "", ""),
        (m4, fmt_rub(won_amount), "успешно закрыто", f"{len(amo['won'])} сделок в этом месяце", "", "green"),
    ]
    for column, value, label, sub, card_class, value_class in cards:
        with column:
            st.markdown(
                f"""
<div class="metric-card {card_class}">
    <div class="metric-value {value_class}">{value}</div>
    <div class="metric-label">{label}</div>
    <div class="metric-sub">{sub}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">▸ Воронка активных сделок</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-note">Суммы по этапам amoCRM. Это прогноз продаж, не прогноз ДДС, пока в карточках не заполнена плановая дата оплаты.</div>',
        unsafe_allow_html=True,
    )
    if amo["funnel_rows"]:
        funnel_df = pd.DataFrame(amo["funnel_rows"])
        funnel_df["Сумма"] = funnel_df["Сумма"].map(fmt_rub)
        funnel_df = funnel_df[["Воронка", "Этап", "Сделок", "Сумма"]]
        st.dataframe(funnel_df, hide_index=True, use_container_width=True)
    else:
        st.info("Активных сделок пока нет.")

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown('<div class="section-title">▸ Что требует внимания</div>', unsafe_allow_html=True)
        if amo["stale"]:
            stale_rows = []
            for item in sorted(amo["stale"], key=lambda row: row["updated"] or date.min)[:20]:
                stale_rows.append({
                    "Сделка": item["name"],
                    "Этап": item["status_name"],
                    "Сумма": fmt_rub(item["price"]),
                    "Последнее движение": item["updated"].strftime("%d.%m.%Y") if item["updated"] else "нет даты",
                })
            st.dataframe(pd.DataFrame(stale_rows), hide_index=True, use_container_width=True)
        else:
            st.markdown(
                '<div class="summary-card"><div class="summary-title">Зависшие сделки</div><div class="summary-value">0</div><div class="summary-text">Нет активных сделок без движения больше 7 дней.</div></div>',
                unsafe_allow_html=True,
            )

    with right:
        st.markdown('<div class="section-title">▸ Контроль прогноза</div>', unsafe_allow_html=True)
        if amo["expected_field_names"]:
            names = ", ".join(amo["expected_field_names"][:4])
            st.markdown(
                f'<div class="summary-card"><div class="summary-title">Поле оплаты найдено</div><div class="summary-text"><strong>{html.escape(names)}</strong><br>Можно использовать его для календаря ожидаемых поступлений.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="risk-card"><div class="risk-title">Пока не вижу поля плановой оплаты</div><div class="small-note">Сейчас сайт показывает объём воронки, но не называет его ожидаемым ДДС. Для точного прогноза добавь в amoCRM поле «Плановая дата оплаты» и заполняй его в сделках.</div></div>',
                unsafe_allow_html=True,
            )
        if amo["limited"]:
            st.warning("В amoCRM загружены первые 5 000 сделок. Если их больше, нужен отдельный фильтр периода.")

    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">▸ Последние сделки</div>', unsafe_allow_html=True)
    recent_rows = []
    for item in sorted(amo["views"], key=lambda row: row["updated"] or date.min, reverse=True)[:30]:
        recent_rows.append({
            "Сделка": item["name"],
            "Воронка": item["pipeline_name"],
            "Этап": item["status_name"],
            "Сумма": fmt_rub(item["price"]),
            "Изменена": item["updated"].strftime("%d.%m.%Y") if item["updated"] else "-",
        })
    if recent_rows:
        st.dataframe(pd.DataFrame(recent_rows), hide_index=True, use_container_width=True)
    else:
        st.info("В amoCRM пока нет сделок для отображения.")

