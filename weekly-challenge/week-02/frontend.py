import html as _html
import streamlit as st
import requests

BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Community Board",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

_CSS = """<style>
/* ── Streamlit chrome ──────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* ── CSS variables ─────────────────────────────────────────── */
:root {
    --meta:       rgba(128, 128, 128, 0.6);
    --border:     rgba(128, 128, 128, 0.13);
    --accent:     #5a67d8;
    --accent-bg:  rgba(90, 103, 216, 0.08);
    --accent-mid: rgba(90, 103, 216, 0.18);
}

/* ── Hero ──────────────────────────────────────────────────── */
.hero {
    padding: 1.75rem 0 1.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.hero-eye {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.45rem;
}
.hero-title {
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.1;
    margin-bottom: 0.4rem;
}
.hero-desc {
    font-size: 0.83rem;
    color: var(--meta);
}

/* ── Post card ─────────────────────────────────────────────── */
.pc-wrap  { padding: 0.15rem 0 0.1rem; }
.pc-title {
    font-size: 0.97rem;
    font-weight: 600;
    line-height: 1.35;
    margin-bottom: 0.3rem;
}
.pc-preview {
    font-size: 0.82rem;
    color: var(--meta);
    line-height: 1.5;
    margin-bottom: 0.5rem;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.pc-footer {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.35rem 0.55rem;
    font-size: 0.72rem;
    color: var(--meta);
}
.pc-author { font-weight: 500; }
.pc-sep    { opacity: 0.4; }
.pc-cmt {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    background: var(--accent-bg);
    color: var(--accent);
    padding: 0.1rem 0.45rem;
    border-radius: 99px;
    font-size: 0.68rem;
    font-weight: 600;
}

/* ── Post detail header ────────────────────────────────────── */
.ph-id    { font-family:ui-monospace,monospace; font-size:0.67rem; color:var(--meta); margin-bottom:0.3rem; }
.ph-title { font-size:1.65rem; font-weight:800; letter-spacing:-0.022em; line-height:1.2; margin-bottom:0.5rem; }
.ph-meta  { font-size:0.78rem; color:var(--meta); display:flex; align-items:center; gap:0.3rem; flex-wrap:wrap; }
.ph-meta .dot { opacity:0.35; }

/* ── Post body ─────────────────────────────────────────────── */
.post-body {
    font-size: 0.95rem;
    line-height: 1.95;
    padding: 1.25rem 0 0.75rem;
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Author avatar ─────────────────────────────────────────── */
.av {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.65rem;
    height: 1.65rem;
    border-radius: 50%;
    color: #fff;
    font-size: 0.6rem;
    font-weight: 700;
    vertical-align: middle;
    flex-shrink: 0;
    margin-right: 0.4rem;
}

/* ── Comment ───────────────────────────────────────────────── */
.cmt-meta   { font-size:0.8rem; margin-bottom:0.25rem; display:flex; align-items:center; }
.cmt-name   { font-weight:600; }
.cmt-date   { color:var(--meta); margin-left:0.45rem; font-size:0.72rem; }
.cmt-body   { font-size:0.875rem; line-height:1.65; padding-left:2.05rem; }

/* ── AI summary ────────────────────────────────────────────── */
.ai-pill {
    display: inline-block;
    background: var(--accent);
    color: #fff;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 99px;
    margin-bottom: 0.65rem;
}
.ai-card {
    border: 1px solid var(--accent-mid);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    background: var(--accent-bg);
    font-size: 0.9rem;
    line-height: 1.85;
    white-space: pre-wrap;
}

/* ── Sidebar stat ──────────────────────────────────────────── */
.sl { font-size:0.67rem; text-transform:uppercase; letter-spacing:0.07em; color:var(--meta); margin-bottom:0.2rem; }
.sv { font-size:1.3rem; font-weight:700; line-height:1; }

/* ── Nav elements ──────────────────────────────────────────── */
.bc { font-size:0.75rem; color:var(--meta); margin-bottom:0.65rem; }

/* ── Section count ─────────────────────────────────────────── */
.count-line { font-size:0.78rem; color:var(--meta); }

/* ── Button: global radius ─────────────────────────────────── */
div[data-testid="stButton"] > button {
    border-radius: 6px;
}
/* Subdued look for non-primary buttons */
div[data-testid="stButton"] > button:not([data-testid*="primary"]) {
    font-size: 0.82rem;
}
</style>"""

st.markdown(_CSS, unsafe_allow_html=True)


# ── Cached API (read operations) ──────────────────────────────────────────────

@st.cache_data(ttl=20, show_spinner=False)
def _cached_posts() -> list | None:
    try:
        r = requests.get(f"{BASE_URL}/posts/", timeout=8)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None

@st.cache_data(ttl=20, show_spinner=False)
def _cached_comment_count(post_id: int) -> int:
    try:
        r = requests.get(f"{BASE_URL}/posts/{post_id}/comments/", timeout=5)
        return len(r.json()) if r.ok else 0
    except requests.RequestException:
        return 0


# ── Mutation helpers (no cache) ───────────────────────────────────────────────

def _get(path: str):
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=8)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None

def _post(path: str, body: dict):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=body, timeout=8)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None

def _patch(path: str, body: dict):
    try:
        r = requests.patch(f"{BASE_URL}{path}", json=body, timeout=8)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None

def _delete(path: str) -> bool:
    try:
        return requests.delete(f"{BASE_URL}{path}", timeout=8).ok
    except requests.RequestException:
        return False

def _bust_cache():
    _cached_posts.clear()
    _cached_comment_count.clear()


# ── Navigation ────────────────────────────────────────────────────────────────

def nav_list(bust: bool = False):
    if bust:
        _bust_cache()
    st.session_state.update(
        page="list", selected_post_id=None, summary=None,
        edit_mode=False, confirm_delete=False, editing_cmt_id=None,
    )

def nav_detail(post_id: int):
    st.session_state.update(
        page="detail", selected_post_id=post_id, summary=None,
        edit_mode=False, confirm_delete=False, editing_cmt_id=None,
    )

def nav_write():
    st.session_state.page = "write"

def _init_state():
    for k, v in dict(
        page="list", selected_post_id=None, summary=None,
        edit_mode=False, confirm_delete=False, editing_cmt_id=None,
    ).items():
        st.session_state.setdefault(k, v)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _preview(content: str, max_len: int = 110) -> str:
    text = " ".join(content.split())
    return (text[:max_len] + "…") if len(text) > max_len else text

def _avatar(name: str) -> str:
    initial = _html.escape(name[0].upper()) if name else "?"
    hue = sum(ord(c) for c in name) % 360
    return f'<span class="av" style="background:hsl({hue},48%,42%)">{initial}</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(post_count=None):
    with st.sidebar:
        st.markdown("### 💬 게시판")
        st.caption("FastAPI · SQLite · Ollama")
        st.divider()

        if st.button("게시판 목록", use_container_width=True):
            nav_list(); st.rerun()
        if st.button("✏️ 새 글 쓰기", type="primary", use_container_width=True):
            nav_write(); st.rerun()

        if post_count is not None:
            st.divider()
            st.markdown(
                '<div class="sl">게시글</div>'
                f'<div class="sv">{post_count}</div>',
                unsafe_allow_html=True,
            )


# ── Components ────────────────────────────────────────────────────────────────

def render_summary_section(post_id: int):
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.markdown("**AI 요약**")
        st.caption("Ollama (gemma4:e4b)로 본문을 요약합니다")
    with col_btn:
        if st.button("요약 생성", type="primary", use_container_width=True, key="gen_summary"):
            with st.spinner("요약 중…"):
                try:
                    r = requests.get(f"{BASE_URL}/posts/{post_id}/summary", timeout=60)
                    if r.ok:
                        st.session_state.summary = r.json().get("summary", "")
                    else:
                        st.error("요약 실패 — Ollama가 실행 중인지 확인하세요.")
                except requests.RequestException:
                    st.error("서버 연결 오류")

    if st.session_state.summary:
        st.markdown(
            f'<div class="ai-card">'
            f'<div class="ai-pill">AI Summary</div><br>'
            f'{_html.escape(st.session_state.summary)}'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_comments(post_id: int, comments: list):
    if not comments:
        st.markdown(
            '<div style="padding:1.5rem 0;text-align:center;font-size:0.85rem;'
            'color:var(--meta)">아직 댓글이 없습니다.</div>',
            unsafe_allow_html=True,
        )
    else:
        for c in comments:
            c_id = c["comment_id"]
            date_str = str(c.get("created_at", ""))[:16]

            if st.session_state.editing_cmt_id == c_id:
                with st.form(f"ec_{c_id}"):
                    new_c = st.text_area(
                        "댓글 수정", value=c["content"], height=80,
                        label_visibility="collapsed",
                    )
                    col_x, col_s = st.columns([1, 2])
                    with col_x:
                        cancel_e = st.form_submit_button("취소", use_container_width=True)
                    with col_s:
                        save_e = st.form_submit_button("저장", type="primary", use_container_width=True)

                if cancel_e:
                    st.session_state.editing_cmt_id = None; st.rerun()
                if save_e:
                    if _patch(f"/posts/{post_id}/comments/{c_id}", {"content": new_c}):
                        st.session_state.editing_cmt_id = None; st.rerun()
                    else:
                        st.error("수정에 실패했습니다.")
            else:
                col_body, col_acts = st.columns([9, 1])
                with col_body:
                    st.markdown(
                        f'<div class="cmt-meta">'
                        f'{_avatar(c["author"])}'
                        f'<span class="cmt-name">{_html.escape(c["author"])}</span>'
                        f'<span class="cmt-date">{date_str}</span>'
                        f'</div>'
                        f'<div class="cmt-body">{_html.escape(c["content"])}</div>',
                        unsafe_allow_html=True,
                    )
                with col_acts:
                    if st.button("✏️", key=f"ec_{c_id}", help="수정", use_container_width=True):
                        st.session_state.editing_cmt_id = c_id; st.rerun()
                    if st.button("🗑️", key=f"dc_{c_id}", help="삭제", use_container_width=True):
                        if _delete(f"/posts/{post_id}/comments/{c_id}"):
                            _cached_comment_count.clear(); st.rerun()
                        else:
                            st.error("삭제에 실패했습니다.")

            st.divider()

    st.markdown("**댓글 작성**")
    with st.form("comment_form", clear_on_submit=True):
        c_author  = st.text_input("작성자", placeholder="이름")
        c_content = st.text_area("내용", height=80, placeholder="댓글을 입력하세요")
        if st.form_submit_button("댓글 등록", type="primary", use_container_width=True):
            if not (c_author and c_content):
                st.warning("작성자와 내용을 입력해주세요.")
            elif _post(f"/posts/{post_id}/comments/", {"author": c_author, "content": c_content}):
                _cached_comment_count.clear(); st.rerun()
            else:
                st.error("댓글 등록에 실패했습니다.")


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_list():
    posts = _cached_posts()
    if posts is None:
        st.error("서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.")
        render_sidebar()
        return

    render_sidebar(len(posts))

    # Hero
    st.markdown(
        '<div class="hero">'
        '<div class="hero-eye">Community Board</div>'
        '<div class="hero-title">게시판</div>'
        '<div class="hero-desc">생각을 나누고 이야기를 기록하는 공간입니다</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_count, col_btn = st.columns([5, 1])
    with col_count:
        st.markdown(
            f'<div class="count-line">총 {len(posts)}개의 게시글</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("✏️ 새 글 쓰기", type="primary", use_container_width=True):
            nav_write(); st.rerun()

    st.markdown('<div style="height:0.65rem"></div>', unsafe_allow_html=True)

    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해보세요!")
        return

    for post in reversed(posts):
        date_str = str(post.get("created_at", ""))[:10]
        preview  = _html.escape(_preview(post.get("content", "")))
        title    = _html.escape(post["title"])
        author   = _html.escape(post["author"])
        cmt_cnt  = _cached_comment_count(post["post_id"])

        with st.container(border=True):
            col_info, col_btn2 = st.columns([10, 1])
            with col_info:
                st.markdown(
                    f'<div class="pc-wrap">'
                    f'<div class="pc-title">{title}</div>'
                    f'<div class="pc-preview">{preview}</div>'
                    f'<div class="pc-footer">'
                    f'<span class="pc-author">{author}</span>'
                    f'<span class="pc-sep">·</span>'
                    f'<span>{date_str}</span>'
                    f'<span class="pc-cmt">💬 {cmt_cnt}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
            with col_btn2:
                st.markdown('<div style="margin-top:0.4rem"></div>', unsafe_allow_html=True)
                if st.button("→", key=f"v_{post['post_id']}", use_container_width=True):
                    nav_detail(post["post_id"]); st.rerun()


def page_write():
    render_sidebar()
    st.markdown('<div class="bc">게시판 › 새 글 쓰기</div>', unsafe_allow_html=True)
    st.markdown("## 새 글 작성")
    st.divider()

    with st.form("write_form"):
        author  = st.text_input("작성자", placeholder="이름을 입력하세요")
        title   = st.text_input("제목",   placeholder="제목을 입력하세요")
        content = st.text_area("내용", height=280, placeholder="내용을 입력하세요")

        col_cancel, col_submit = st.columns([1, 3])
        with col_cancel:
            cancel = st.form_submit_button("취소", use_container_width=True)
        with col_submit:
            submit = st.form_submit_button("등록하기", type="primary", use_container_width=True)

    if cancel:
        nav_list(); st.rerun()
    if submit:
        if not (author and title and content):
            st.warning("모든 항목을 입력해주세요.")
        elif _post("/posts/", {"author": author, "title": title, "content": content}):
            nav_list(bust=True); st.rerun()
        else:
            st.error("등록에 실패했습니다.")


def page_detail():
    post_id = st.session_state.selected_post_id
    post = _get(f"/posts/{post_id}")
    if post is None:
        st.error("게시글을 찾을 수 없습니다.")
        nav_list(); return

    comments = _get(f"/posts/{post_id}/comments/") or []
    render_sidebar()

    col_back, _ = st.columns([1, 7])
    with col_back:
        if st.button("← 목록"):
            nav_list(); st.rerun()

    date_str = str(post.get("created_at", ""))[:10]
    st.markdown(
        f'<div class="ph-id">#{post["post_id"]}</div>'
        f'<div class="ph-title">{_html.escape(post["title"])}</div>'
        f'<div class="ph-meta">'
        f'{_html.escape(post["author"])}'
        f'<span class="dot">·</span>{date_str}'
        f'<span class="dot">·</span>댓글 {len(comments)}개'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    tab_body, tab_summary, tab_comments = st.tabs([
        "본문",
        "✨ AI 요약",
        f"💬 댓글 ({len(comments)})",
    ])

    with tab_body:
        if not st.session_state.edit_mode:
            st.markdown(
                f'<div class="post-body">{_html.escape(post["content"])}</div>',
                unsafe_allow_html=True,
            )
            st.divider()
            col_e, col_d, _ = st.columns([1, 1, 5])
            with col_e:
                if st.button("✏️ 수정", use_container_width=True):
                    st.session_state.edit_mode = True; st.rerun()
            with col_d:
                if st.button("🗑️ 삭제", use_container_width=True):
                    st.session_state.confirm_delete = True; st.rerun()

            if st.session_state.confirm_delete:
                st.warning("이 게시글을 삭제하시겠습니까? 댓글도 함께 삭제됩니다.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("삭제 확인", type="primary", use_container_width=True, key="cdel"):
                        if _delete(f"/posts/{post_id}"):
                            nav_list(bust=True); st.rerun()
                        else:
                            st.error("삭제에 실패했습니다.")
                with col_no:
                    if st.button("취소", use_container_width=True, key="ccancel"):
                        st.session_state.confirm_delete = False; st.rerun()
        else:
            with st.form("edit_form"):
                new_title   = st.text_input("제목",  value=post["title"])
                new_content = st.text_area("내용",   value=post["content"], height=280)
                col_cx, col_sv = st.columns([1, 3])
                with col_cx:
                    cancel_e = st.form_submit_button("취소", use_container_width=True)
                with col_sv:
                    save_e = st.form_submit_button("저장", type="primary", use_container_width=True)

            if cancel_e:
                st.session_state.edit_mode = False; st.rerun()
            if save_e:
                payload = {}
                if new_title != post["title"]:       payload["title"]   = new_title
                if new_content != post["content"]:   payload["content"] = new_content
                if payload:
                    if _patch(f"/posts/{post_id}", payload):
                        _cached_posts.clear()
                        st.session_state.edit_mode = False; st.rerun()
                    else:
                        st.error("수정에 실패했습니다.")
                else:
                    st.session_state.edit_mode = False; st.rerun()

    with tab_summary:
        render_summary_section(post_id)

    with tab_comments:
        render_comments(post_id, comments)


# ── Entry ─────────────────────────────────────────────────────────────────────

_init_state()

{
    "list":   page_list,
    "write":  page_write,
    "detail": page_detail,
}.get(st.session_state.page, page_list)()
