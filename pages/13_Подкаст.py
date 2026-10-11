"""
Страница «Подкаст» · Коченевских бюро
Рубрика «Вместо созвона»: месячный отчёт в тапочках, аудио + обложка.
Файлы лежат в папке Google Диска «Подкаст в тапочках».
"""
import streamlit as st
import urllib.request
import urllib.parse
import json
import os
try:
    import streamlit.components.v1 as components
except Exception:
    components = None

st.set_page_config(page_title="Подкаст · Коченевских", page_icon="◈", layout="wide")

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


# ── auth ──
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.warning("Сначала войдите на главной странице")
    st.stop()

# ── brand ──
ORANGE = "#F74028"
MINT = "#D6EFB9"
GRAPHITE = "#252525"
WHITE = "#FFFFFF"
LOGO_URL = "https://static.tildacdn.com/tild3538-3366-4836-a666-313132343465/Group_417.png"
FOLDER_ID = "1fUvnddR6ZN5H7WszOKU21Cwnvcc8OvIu"
MONTHS = {"01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель", "05": "Май",
          "06": "Июнь", "07": "Июль", "08": "Август", "09": "Сентябрь", "10": "Октябрь",
          "11": "Ноябрь", "12": "Декабрь"}

# ── CSS ──
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: {WHITE}; }}
    #MainMenu, header, footer {{ visibility: hidden; }}
    .ep-title {{ font-size: 1.6rem; font-weight: 300; color: {GRAPHITE}; }}
    .ep-note {{ font-size: 0.95rem; color: #6A6A6A; }}
</style>
""", unsafe_allow_html=True)


# ── шапка ──
st.markdown(f'<img src="{LOGO_URL}" style="height:30px">', unsafe_allow_html=True)
st.markdown(f'<h2 style="font-weight:300;font-size:1.9rem;color:{GRAPHITE};margin:0 0 2px">Подкаст</h2>', unsafe_allow_html=True)
st.caption('Рубрика «Вместо созвона». Раз в месяц вместо созвона: отчёт голосом, что было и что планируем.')

# ── Google auth ──
def _get_token():
    try:
        client_id = st.secrets["google_client_id"]
        client_secret = st.secrets["google_client_secret"]
        refresh_token = st.secrets["google_refresh_token"]
    except Exception:
        sp, tp = "/opt/data/google_client_secret.json", "/opt/data/google_token.json"
        if not os.path.exists(sp) or not os.path.exists(tp):
            return None
        client_id = json.load(open(sp))['installed']['client_id']
        client_secret = json.load(open(sp))['installed']['client_secret']
        refresh_token = json.load(open(tp))['refresh_token']
    data = urllib.parse.urlencode({'client_id': client_id, 'client_secret': client_secret,
                                   'refresh_token': refresh_token, 'grant_type': 'refresh_token'}).encode()
    try:
        req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())['access_token']
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def load_episodes():
    token = _get_token()
    if not token:
        return []
    q = urllib.parse.quote("'" + FOLDER_ID + "' in parents and trashed=false")
    url = ('https://www.googleapis.com/drive/v3/files?q=' + q +
           '&orderBy=createdTime%20desc&pageSize=200&fields=files(id,name)')
    try:
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
        files = json.loads(urllib.request.urlopen(req, timeout=25).read())['files']
    except Exception:
        return []
    eps = {}
    for f in files:
        base, dot, ext = f['name'].rpartition('.')
        if base:
            eps.setdefault(base, {})[ext.lower()] = f['id']
    out = []
    for base, d in eps.items():
        audio = d.get('mp3') or d.get('m4a') or d.get('ogg') or d.get('wav')
        if audio:
            out.append({'base': base, 'audio': audio,
                        'cover': d.get('jpg') or d.get('jpeg') or d.get('png')})
    return sorted(out, key=lambda e: e['base'], reverse=True)


@st.cache_data(ttl=86400, show_spinner='Загружаю выпуск…')
def load_bytes(fid):
    token = _get_token()
    if not token:
        return None
    url = 'https://www.googleapis.com/drive/v3/files/' + fid + '?alt=media'
    try:
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()
    except Exception:
        return None


def pretty(base):
    parts = base.split('-')
    if len(parts) >= 2:
        return MONTHS.get(parts[-1], parts[-1]) + ' ' + parts[0]
    return base



PIN_JS = r"""<script>
(function () {
  var pd = window.parent.document;
  var LABEL = "__LABEL__";
  function findAudio() {
    var a = pd.querySelector("audio[data-testid=stAudio]");
    if (a) { return a; }
    var all = pd.querySelectorAll("audio");
    return (all && all.length) ? all[0] : null;
  }
  function hide(a) {
    if (a.parentElement) { a.parentElement.style.display = "none"; }
    a.style.display = "none";
  }
  function build(a) {
    var src = a.src;
    if (!src) { return false; }
    var bar = pd.createElement("div");
    bar.id = "neo-pod-pin";
    bar.style.cssText = "position:fixed;left:12px;right:12px;bottom:12px;z-index:2147483000;background:#252525;border-radius:14px;padding:10px 14px;box-shadow:0 10px 30px rgba(0,0,0,.35);display:flex;align-items:center;gap:12px;font-family:Inter,Arial,sans-serif";
    var lab = pd.createElement("div");
    lab.style.cssText = "color:#fff;font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:30%";
    lab.textContent = LABEL;
    var aud = pd.createElement("audio");
    aud.controls = true;
    aud.preload = "auto";
    aud.style.cssText = "flex:1;height:34px;min-width:0";
    var link = pd.createElement("a");
    link.textContent = "↗";
    link.title = "Открыть в отдельном окне";
    link.href = src;
    link.target = "_blank";
    link.style.cssText = "color:#D6EFB9;font-size:18px;text-decoration:none;padding:0 2px";
    var x = pd.createElement("div");
    x.textContent = "×";
    x.title = "Свернуть плеер";
    x.style.cssText = "color:#9A9A9A;font-size:22px;line-height:1;cursor:pointer;padding:0 4px";
    x.onclick = function () { if (bar.parentNode) { bar.parentNode.removeChild(bar); } };
    bar.appendChild(lab); bar.appendChild(aud); bar.appendChild(link); bar.appendChild(x);
    pd.body.appendChild(bar);
    fetch(src).then(function (r) { return r.blob(); }).then(function (b) {
      aud.src = URL.createObjectURL(b);
    }).catch(function () { aud.src = src; });
    return true;
  }
  var tries = 0;
  function start() {
    tries++;
    var a = findAudio();
    if (!a || !a.src) { if (tries < 60) { setTimeout(start, 500); } return; }
    hide(a);
    if (pd.getElementById("neo-pod-pin")) { return; }
    if (!build(a) && tries < 60) { setTimeout(start, 500); }
  }
  start();
})();
</script>
"""


def inject_js(code):
    if components is None:
        return
    try:
        components.html(code, height=0)
    except Exception:
        pass


eps = load_episodes()
if not eps:
    st.info('Подкастов пока нет. Как только файл появится в папке «Подкаст в тапочках» на Диске, страница покажет его сама.')
    st.stop()


def ep_block(ep, note=None, pin=False):
    cov = load_bytes(ep['cover']) if ep.get('cover') else None
    if cov:
        cols = st.columns([0.72, 1.56, 0.72])
        with cols[1]:
            st.image(cov, use_container_width=True)
    st.markdown('<div class="ep-title">Отчёт в тапочках · ' + pretty(ep['base']) + '</div>',
                unsafe_allow_html=True)
    if note:
        st.markdown('<div class="ep-note">' + note + '</div>', unsafe_allow_html=True)
    data = load_bytes(ep['audio'])
    if data:
        st.audio(data, format='audio/mpeg')
        if pin:
            inject_js(PIN_JS.replace('__LABEL__', 'Отчёт в тапочках · ' + pretty(ep['base'])))
    else:
        st.error('Аудио не загрузилось, проверьте доступ к Диску.')


ep_block(eps[0], 'Что нужно знать о прошедшем месяце и о планах на следующий. Наливай чай, открывай сайт и слушай.', pin=True)

if len(eps) > 1:
    st.markdown('---')
    st.markdown('<div class="ep-title" style="font-size:1.2rem">Предыдущие выпуски</div>', unsafe_allow_html=True)
    for e in eps[1:]:
        with st.expander('Отчёт в тапочках · ' + pretty(e['base'])):
            ep_block(e)
