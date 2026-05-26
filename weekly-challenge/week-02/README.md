# FastAPI 기반 게시판 서비스

> 위클리챌린지 2주차 - FastAPI 기반 게시판 서비스

---

## 소개

SQLite를 DB로 사용하는 RESTful 게시판 서버입니다.
Post / Comment CRUD와 Ollama를 중계하는 AI 요약 기능을 제공합니다.
단일 `main.py`로 시작해 Router → Controller → Model의 3-layer 구조로 리팩토링하는 과정까지 담은 프로젝트입니다.

---

## 목표

- REST 원칙에 맞는 Post / Comment CRUD API 설계 및 구현
- Ollama를 중계(Relay)하여 게시글 AI 요약 기능 추가
- 단일 `main.py` → 3-layer 구조(Router / Controller / Model)로 리팩토링

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Language | Python 3.11 |
| Framework | FastAPI |
| Server | Uvicorn |
| Database | SQLite (sqlite3) |
| Validation | Pydantic |
| HTTP Client | httpx |
| AI | Ollama (gemma4:e4b) |

---

## 주요 기능

**게시글 (Posts)**

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/posts/` | 글 생성 |
| GET | `/posts/` | 글 목록 조회 |
| GET | `/posts/{id}` | 글 상세 조회 |
| PATCH | `/posts/{id}` | 글 수정 |
| DELETE | `/posts/{id}` | 글 삭제 |

**댓글 (Comments)**

| Method | URL | 설명 |
|--------|-----|------|
| POST | `/posts/{id}/comments/` | 댓글 생성 |
| GET | `/posts/{id}/comments/` | 댓글 목록 조회 |
| PATCH | `/posts/{id}/comments/{cid}` | 댓글 수정 |
| DELETE | `/posts/{id}/comments/{cid}` | 댓글 삭제 |

**AI 요약 (Summary)**

| Method | URL | 설명 |
|--------|-----|------|
| GET | `/posts/{id}/summary` | 게시글 AI 요약 (Ollama Relay) |

---

## 프로젝트 구조

```
week-02/
├── main.py               # 앱 초기화 + 라우터 등록 (10줄)
├── schemas.py            # Pydantic 요청/응답 스키마
├── database/
│   └── db.py             # DB 연결 (get_db, create_db_and_tables)
├── models/
│   └── post.py           # DB 쿼리 전담
├── controllers/
│   └── post.py           # 비즈니스 로직, 에러 처리, AI 호출
└── routers/
    └── post.py           # URL 경로 정의
```

---

## 흐름

**요청 처리 흐름 (3-layer)**

```
클라이언트 요청
  └─ Router      URL 경로 → controller 연결
       └─ Controller   존재 확인 · 필드 검증 · AI 호출
            └─ Model        DB 쿼리 실행 (SELECT / INSERT / UPDATE / DELETE)
                 └─ database/db.py   SQLite 연결 제공
```

**AI 요약 흐름 (Relay 구조)**

```
클라이언트
  └─ GET /posts/{id}/summary
       └─ controller: 게시글 조회 → Ollama 호출
            └─ POST localhost:11434/v1/chat/completions
                 └─ { "summary": "..." } 반환
```

---

## 실행

```bash
cd weekly-challenge/week-02
fastapi dev main.py
# 또는
uvicorn main:app --reload
```

AI 요약 기능은 Ollama가 로컬에서 실행 중이어야 동작한다.

```bash
ollama serve
```

---

## 회고

처음에는 하나의 `main.py`에서 모든 기능을 처리하는 단순한 구조로 시작했습니다. 
기능이 점점 늘어나면서 코드가 복잡해졌고, 이를 Router / Controller / Model의 3-layer 구조로 리팩토링하게 되었습니다.

API 명세부터 구조 설계까지 스스로 결정하며 진행했고, 막히는 부분은 공식 문서와 다른 사람들의 구현 코드를 찾아보며 하나씩 해결해나갔습니다. 직접 에러를 겪고 원인을 추적하며 수정하는 과정에서, 단순히 문법을 사용하기 보다 동작 원리를 이해하게 되었습니다.

FastAPI를 사용해 CRUD 구조 설계, SQLite 연동, Ollama 기반 로컬 LLM 연동까지 전체 흐름을 경험하면서, 단순히 개념을 아는 것과 실제로 직접 구현해보는 것은 다르다는 점을 크게 느꼈습니다.

특히 구현 과정에서 “사용자 입장에서 리소스를 어떻게 식별해야 하는가”를 계속 고민하게 되었습니다. 
초기에는 리스트 인덱스를 기준으로 처리했지만, 삭제 이후 index가 변경되면서 리소스 식별이 깨지는 문제를 겪었습니다. 이 과정을 통해 ID를 안정적으로 유지하는 것이 왜 중요한지 직접 체감할 수 있었습니다.
또한 기능 구현에만 집중하는 것이 아니라, 각 레이어가 어떤 책임을 가져야 하는지, 어떤 데이터를 주고받아야 하는지까지 고민해보며 설계 관점으로 바라보려고 노력했습니다.

무엇보다 처음부터 끝까지 직접 구현하고 구조를 개선해봤다는 점에서 큰 의미가 있었고, 이번 프로젝트를 계기로 앞으로도 더 좋은 코드와 설계에 대해 계속 고민하며 성장하고 싶습니다.

---

<details>
<summary><strong>구현 과정에서 배운 점</strong></summary>

<br>

#### 1. import 경로와 패키지 구조

파일을 폴더 단위로 분리하면서 import 경로 문제를 가장 먼저 겪었습니다.

처음에는 잘못된 경로를 참조했고, 패키지 구조에서는 `폴더명.파일명` 형태로 정확히 import해야 한다는 점을 에러를 통해 익혔습니다.

이를 통해 Python이 모듈을 탐색하는 방식과 패키지 구조를 구조적으로 이해하게 되었습니다.

---

#### 2. generator와 context manager의 차이

`get_db()`를 `yield` 기반으로 구현한 뒤, `with get_db() as conn:`이 동작하지 않는 문제를 겪었습니다.

이 과정을 통해 `yield`가 포함된 함수는 generator 함수가 되며, `with` 문에서 사용하려면 `@contextmanager`가 필요하다는 점을 제대로 이해했습니다.

이전에는 문법처럼 외우던 개념이었는데, 직접 동작 원리를 부딪혀보며 흐름을 이해할 수 있었습니다.

---

#### 3. 레이어 간 반환값 설계의 중요성

초기에는 model 함수의 반환값을 충분히 고민하지 않고 구현했습니다.

예를 들어 model이 ID만 반환하면, controller에서 다시 SELECT를 호출해야 하는 비효율적인 흐름이 생겼습니다.

이 경험을 통해 “각 레이어가 무엇을 입력받고 무엇을 반환할지 먼저 정의해야 한다”는 점을 배웠습니다.

단순 구현보다 인터페이스 설계가 중요하다는 점을 체감할 수 있었습니다.

---

#### 4. 리스트 index 기반 ID 관리 문제

초기 in-memory 구현에서는 list index를 ID처럼 사용했습니다.

하지만 게시글 삭제 이후 index가 변경되면서, 기존 리소스가 다른 게시글을 가리키는 문제가 발생했습니다.

이를 해결하기 위해:

- 전역 ID 카운터 사용
- SQLite `AUTOINCREMENT` 적용

위 방식으로 수정했습니다.

이 과정을 통해 REST API에서 리소스 ID는 안정적으로 유지되어야 한다는 점을 직접 체감할 수 있었습니다.

</details>

---

<details>
<summary><strong>설계 고민</strong></summary>

<br>

#### 왜 3-layer 구조로 분리했는가

단일 `main.py` 구조에서는 URL 처리, 비즈니스 로직, DB 쿼리가 하나의 함수 안에 섞이게 됩니다.

레이어를 분리하자 각 계층의 역할이 명확해졌고, 예를 들어 DB 구조가 바뀌어도 model만 수정하면 되는 형태가 되었습니다.

이번 프로젝트를 통해 “코드 분리는 단순 정리가 아니라 유지보수를 위한 설계”라는 점을 체감할 수 있었습니다.

</details>

---

<details>
<summary><strong>현재 한계</strong></summary>

<br>

- 인증 기능이 없어 모든 요청이 공개되어 있습니다.
- SQLite 기반이라 동시성 처리에는 한계가 있습니다.
- AI 요약 기능은 단순 relay 구조이며, streaming 응답이나 prompt 최적화는 적용하지 않았습니다.
- 예외 처리 방식이 레이어별로 완전히 분리되어 있지는 않습니다.

</details>

---

<details>
<summary><strong>앞으로 개선해보고 싶은 점</strong></summary>

<br>

- SQLAlchemy 기반 ORM 구조로 리팩토링
- Async DB 처리 및 connection pool 적용
- Request / Response schema 분리
- JWT 기반 인증/인가 추가
- AI 응답 streaming 처리
- Docker 기반 실행 환경 구성

</details>