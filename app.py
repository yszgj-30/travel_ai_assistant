import re
import time
import requests
import streamlit as st

# ---------- Page config & dark travel theme ----------
st.set_page_config(
    page_title="Wander · 智能出行",
    page_icon="✧",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAIN_API = "http://127.0.0.1:8000/chat"

# ---------- Custom CSS: vintage travel desk aesthetic ----------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,500&family=JetBrains+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;600;700&display=swap" rel="stylesheet">

<style>
/* ---------- global ---------- */
:root {
    --ink: #f2e6d5;
    --paper: #1a1815;
    --card: #24211c;
    --amber: #d4a853;
    --amber-dim: #8b7338;
    --rust: #c47a4a;
    --sage: #7a9a7e;
    --slate: #5a7a8a;
    --divider: #3a3530;
    --muted: #9a9490;
    --radius: 2px;
}

/* override streamlit's default */
.stApp {
    background: var(--paper);
}

/* ---------- typography ---------- */
h1, h2, h3, .big-title {
    font-family: 'Playfair Display', 'Noto Serif SC', serif !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    letter-spacing: 0.02em;
}
h1 { font-size: 2.4rem !important; }
h2 { font-size: 1.4rem !important; font-weight: 500 !important; }
h3 { font-size: 1.1rem !important; color: var(--amber) !important; }

p, li, label, .stMarkdown, .stCaption {
    font-family: 'Noto Serif SC', 'JetBrains Mono', serif !important;
    color: var(--ink) !important;
    line-height: 1.7;
}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {
    background: #141210 !important;
    border-right: 1px solid var(--divider) !important;
}
[data-testid="stSidebar"] h2 {
    font-size: 1rem !important;
    color: var(--amber) !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid var(--divider) !important;
    color: var(--ink) !important;
    border-radius: var(--radius) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    text-align: left !important;
    padding: 0.6rem 0.9rem !important;
    transition: all 0.25s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: var(--amber) !important;
    color: var(--amber) !important;
    background: rgba(212, 168, 83, 0.06) !important;
}

/* ---------- chat ---------- */
[data-testid="stChatMessage"] {
    background: var(--card) !important;
    border: 1px solid var(--divider) !important;
    border-radius: var(--radius) !important;
    padding: 1.2rem 1.4rem !important;
    margin-bottom: 0.8rem !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdown"] p {
    font-size: 0.95rem;
}

/* chat input */
[data-testid="stChatInput"] textarea {
    background: var(--card) !important;
    border: 1px solid var(--divider) !important;
    border-radius: var(--radius) !important;
    color: var(--ink) !important;
    font-family: 'Noto Serif SC', serif !important;
    padding: 0.9rem 1rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 1px var(--amber-dim) !important;
}

/* ---------- status / alerts ---------- */
.stAlert {
    border-radius: var(--radius) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}
.stSuccess { background: rgba(122, 154, 126, 0.10) !important; border: 1px solid rgba(122, 154, 126, 0.25) !important; }
.stError   { background: rgba(196, 122, 74, 0.10) !important;  border: 1px solid rgba(196, 122, 74, 0.25) !important; }
.stInfo    { background: rgba(90, 122, 138, 0.10) !important;  border: 1px solid rgba(90, 122, 138, 0.25) !important; }
.stWarning { background: rgba(212, 168, 83, 0.08) !important; border: 1px solid rgba(212, 168, 83, 0.25) !important; }

/* ---------- spinner ---------- */
.stSpinner > div {
    border-color: var(--amber) transparent transparent transparent !important;
}

/* ---------- divider ---------- */
hr {
    border-color: var(--divider) !important;
    margin: 1.5rem 0 !important;
}

/* ---------- caption ---------- */
.stCaption {
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ---------- intent tag ---------- */
.intent-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 2px 10px;
    border-radius: var(--radius);
    margin-bottom: 6px;
}
.tag-weather { color: #d4a853; border: 1px solid #d4a85340; }
.tag-save    { color: #7a9a7e; border: 1px solid #7a9a7e40; }
.tag-route   { color: #5a7a8a; border: 1px solid #5a7a8a40; }
.tag-chat    { color: #9a9490; border: 1px solid #9a949030; }

/* ---------- status badge in sidebar ---------- */
.status-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
}
.status-online  { background: #7a9a7e; box-shadow: 0 0 6px #7a9a7e60; }
.status-offline { background: #c47a4a; box-shadow: 0 0 6px #c47a4a60; }

/* ---------- scrollbar ---------- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--paper); }
::-webkit-scrollbar-thumb { background: var(--divider); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
@st.cache_data(ttl=15)
def check_backend():
    try:
        r = requests.get("http://127.0.0.1:8000/docs", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def detect_intent(query: str) -> str:
    if any(kw in query for kw in ["天气", "气温", "下雨", "下雪", "温度", "风力"]):
        return "weather"
    if any(kw in query for kw in ["保存", "文件", "写入", "记录"]):
        return "save"
    if any(kw in query for kw in ["路线", "地图", "导航", "去哪", "怎么去", "行程", "规划"]):
        return "route"
    return "chat"


def intent_config(intent: str) -> dict:
    return {
        "weather": {"label": "天气查询", "tag": "tag-weather", "icon": "◇", "spinner": "正在调取气象数据 · 高德实时API"},
        "save":    {"label": "文件保存", "tag": "tag-save",    "icon": "◎", "spinner": "正在整理内容并写入磁盘"},
        "route":   {"label": "行程规划", "tag": "tag-route",   "icon": "◈", "spinner": "正在规划出行路线"},
        "chat":    {"label": "智能问答", "tag": "tag-chat",    "icon": "◇", "spinner": "思考中"},
    }.get(intent, {"label": "智能问答", "tag": "tag-chat", "icon": "◇", "spinner": "思考中"})


# ---------- Session ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ✧ WANDER")
    st.caption("智能出行助手")

    backend_ok = check_backend()
    dot = "status-online" if backend_ok else "status-offline"
    label = "API 在线" if backend_ok else "API 离线"
    st.markdown(
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;color:var(--ink);margin:1rem 0;">'
        f'<span class="status-dot {dot}"></span>{label}</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("##### 快捷指令")
    shortcuts = [
        ("◇ 查天气 · 北京", "北京今天天气"),
        ("◇ 查天气 · 上海", "上海今天天气"),
        ("◎ 保存计划", "帮我保存旅行计划：周末杭州西湖一日游，上午断桥苏堤，下午龙井村品茶"),
        ("◈ 规划路线", "杭州一日游最佳路线"),
    ]
    for label_text, query_text in shortcuts:
        if st.button(label_text, key=query_text, use_container_width=True):
            st.session_state.pending_input = query_text

    st.divider()
    st.caption("基于 LangGraph + 高德地图")
    st.caption(f"Session · {time.strftime('%H:%M')}")

# ---------- Header ----------
col_title, col_spacer = st.columns([3, 1])
with col_title:
    st.title("Wander")
    st.markdown(
        '<p style="color:var(--muted);font-size:0.9rem;margin-top:-0.5rem;">'
        '实时天气 &nbsp;·&nbsp; 行程规划 &nbsp;·&nbsp; 文件存档'
        '</p>',
        unsafe_allow_html=True,
    )

st.divider()

# ---------- Message history ----------
for msg in st.session_state.messages:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role):
        if role == "user":
            intent = detect_intent(msg["content"])
            cfg = intent_config(intent)
            st.markdown(
                f'<span class="intent-tag {cfg["tag"]}">{cfg["icon"]} {cfg["label"]}</span>',
                unsafe_allow_html=True,
            )
        st.markdown(msg["content"])

# ---------- Input ----------
user_input = st.chat_input("输入目的地或需求 …")

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    intent = detect_intent(user_input)
    cfg = intent_config(intent)

    # render user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(
            f'<span class="intent-tag {cfg["tag"]}">{cfg["icon"]} {cfg["label"]}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(user_input)

    # call API
    with st.chat_message("assistant"):
        placeholder = st.empty()
        elapsed = 0.0

        try:
            with st.spinner(cfg["spinner"]):
                t0 = time.time()
                res = requests.post(MAIN_API, json={"query": user_input}, timeout=25)
                elapsed = time.time() - t0

            if res.status_code == 200:
                data = res.json()
                reply = data.get("answer", "")

                if not reply:
                    st.error("后端返回空内容，请稍后重试")
                    st.session_state.messages.append({"role": "assistant", "content": "抱歉，未能获取回答。"})
                else:
                    st.markdown(reply)

                    # contextual feedback
                    if intent == "weather":
                        st.success(f"数据来源：高德地图实时天气 API · 响应 {elapsed:.1f}s")
                    elif intent == "save":
                        m = re.search(r"\./output/[\w.]+", reply)
                        file_hint = m.group() if m else "已保存"
                        st.success(f"磁盘写入完成 — {file_hint}")
                    elif intent == "route":
                        st.info("路线规划结果 · 建议配合地图应用查看")

                    st.session_state.messages.append({"role": "assistant", "content": reply})

            elif res.status_code == 422:
                st.warning("输入内容不符合要求，请检查后重试")
                st.session_state.messages.append({"role": "assistant", "content": "输入无效，请重新输入。"})
            else:
                st.error(f"服务异常 · HTTP {res.status_code}")
                st.session_state.messages.append({"role": "assistant", "content": f"服务异常（{res.status_code}）。"})

        except requests.Timeout:
            st.error("请求超时 · 服务端响应过慢，请稍后重试")
            st.session_state.messages.append({"role": "assistant", "content": "请求超时。"})
        except requests.ConnectionError:
            st.error("连接失败 · 请确认 API 服务已启动")
            st.session_state.messages.append({"role": "assistant", "content": "无法连接后端。"})
        except Exception as exc:
            st.error(f"未知错误 · {exc}")
            st.session_state.messages.append({"role": "assistant", "content": "发生未知错误。"})

        st.caption(f"模块 · {cfg['label']} &nbsp;|&nbsp; 响应 · {elapsed:.1f}s")
