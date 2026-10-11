"""
Страница «Статистика соцсетей» · Коченевских бюро

Читает статистику сообщества VK через API и показывает охват и активность
за последние 30 дней.

Необходимые Streamlit Secrets:
VK_SERVICE_KEY = "..."
VK_USER_TOKEN = "..."
VK_GROUP_ID = "..."
"""
import html
import json
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Статистика соцсетей · Коченевских",
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


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице.")
    st.stop()

ORANGE = "#F74028"
MINT = "#D6EFB9"
SKY = "#D0E2F7"
GRAPHITE = "#252525"
GREY = "#E6E6E6"
WHITE = "#FFFFFF"
SUCCESS = "#2E7D32"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"

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
    .hero-title {{ font-size: 2.35rem; font-weight: 300; color: {GRAPHITE}; letter-spacing: -0.03em; margin-bottom: 0.25rem; }}
    .hero-subtitle {{ font-size: 0.9rem; color: #999; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 1.4rem; }}
    .section-line {{ height: 1px; background: {GREY}; margin: 1.65rem 0; }}
    .section-title {{ font-size: 1.05rem; font-weight: 700; color: {GRAPHITE}; margin-bottom: 0.85rem; }}
    .section-note {{ font-size: 0.78rem; color: #999; margin: -0.45rem 0 0.9rem 0; }}
    .vk-card {{ background: linear-gradient(135deg, #F6FAFF 0%, #FFFFFF 100%); border: 1px solid {SKY}; border-radius: 14px; padding: 1.35rem 1.45rem; min-height: 108px; box-shadow: 0 2px 8px rgba(0,0,0,0.035); }}
    .vk-title {{ font-size: 0.78rem; color: #5B78A2; text-transform: uppercase; letter-spacing: 0.04em; }}
    .vk-value {{ font-size: 1.8rem; font-weight: 650; color: {GRAPHITE}; margin-top: 0.25rem; }}
    .vk-sub {{ font-size: 0.76rem; color: #8B9BB2; margin-top: 0.25rem; }}
    .info-card {{ border: 1px solid {GREY}; border-radius: 14px; padding: 1.1rem 1.35rem; background: #FFFFFF; color: #777; font-size: 0.82rem; line-height: 1.45; }}
    @media (max-width: 640px) {{
        .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
        .hero-title {{ font-size: 1.55rem; }}
        .vk-value {{ font-size: 1.55rem; }}
    }}
</style>
""",
    unsafe_allow_html=True,
)


def fmt_int(value):
    try:
        return f"{int(round(float(value))):,}".replace(",", " ")
    except (TypeError, ValueError):
        return "0"


def clean_text(value):
    return " ".join(str(value or "").replace("\n", " ").split())


def secret_value(name):
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or "").strip()


def get_json(url, timeout=25):
    request = urllib.request.Request(url, method="GET")
    request.add_header("User-Agent", "KochenevskikhDashboard/1.0")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError("VK отклонил доступ. Нужен пользовательский токен с доступом к сообществу.") from None
        if exc.code == 429:
            raise RuntimeError("VK временно ограничил частоту запросов. Попробуй обновить страницу позже.") from None
        raise RuntimeError("VK вернул ошибку при загрузке статистики.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("VK сейчас не отвечает. Попробуй обновить страницу позже.") from None


@st.cache_data(ttl=900, show_spinner=False)
def load_vk_stats(user_token, group_id, today):
    if not user_token or not group_id:
        raise RuntimeError("В Secrets не заполнены VK_USER_TOKEN или VK_GROUP_ID.")
    start = today - timedelta(days=29)
    timestamp_from = int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    timestamp_to = int(datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc).timestamp())
    params = {
        "group_id": group_id,
        "timestamp_from": timestamp_from,
        "timestamp_to": timestamp_to,
        "interval": "day",
        "stats_groups": "visitors,reach,activity",
        "extended": 1,
        "v": "5.199",
        "access_token": user_token,
    }
    url = "https://api.vk.com/method/stats.get?" + urllib.parse.urlencode(params)
    response = get_json(url, timeout=25)
    if response.get("error"):
        error = response["error"]
        message = clean_text(error.get("error_msg"))
        raise RuntimeError(message or "VK не вернул статистику сообщества.")
    records = response.get("response", [])
    if isinstance(records, dict):
        records = records.get("items", [])
    totals = defaultdict(float)
    for record in records or []:
        if not isinstance(record, dict):
            continue
        for key in ("visitors", "reach", "reach_subscribers", "subscribed", "unsubscribed", "likes", "comments", "copies"):
            value = record.get(key, 0)
            if isinstance(value, (int, float)):
                totals[key] += value
    return {"records": records or [], "totals": dict(totals), "start": start, "end": today}


today = date.today()
months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
period_label = f"{months_ru[today.month - 1]} {today.year}"
st.markdown(
    f"""
<div class="hero-title"><img src="{LOGO_URL}" style="height:22px;vertical-align:middle;margin-right:10px;">Статистика соцсетей</div>
<div class="hero-subtitle">VK · охват и активность сообщества · {period_label}</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">▸ Сообщество VK</div>', unsafe_allow_html=True)
st.markdown('<div class="section-note">Сводка за последние 30 дней из VK API. Это маркетинговые показатели, не продажи.</div>', unsafe_allow_html=True)

vk_key = secret_value("VK_USER_TOKEN") or secret_value("VK_ACCESS_TOKEN")
vk_group_id = secret_value("VK_GROUP_ID")
try:
    with st.spinner("Загружаю статистику VK..."):
        vk = load_vk_stats(vk_key, vk_group_id, today)
    totals = vk["totals"]
    vk_cols = st.columns(4)
    vk_cards = [
        (vk_cols[0], fmt_int(totals.get("visitors", 0)), "посетителей", "за 30 дней"),
        (vk_cols[1], fmt_int(totals.get("reach", 0)), "охват", "за 30 дней"),
        (vk_cols[2], fmt_int(totals.get("subscribed", 0)), "подписались", "за 30 дней"),
        (vk_cols[3], fmt_int(totals.get("unsubscribed", 0)), "отписались", "за 30 дней"),
    ]
    for column, value, label, sub in vk_cards:
        with column:
            st.markdown(
                f'<div class="vk-card"><div class="vk-value">{value}</div><div class="vk-title">{label}</div><div class="vk-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
    if vk.get("records"):
        chart_rows = []
        for record in vk["records"]:
            if not isinstance(record, dict):
                continue
            period = record.get("period") or record.get("period_from")
            if isinstance(period, (int, float)):
                period = datetime.fromtimestamp(period, tz=timezone.utc).strftime("%d.%m")
            if not period:
                continue
            chart_rows.append({"Дата": str(period), "Посетители": record.get("visitors", 0), "Охват": record.get("reach", 0)})
        if chart_rows:
            chart_df = pd.DataFrame(chart_rows).set_index("Дата")
            st.line_chart(chart_df, height=260)
    st.caption(f"Период VK: {vk['start'].strftime('%d.%m.%Y')} - {vk['end'].strftime('%d.%m.%Y')}")
except RuntimeError as exc:
    st.info(f"Статистика VK пока не загрузилась. Для метода stats.get нужен пользовательский токен с доступом к сообществу: {exc}")

st.markdown(
    f"""
<div style="text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid {GREY};">
    <span style="font-size:0.7rem; color:#ccc;">VK · обновляется автоматически</span>
</div>
""",
    unsafe_allow_html=True,
)
