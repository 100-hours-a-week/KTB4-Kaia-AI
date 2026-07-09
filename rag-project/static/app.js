const form = document.getElementById("ask-form");
const input = document.getElementById("question");
const submitBtn = document.getElementById("submit-btn");
const examples = document.getElementById("examples");
const flow = document.getElementById("flow");
const status = document.getElementById("status");
const thread = document.getElementById("thread");
const turnTemplate = document.getElementById("turn-template");
const statePanel = document.getElementById("state-panel");
const stateLabel = document.getElementById("state-label");
const stateText = document.getElementById("state-text");
const announcer = document.getElementById("announcer");
const corpusNote = document.getElementById("corpus-note");
const newThreadBtn = document.getElementById("new-thread-btn");
const themeToggleBtn = document.getElementById("theme-toggle-btn");
const themeToggleLabel = document.getElementById("theme-toggle-label");

const THREAD_ID_KEY = "kaia-thread-id";
const THEME_KEY = "kaia-theme";

marked.setOptions({ breaks: true, gfm: true });

function getThreadId() {
  let id = localStorage.getItem(THREAD_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(THREAD_ID_KEY, id);
  }
  return id;
}

function startNewThread() {
  localStorage.setItem(THREAD_ID_KEY, crypto.randomUUID());
  thread.innerHTML = "";
  statePanel.hidden = true;
  announcer.textContent = "새 대화를 시작했습니다.";
}

const darkMediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

function isDarkActive() {
  const saved = localStorage.getItem(THEME_KEY);
  return saved ? saved === "dark" : darkMediaQuery.matches;
}

function syncThemeToggleUi() {
  const dark = isDarkActive();
  themeToggleLabel.textContent = dark ? "라이트로" : "다크로";
  themeToggleBtn.setAttribute("aria-pressed", String(dark));
}

function toggleTheme() {
  const next = isDarkActive() ? "light" : "dark";
  localStorage.setItem(THEME_KEY, next);
  document.documentElement.dataset.theme = next;
  syncThemeToggleUi();
  announcer.textContent = next === "dark" ? "다크 모드로 전환했습니다." : "라이트 모드로 전환했습니다.";
}

themeToggleBtn.addEventListener("click", toggleTheme);
darkMediaQuery.addEventListener("change", () => {
  if (!localStorage.getItem(THEME_KEY)) {
    if (darkMediaQuery.matches) {
      document.documentElement.dataset.theme = "dark";
    } else {
      delete document.documentElement.dataset.theme;
    }
    syncThemeToggleUi();
  }
});
syncThemeToggleUi();

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// CommonMark 규칙상 닫는 **가 문장부호(예: ")") 바로 뒤에 오고 공백 없이
// 한글이 바로 이어지면 "닫는 델리미터"로 인정되지 않아 **가 그대로 노출된다
// (예: "**A(B)**입니다" → 굵게 안 됨). 공백 하나를 넣어 우회한다.
function fixEmphasisSpacing(text) {
  return text.replace(/([)\]"'”’])\*\*(?=[가-힣])/g, "$1** ");
}

// LaTeX($...$, $$...$$)는 markdown 파서가 모르는 문법이라 그대로 파싱하면
// 밑줄(_)이 이탤릭으로 오인되는 등 깨질 수 있어, 마크다운 변환 전에 토큰으로
// 빼뒀다가 렌더링 후 복원하고 KaTeX로 별도 typeset한다.
function renderAnswerMarkdown(target, rawText) {
  const mathTokens = [];
  const protectedText = fixEmphasisSpacing(rawText).replace(/\$\$[\s\S]+?\$\$|\$[^\n$]+?\$/g, (match) => {
    mathTokens.push(match);
    return `@@MATH${mathTokens.length - 1}@@`;
  });

  let html = DOMPurify.sanitize(marked.parse(protectedText));
  html = html.replace(/@@MATH(\d+)@@/g, (_, i) => escapeHtml(mathTokens[Number(i)]));

  target.innerHTML = html;

  if (window.renderMathInElement) {
    renderMathInElement(target, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
    });
  }
}

const MODE_STAMPS = {
  answer_question: { label: "질문에 답함", icon: "🔎", cls: "mode-badge--inquiry" },
  til_write: { label: "TIL로 저장됨", icon: "🌱", cls: "mode-badge--journal" },
  wil_synthesize: { label: "WIL로 종합됨", icon: "🗂️", cls: "mode-badge--journal" },
  retrospective_write: { label: "회고로 저장됨", icon: "📝", cls: "mode-badge--journal" },
};

function pickSample(list, n) {
  if (list.length <= n) return list;
  const step = list.length / n;
  return Array.from({ length: n }, (_, i) => list[Math.floor(i * step)]);
}

async function loadCorpus() {
  try {
    const res = await fetch("/corpus");
    if (!res.ok) return;
    const { count, topics } = await res.json();

    if (count > 0) {
      corpusNote.textContent = `현재 색인 문서: ${count}개`;
      corpusNote.hidden = false;
    }

    pickSample(topics, 3).forEach((topic) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip-example";
      btn.textContent = `${topic}에 대해 설명해줘`;
      examples.appendChild(btn);
    });
    if (topics.length > 0) examples.hidden = false;
  } catch (err) {
    // 코퍼스 정보는 부가 정보라 실패해도 질문 흐름엔 영향 없음
  }
}

function appendTurn(question, data) {
  const node = turnTemplate.content.cloneNode(true);
  const turnQuestion = node.querySelector(".turn-question");
  const answerEl = node.querySelector(".answer");
  const sourcesEl = node.querySelector(".sources");

  turnQuestion.textContent = question;
  renderAnswerMarkdown(answerEl, data.answer);
  data.tools_used.forEach((name) => {
    const stamp = MODE_STAMPS[name] ?? { label: name, icon: "•", cls: "mode-badge--other" };
    const badge = document.createElement("span");
    badge.className = `mode-badge ${stamp.cls}`;
    badge.textContent = `${stamp.icon} ${stamp.label}`;
    sourcesEl.appendChild(badge);
  });

  thread.appendChild(node);
  thread.scrollIntoView({ block: "end", behavior: "smooth" });

  const stampLabels = data.tools_used.map((name) => (MODE_STAMPS[name] ?? { label: name }).label);
  announcer.textContent = stampLabels.length
    ? `${stampLabels.join(", ")}.`
    : "답변을 표시했습니다.";
}

function showState({ label, text, isError }) {
  flow.classList.remove("is-loading", "is-settled");
  flow.hidden = true;
  status.hidden = true;
  stateLabel.textContent = label;
  stateText.textContent = text;
  statePanel.classList.toggle("is-error", Boolean(isError));
  statePanel.hidden = false;
  announcer.textContent = text;
}

async function ask(question) {
  flow.classList.remove("is-settled");
  flow.hidden = false;
  flow.classList.add("is-loading");
  status.hidden = false;
  statePanel.hidden = true;
  submitBtn.disabled = true;
  announcer.textContent = "생각 중입니다.";

  try {
    const res = await fetch("/converse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question, thread_id: getThreadId() }),
    });

    flow.classList.remove("is-loading");
    flow.classList.add("is-settled");
    status.hidden = true;

    if (res.ok) {
      const data = await res.json();
      appendTurn(question, data);
      return;
    }

    showState({
      label: "pipeline error",
      text: "답변 생성 파이프라인에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
      isError: true,
    });
  } catch (err) {
    showState({
      label: "connection error",
      text: "서버에 연결하지 못했습니다. 서버가 실행 중인지 확인해주세요.",
      isError: true,
    });
  } finally {
    submitBtn.disabled = input.value.trim().length === 0;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  submitBtn.disabled = true;
  ask(question);
});

input.addEventListener("input", () => {
  submitBtn.disabled = input.value.trim().length === 0;
});

examples.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip-example");
  if (!btn) return;
  ask(btn.textContent);
});

newThreadBtn.addEventListener("click", startNewThread);

submitBtn.disabled = true;
loadCorpus();
