"""Глазок видимости: прячет все цифры на сайте.

Подключается одной строкой на странице после входа по паролю:

    import privacy
    privacy.arm()

Кнопка стоит вверху страницы справа: «Показать цифры» и «Скрыть цифры».
Пока цифры скрыты, числа размыты, а подписи и структура читаются.
"""
import streamlit as st
import streamlit.components.v1 as components

KEY = "hide_numbers"
START_HIDDEN = True

CSS_BASE = """
<style>
.st-key-eyebtn button { border-radius: 22px; padding: 8px 15px; font-size: 14px; font-weight: 600; border: 2px solid #F74028; background: #FFFFFF; color: #252525; box-shadow: 0 2px 8px rgba(0, 0, 0, .10); }
.st-key-eyebtn button:hover { background: #FFF4F1; }
</style>
"""

CSS_BLUR = """
<style>
.nb, .nb * { filter: blur(7px) !important; }
[class*="metric"], [class*="kpi"], [class*="card-val"], [class*="card-value"], [class*="amount"], [class*="money"], [class*="value"], [class*="val"], [class*="total"], [class*="sum"], [class*="price"] { filter: blur(7px) !important; }
table, table * { filter: blur(7px) !important; }
[data-testid="stDataFrame"], [data-testid="stTable"], [data-testid="stPlotlyChart"], [data-testid="stArrowVegaLiteChart"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { filter: blur(7px) !important; }
.st-key-eyebtn, .st-key-eyebtn * { filter: none !important; }
</style>
"""

SCRIPT = """
<script>
(function () {
  var doc = window.parent.document;
  var win = doc.defaultView;
  var hide = __HIDE__;
  function hasDigit(t) { return /[0-9]/.test(t); }
  function skip(el) {
    var up = el;
    for (var i = 0; i < 7 && up; i++) {
      if (up.tagName === "SCRIPT" || up.tagName === "STYLE") { return true; }
      if (up.classList && up.classList.contains("st-key-eyebtn")) { return true; }
      up = up.parentElement;
    }
    return false;
  }
  function mark(root) {
    if (!root) { return; }
    var walker = doc.createTreeWalker(root, 4, null, false);
    var list = [];
    var node;
    while ((node = walker.nextNode())) { if (hasDigit(node.nodeValue)) { list.push(node); } }
    for (var k = 0; k < list.length; k++) {
      var el = list[k].parentElement;
      if (el && !skip(el)) { el.classList.add("nb"); }
    }
  }
  win.__neoMark = mark;
  if (hide && !win.__neoCurtain) {
    win.__neoCurtain = true;
    var c = doc.createElement("style");
    c.id = "neo-curtain";
    c.textContent = ".stMainBlockContainer, .stSidebar { filter: blur(9px); }";
    doc.head.appendChild(c);
    setTimeout(function () { var x = doc.getElementById("neo-curtain"); if (x) { x.remove(); } }, 600);
  }
  if (!win.__neoWatch) {
    win.__neoWatch = true;
    var t1 = null;
    var t2 = null;
    var obs = new MutationObserver(function () {
      mark(doc.body);
      if (t1) { clearTimeout(t1); }
      if (t2) { clearTimeout(t2); }
      t1 = setTimeout(function () { mark(doc.body); }, 150);
      t2 = setTimeout(function () { mark(doc.body); }, 600);
    });
    obs.observe(doc.body, { childList: true, subtree: true, characterData: true });
    setInterval(function () { mark(doc.body); }, 900);
  }
  mark(doc.body);
})();
</script>
"""


def hidden():
    """True, если цифры сейчас скрыты."""
    if KEY not in st.session_state:
        st.session_state[KEY] = START_HIDDEN
    return bool(st.session_state[KEY])


def arm():
    """Ставит кнопку вверху страницы справа и размывает цифры."""
    hide = hidden()
    label = "\U0001F441  Показать цифры" if hide else "\U0001F648  Скрыть цифры"
    tip = "Открыть суммы" if hide else "Спрятать суммы"
    _left, _right = st.columns([5, 2])
    with _right:
        with st.container(key="eyebtn"):
            if st.button(label, key="eye_btn", help=tip):
                st.session_state[KEY] = not hide
                st.rerun()
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    if hide:
        st.markdown(CSS_BLUR, unsafe_allow_html=True)
    code = SCRIPT.replace("__HIDE__", "true" if hide else "false")
    st.markdown(code, unsafe_allow_html=True)
    components.html(code, height=0)
