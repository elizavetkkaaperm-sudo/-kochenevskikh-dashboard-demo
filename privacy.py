"""Глазок видимости: прячет все цифры на сайте.

Ставится одной строкой на странице после входа по паролю:

    import privacy
    privacy.arm()

Глазок висит в правом верхнем углу. Пока режим включён, все цифровые
элементы страницы размыты: таблицы, карточки, графики, метрики.
По умолчанию цифры скрыты, показывать их нужно осознанно.
"""
import streamlit as st

KEY = "hide_numbers"
START_HIDDEN = True

CSS_BASE = """
<style>
.st-key-eyebtn { position: fixed; top: 42%; right: 10px; z-index: 100000; }
.st-key-eyebtn button { width: 46px; height: 46px; border-radius: 50%; padding: 0; font-size: 20px; line-height: 1; border: 1px solid #E6E6E6; background: #FFFFFF; box-shadow: 0 2px 8px rgba(0, 0, 0, .12); }
.st-key-eyebtn button:hover { background: #FAFAFA; }
</style>
"""

CSS_BLUR = """
<style>
.nb, .nb * { filter: blur(7px) !important; transition: filter .15s ease; }
.stDataFrame, [data-testid="stDataFrame"], [data-testid="stTable"],
[data-testid="stPlotlyChart"], [data-testid="stArrowVegaLiteChart"] { filter: blur(7px) !important; }
</style>
"""

SCRIPT = """
<script>
(function () {
  var doc = window.parent.document;
  var win = doc.defaultView;
  function hasDigit(t) { return /[0-9]/.test(t); }
  function skip(el) {
    var up = el;
    for (var i = 0; i < 6 && up; i++) {
      if (up.tagName === "SCRIPT" || up.tagName === "STYLE") { return true; }
      if (up.classList && (up.classList.contains("nb") || up.classList.contains("st-key-eyebtn"))) { return true; }
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
  if (!win.__neoWatch) {
    win.__neoWatch = true;
    var timer = null;
    var obs = new MutationObserver(function () {
      if (timer) { clearTimeout(timer); }
      timer = setTimeout(function () { timer = null; mark(doc.body); }, 200);
    });
    obs.observe(doc.body, { childList: true, subtree: true, characterData: true });
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
    """Ставит глазок и размывает цифры, пока режим включён."""
    hide = hidden()
    eye = "\U0001F648" if hide else "\U0001F441"
    tip = "Показать цифры" if hide else "Скрыть цифры"
    with st.container(key="eyebtn"):
        if st.button(eye, key="eye_btn", help=tip):
            st.session_state[KEY] = not hide
            st.rerun()
    st.markdown(CSS_BASE, unsafe_allow_html=True)
    st.markdown(SCRIPT, unsafe_allow_html=True)
    if hide:
        st.markdown(CSS_BLUR, unsafe_allow_html=True)
