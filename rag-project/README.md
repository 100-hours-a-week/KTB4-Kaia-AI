# Knowledge Gardener

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C)

> 개인의 학습 기록을 지속적으로 축적하고, 그 기록을 다시 검색 가능한 지식으로 활용하는 AI 학습 에이전트

Knowledge Gardener는 질문에는 근거 있는 답을 주고, 배운 내용은 잊지 않도록 기록해두는 개인 학습 에이전트입니다. 단순히 문서를 검색하는 RAG가 아니라, 질문과 학습 회고를 에이전트가 스스로 구분해 처리하고, 새로 쌓인 학습일지를 다시 지식베이스에 편입시켜 **매일 쓸수록 답변이 좋아지는 구조**를 목표로 합니다.

지금은 [CS231n](https://cs231n.github.io/) 강의 노트를 코퍼스 삼아 이 구조를 LangGraph 에이전트로 구현한 상태이고, 다음 단계는 쌓인 기록을 그래프로 연결해 벡터 검색만으로는 놓치는 다중 홉 질문에도 답하는 것입니다([로드맵](#로드맵) 참고).

---

## Why

대부분의 개인용 RAG는 "문서를 검색해서 답한다"에서 멈춥니다. 하지만 실제로 배운다는 건 문서를 읽는 것뿐 아니라, 그걸 소화해서 스스로 정리하는 과정이기도 합니다. Knowledge Gardener는 이 학습 과정 자체를 데이터로 다룹니다 — 검색으로 끝나는 게 아니라, 그 순간의 대화가 다음 검색의 근거로 남습니다.

---

## 주요 기능

**근거 기반 질의응답** (`answer_question`)  
검색된 문서에 근거해서만 답변을 생성하고, 참고한 문서(`sources`)를 함께 반환합니다. 검색 품질이 낮으면(top1 relevance score < 0.4) 질문을 다시 써서 재검색합니다 — 무한 루프 방지를 위해 최대 2회.

**학습일지 자동 저장** (`journal_write`)  
"오늘 ~공부했어", "~에서 막혔어" 같은 회고형 발화를 감지하면, 저장 여부를 먼저 확인한 뒤 `{주제, 배운 것, 막힌 것, 연결 개념}` 구조로 저장합니다. 날짜는 LLM이 아니라 서버가 직접 채워 신뢰가 필요 없는 사실까지 LLM에 맡기지 않습니다.

**질문 vs 회고, 에이전트가 스스로 판단**  
키워드 매칭이 아니라 LLM이 tool description을 보고 두 tool 중 무엇을 부를지 스스로 판단합니다(tool-calling). `MemorySaver` + `thread_id`로 멀티턴 맥락도 유지됩니다.

**계속 자라나는 지식베이스**  
저장된 학습일지는 기존 문서 인덱싱 파이프라인을 그대로 재사용해 검색 대상에 편입됩니다. 쓸수록 코퍼스가 늘어나고, 코퍼스가 늘어날수록 답변의 근거도 풍부해집니다.

---

## 데모

```
사용자: "Transformer의 Encoder와 Decoder 차이가 뭐야?"
   ↓
Agent가 answer_question 호출 → retrieve → grade_docs
   ├─ score ≥ 0.4 → generate: 문서 근거로 답변 생성
   └─ score < 0.4 → rewrite_query → retrieve 재시도 (최대 2회)
   ↓
답변 + 참고 문서(sources) 반환

사용자: "오늘 Attention 공부했어. Positional Encoding에서 막혔어."
   ↓
Agent가 journal_write 호출 (저장 여부 먼저 확인)
   ↓
{topic, learned, stuck, related_concepts} → data/journal/*.md 저장
   ↓
다음 인덱싱 시 검색 대상에 편입
```

---

## 아키텍처

![Architecture](diagram.svg)

서버 시작 시 에이전트 그래프를 한 번만 구성해 재사용합니다(요청마다 새로 만들지 않음).  \
사용자 메시지가 오면 LLM이 시스템 프롬프트와 대화 맥락을 보고 `answer_question` / `journal_write` 중 하나를 부르거나, 애매하면 되묻습니다. 모든 실행은 LangSmith로 추적·평가됩니다.

---

## 기술 스택

| 영역 | 선택 | 채택 근거 |
|---|---|---|
| 오케스트레이션 | LangGraph (StateGraph + tool-calling Agent) | 단일 체인(LCEL)은 조건 분기·재시도·대화 메모리를 표현할 방법이 없어 상태 기반 그래프로 전환 |
| 전처리 | [markitdown](https://github.com/microsoft/markitdown) | 형식(PDF, HTML, DOCX)이 달라도 하나의 코드로 Markdown 통일 |
| 청킹 | Markdown Header Splitter | 글자 수 분할은 섹션을 쪼개 검색이 부정확해져, 헤더 단위 분할로 의미를 보존 |
| 임베딩 | 로컬 `BAAI/bge-m3` | Gemini 임베딩 일일 한도 초과로 재인덱싱 불가 → 로컬 전환으로 무제한·무료·다국어 지원 |
| 벡터 DB | Chroma `PersistentClient` | Cloud 무료 300 레코드 제한을 넘어서, 로컬 디스크 영속 저장으로 전환 |
| 검색 재시도 | score 기반 `grade_docs` + `rewrite_query` | top1 relevance score < 0.4면 재검색, `retry_count` 최대 2회로 무한루프 방지 |
| 대화 라우팅 | tool-calling (`bind_tools` + `tools_condition`) | 키워드 매칭이 아니라 LLM이 tool description을 보고 스스로 판별 |
| 대화 메모리 | `MemorySaver` + `thread_id` | 멀티턴 대화에서 이전 맥락 유지 |
| 생성 LLM | `gemini-2.5-flash`(기본) · `gemma4:e2b`(Ollama) · `gemma-4-31b`(Cerebras) | 같은 코드로 provider만 바꿔 품질·속도·비용 A/B 비교 |
| 서빙 | FastAPI + lifespan | 에이전트 그래프는 서버 시작 시 1회 구성, 요청마다 `invoke()`만 호출 |
| 평가 | LangSmith | 답변 품질을 Dataset 점수로 측정 + 실행 과정 추적 |

---

## 프로젝트 구조

```
rag-project/
├── main.py              # FastAPI 진입점 (lifespan에서 에이전트 그래프 1회 구성)
├── graph.py              # QA 그래프(재검색 루프) / 에이전트 그래프(tool-calling+메모리)
├── nodes.py              # retrieve / generate / grade_docs / rewrite_query 노드
├── tools.py              # answer_question / journal_write
├── writer.py             # write_daily / write_weekly / write_til
├── rag.py                # 임베딩·벡터스토어·LLM 빌더
├── routers/ · controllers/ · schemas/   # API 레이어
├── prompts/              # 콘텐츠 프롬프트
├── static/                # 대화형 프론트엔드
├── data/, chroma_data/    # ← gitignore
└── docs/
```

---

## 실행 방법

```bash
uv sync
cp .env.example .env          # LLM_PROVIDER=google|ollama|cerebras, 실제 키 커밋 금지

uv run python preprocess.py   # data/raw/* → data/processed/*.md
uv run python rag.py          # 인덱싱 (chroma_data 생성, 최초 1회)
uv run uvicorn main:app --reload   # 서버 (http://localhost:8000)
```

---

## 로드맵

<details>
<summary><b>Hub — Graph RAG</b></summary><br>

개체·관계를 LLM으로 추출해 그래프로 저장하고, 질의 시 벡터 검색 + 그래프 탐색(1~2홉)을 결합해 다중 홉 질문에 답합니다. 코퍼스 전량을 한 번에 추출하면 무료 LLM 호출 한도를 넘기므로 신규/수정 노트만 증분 처리합니다. 목표: 다중 홉 질문 세트(n=10)에서 벡터-only 대비 정답률 +20%p.

</details>

<details>
<summary><b>Hub 고도화</b> — 재검색 LLM 채점, RAGAS, 하이브리드 검색</summary><br>

- 재검색 루프를 score 임계값 기반 `grade_docs`에서 LLM 채점(`grade_documents`)으로 교체
- RAGAS 도입 — `faithfulness`(목표 ≥0.80) · `context_recall`(목표 ≥0.70), 평가셋 20쌍 확보 후 적용
- 하이브리드 검색 — Chroma dense 검색 + BM25를 `EnsembleRetriever`로 결합
- 출처 문서 요약 tool 추가

</details>

<details>
<summary><b>Input Layer</b> — 판서 인식, 북마크 흡수</summary><br>

- 판서 인식 — 손글씨 사진 → VLM/OCR → 구조화 텍스트로 변환해 그래프·일지에 편입. 
- 북마크 흡수 — 북마크 URL → 본문 추출 → 그래프 편입 + 주기적 리서페이스(스케줄러)

</details>

<details>
<summary><b>Output Layer</b> — 마인드맵 시각화</summary><br>

- 마인드맵 시각화 — Graph RAG 서브그래프를 개념/일간/주간 단위로 렌더링
- 데모그래픽 시각화 - 이미지 한 장으로 학습 내용 복습할 수 있도록 제공

</details>

<details>
<summary><b>기타</b> — Streaming 응답</summary><br>

- Streaming 응답 — `stream_mode="messages"`

</details>

---

## 회고

- [7주차 회고](retro-week7.md) — FastAPI 서빙 + LangSmith 평가 도입
- [8주차 회고] — LCEL → LangGraph 마이그레이션: 설계 결정, 트러블슈팅, 평가 결과, API 레퍼런스
