import html

import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"

CH_COLORS = ["ch1", "ch2", "ch3"]

CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #1b1e1c;
    --surface: #232720;
    --surface-2: #2b3026;
    --line: #343a2e;
    --text: #ece9df;
    --text-muted: #8d9684;
    --ch1: #f2a33d;
    --ch2: #5fb8ae;
    --ch3: #d98c82;
}

html, body, h1, h2, h3, h4, p, span, label, div, button, textarea, input, li {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background-color: var(--bg);
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
    background-size: 44px 44px;
}

[data-testid="stSidebar"] {
    background-color: var(--surface);
    border-right: 1px solid var(--line);
}

.eyebrow {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: var(--text-muted) !important;
    margin: 0.2rem 0 0.3rem 0;
}

.ch-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    padding: 1px 8px;
    border-radius: 3px;
    border: 1px solid currentColor;
    margin-bottom: 0.5rem;
}
.ch-badge.ch1 { color: var(--ch1) !important; }
.ch-badge.ch2 { color: var(--ch2) !important; }
.ch-badge.ch3 { color: var(--ch3) !important; }

.run-id {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.4rem;
    font-weight: 600;
    color: var(--text) !important;
    line-height: 1.1;
}

.signal-box {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.92rem;
    color: var(--text) !important;
    background: var(--surface-2);
    border-left: 3px solid var(--text-muted);
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
    white-space: pre-wrap;
    margin-top: 0.5rem;
}

.param-row {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem;
    color: var(--text-muted) !important;
    letter-spacing: 0.03em;
    margin: 0.2rem 0 0.4rem 0;
}

.readout {
    background: var(--surface-2);
    border-radius: 6px;
    padding: 0.85rem 1rem;
    line-height: 1.65;
    min-height: 4.5rem;
    color: var(--text);
}

.meter-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-top: 0.6rem;
}
.meter-track {
    flex: 1;
    height: 5px;
    background: var(--surface-2);
    border-radius: 3px;
    overflow: hidden;
}
.meter-fill { height: 100%; border-radius: 3px; }
.meter-fill.ch1 { background: var(--ch1); }
.meter-fill.ch2 { background: var(--ch2); }
.meter-fill.ch3 { background: var(--ch3); }
.meter-value {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.74rem;
    color: var(--text-muted) !important;
    white-space: nowrap;
}

div.st-key-ch_card_0, div.st-key-result_0 {
    border-color: var(--ch1) !important;
    border-top-width: 3px !important;
    background: var(--surface) !important;
}
div.st-key-ch_card_1, div.st-key-result_1 {
    border-color: var(--ch2) !important;
    border-top-width: 3px !important;
    background: var(--surface) !important;
}
div.st-key-ch_card_2, div.st-key-result_2 {
    border-color: var(--ch3) !important;
    border-top-width: 3px !important;
    background: var(--surface) !important;
}

[data-testid="stSidebar"] .stButton button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem;
}
</style>
"""

st.set_page_config(page_title="Mini GPT 성능 확인기", page_icon="🎛️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


def _get(path: str):
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=120)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None


def _post(path: str, body: dict):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=body, timeout=300)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None


def _delete(path: str) -> bool:
    try:
        return requests.delete(f"{BASE_URL}{path}", timeout=10).ok
    except requests.RequestException:
        return False


def _init_state():
    st.session_state.setdefault("page", "new")
    st.session_state.setdefault("selected_test_id", None)


def nav_new():
    st.session_state.update(page="new", selected_test_id=None)


def nav_detail(test_id: int):
    st.session_state.update(page="detail", selected_test_id=test_id)


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="eyebrow">Mini GPT Bench</div>', unsafe_allow_html=True)
        st.markdown("### 🎛️ 성능 확인기")
        st.caption("샘플링 파라미터 채널 비교 도구")

        if st.button("+ 새 테스트", type="primary", use_container_width=True):
            nav_new(); st.rerun()

        st.markdown('<div class="eyebrow" style="margin-top:1.5rem;">Run Log</div>', unsafe_allow_html=True)

        tests = _get("/tests")
        if tests is None:
            st.error("서버에 연결할 수 없습니다.")
            return
        if not tests:
            st.caption("아직 실행된 테스트가 없습니다.")

        for t in reversed(tests):
            label = t["input_text"][:7] + ("…" if len(t["input_text"]) > 7 else "")
            col_label, col_del = st.columns([5, 1])
            with col_label:
                if st.button(f"#{t['id']:03d}  {label}", key=f"t_{t['id']}", use_container_width=True):
                    nav_detail(t["id"]); st.rerun()
            with col_del:
                if st.button("✕", key=f"d_{t['id']}", help="삭제"):
                    _delete(f"/tests/{t['id']}")
                    if st.session_state.selected_test_id == t["id"]:
                        nav_new()
                    st.rerun()


def render_results(results: list):
    max_tps = max((r["tokens_per_sec"] for r in results), default=0) or 1
    cols = st.columns(len(results))
    for i, (col, r) in enumerate(zip(cols, results)):
        ch = CH_COLORS[i % len(CH_COLORS)]
        with col, st.container(border=True, key=f"result_{i}"):
            cfg = r["config"]
            st.markdown(f'<span class="ch-badge {ch}">CH{i + 1}</span>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="param-row">temp {cfg["temperature"]} · top_k {cfg["top_k"]} · '
                f'rep {cfg["repetition_penalty"]} · max {cfg["max_new_tokens"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="readout">{html.escape(r["generated_text"])}</div>',
                unsafe_allow_html=True,
            )
            pct = (r["tokens_per_sec"] / max_tps) * 100
            st.markdown(
                f'<div class="meter-row">'
                f'<div class="meter-track"><div class="meter-fill {ch}" style="width:{pct:.0f}%;"></div></div>'
                f'<span class="meter-value">{r["tokens_per_sec"]:.1f} tok/s · {r["elapsed_time"]:.2f}s</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def page_new():
    st.markdown('<div class="eyebrow">Input Signal</div>', unsafe_allow_html=True)
    st.title("새 테스트")
    st.caption("입력 텍스트 1개에 샘플링 파라미터 조합(최대 3채널)을 동시에 실행해 비교합니다.")

    input_text = st.text_area("입력 텍스트", placeholder="예: 안녕하세요", height=120)

    num_configs = st.segmented_control("비교할 채널 수", [1, 2, 3], default=2)
    if num_configs is None:
        num_configs = 1

    configs = []
    cols = st.columns(num_configs)
    for i, col in enumerate(cols):
        ch = CH_COLORS[i % len(CH_COLORS)]
        with col, st.container(border=True, key=f"ch_card_{i}"):
            st.markdown(f'<span class="ch-badge {ch}">CH{i + 1}</span>', unsafe_allow_html=True)
            temperature = st.slider("temperature", 0.1, 2.0, 0.8, 0.1, key=f"temp_{i}")
            top_k = st.number_input("top_k", min_value=1, max_value=200, value=40, key=f"topk_{i}")
            repetition_penalty = st.slider("repetition_penalty", 1.0, 2.0, 1.0, 0.1, key=f"rep_{i}")
            max_new_tokens = st.number_input("max_new_tokens", min_value=10, max_value=200, value=80, key=f"max_{i}")
            configs.append({
                "temperature": temperature,
                "top_k": int(top_k),
                "repetition_penalty": repetition_penalty,
                "max_new_tokens": int(max_new_tokens),
            })

    if st.button("▶  실행", type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning("입력 텍스트를 입력해주세요.")
        else:
            with st.spinner("생성 중… (채널당 수 초~수십 초 소요)"):
                result = _post("/tests", {"input_text": input_text, "configs": configs})
            if result:
                nav_detail(result["id"]); st.rerun()
            else:
                st.error("요청에 실패했습니다. FastAPI 서버가 실행 중인지 확인하세요.")


def page_detail():
    test_id = st.session_state.selected_test_id
    test = _get(f"/tests/{test_id}")
    if test is None:
        st.error("테스트를 찾을 수 없습니다.")
        nav_new(); st.rerun()
        return

    st.markdown('<div class="eyebrow">Run Log</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="run-id">#{test["id"]:03d}</div>', unsafe_allow_html=True)
    st.caption(test["created_at"])
    st.markdown(f'<div class="signal-box">{html.escape(test["input_text"])}</div>', unsafe_allow_html=True)
    st.write("")
    render_results(test["results"])


_init_state()
render_sidebar()

if st.session_state.page == "detail" and st.session_state.selected_test_id is not None:
    page_detail()
else:
    page_new()
