# Week 02 TIL — HTTP, LLM 연동, DB, 서비스 구조

> AI 백엔드를 만드는 데 필요한 레이어들을 처음부터 끝까지 쌓은 한 주였습니다.

**기간:** 2026-05-18 ~ 2026-05-22  
**키워드:** `HTTP` `FastAPI` `Ollama` `httpx` `직렬화` `스트리밍` `예외처리` `Database` `SQL` `디자인패턴` `CORS` `HTTPS`

---

## 📋 이번 주 학습 지도

| 날짜 | 주제 | 핵심 개념 |
|------|------|-----------|
| 05/18 | 클라이언트-서버, HTTP | 소켓, HTTP 메시지, FastAPI, REST, Pydantic |
| 05/19 | 로컬 LLM, 비동기 통신 | Ollama, httpx, 직렬화, 스트리밍, 예외처리 |
| 05/20 | 데이터베이스 기초 | RDB, SQL, ERD, Index, Transaction, NoSQL |
| 05/21 | 구조 개선, 프론트엔드 | Route-Controller-Model, 미들웨어, HTML/JS, CORS, Streamlit |
| 05/22 | 딥다이브 | HTTP vs HTTPS, TLS 핸드셰이크 |

---

## 📖 학습 내용

### Day 1 (05/18) — 클라이언트, 서버, HTTP

**개념 흐름:**

```
두 컴퓨터가 연결하고 싶다
    ↓ (어떻게?)
소켓으로 통로를 뚫는다
    ↓ (근데 뭐라고 말해야 해?)
HTTP라는 말하는 규칙을 쓴다
    ↓ (규칙에 맞게 쓴 요청서가)
HTTP 메시지다 — 시작줄 + 헤더 + 빈줄 + 본문
    ↓ (요청서에 "나 뭐 하고 싶어" 표시하는 게)
HTTP 메서드다 — GET / POST / PUT / PATCH / DELETE
    ↓ (서버가 처리 후 결과를 알려주는 게)
Status Code다 — 200 / 404 / 500...
    ↓ (이걸 파이썬으로 쉽게 구현하는 도구가)
FastAPI고, 그 설계 원칙이 REST다
```


---

#### 1-1. 클라이언트 / 서버

> 클라이언트는 서버에 필요한 데이터나 응답을 요청하고, 서버는 해당 요청을 받아서 결과를 반환한다.

데이터를 중앙에서 관리하고 여러 클라이언트에게 동시에 제공하기 위해서. 모든 기기가 데이터를 각자 저장하면 동기화가 불가능하다.

**핵심:**
- 역할 구분이지, 위치 구분이 아니다. **같은 컴퓨터도 요청하면 클라이언트, 응답하면 서버.**
- 브라우저(클라이언트)가 URL로 요청 → 서버가 HTML/JSON 등으로 응답
- API 서버가 외부 결제 API를 호출할 때는 그 서버도 클라이언트가 된다

> 클라이언트 = 손님(주문하는 쪽), 서버 = 바리스타(만들어서 주는 쪽)

🔗 [MDN - 클라이언트-서버 개요](https://developer.mozilla.org/ko/docs/Learn/Server-side/First_steps/Client-Server_overview)

---

#### 1-2. 소켓(Socket) / 포트(Port) / localhost

> 소켓은 TCP 배달망에 프로그래밍으로 접근할 수 있게 해주는 인터페이스. 포트는 한 컴퓨터에서 여러 프로그램을 구분하는 번호. localhost는 자기 자신(이 컴퓨터)을 가리키는 주소.

두 컴퓨터가 데이터를 주고받으려면 연결 통로가 필요하다. 소켓이 그 통로를 만들어준다.

**핵심:**
- "소켓이 서버보다 훨씬 더 큰 개념이다." 서버는 소켓을 사용하는 것이지, 소켓 = 서버가 아니다.
- 소켓은 TCP 네트워크 자체가 아니라, TCP에 접근하는 프로그래밍 인터페이스
- **잘 알려진 포트:** `22` SSH / `80` HTTP / `443` HTTPS / `8000` FastAPI 기본값
- 포트 `0~1023`은 well-known ports — 시스템 예약, 임의로 쓰면 충돌

> 소켓 = 전화기 자체 / 포트 = 회사 내선 번호 / localhost = 나 자신(127.0.0.1)

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))  # 내 컴퓨터 12345번 포트에 바인딩
server_socket.listen(1)
client_socket, addr = server_socket.accept()
client_socket.sendall("Hello".encode('utf-8'))
```

- 문자 → 바이트: `encode('utf-8')` (인코딩)
- 바이트 → 문자: `decode('utf-8')` (디코딩)

🔗 [MDN - TCP 글로서리](https://developer.mozilla.org/ko/docs/Glossary/TCP)

---

#### 1-3. HTTP (HyperText Transfer Protocol)

> 웹에서 클라이언트와 서버가 데이터를 주고받기 위한 통신 규약. TCP 위에서 동작하며, 메시지의 형식을 표준화한 것.

TCP만으로는 데이터를 전달할 수 있지만 형식이 없다. 서버가 보낸 "안녕히가세요손님"이 정상 응답인지 에러인지 클라이언트가 알 수 없다. HTTP는 이 형식을 표준화해서 어떤 브라우저든, 어떤 언어로 만든 서버든 같은 방식으로 통신할 수 있게 해준다.

**핵심:**
- "TCP는 규약이 없다. 본인들만의 규약으로 메시지를 주고받고 싶어서 HTTP가 나온 것."
- HTTP는 TCP 위에 얹힌 애플리케이션 프로토콜 — TCP가 배달망이라면, HTTP는 주문서 형식
- HTTP는 **Stateless(무상태)**: 요청 하나 끝나면 서버가 이전 요청을 기억 못 함 → 쿠키/세션/JWT 토큰이 필요한 이유

> TCP = 배달망 (내용물이 뭔지 상관없이 신뢰성 있게 전달)  
> HTTP = 주문서 형식 (메서드, URL, payload, 상태코드라는 약속)

---

#### 1-4. HTTP Message

> 클라이언트와 서버가 실제로 주고받는 데이터의 단위. 정해진 형식(시작줄 + 헤더 + 빈줄 + 본문)으로 구성된다.

**핵심:**

| 구성 요소 | 설명 | 비유 |
|---|---|---|
| 시작줄 (Start Line) | 뭘 요청/응답하는지 | 편지 제목 |
| 헤더 (Headers) | 본문에 대한 메타 정보 | 봉투에 적힌 정보 |
| 빈 줄 (Empty Line) | 헤더 끝, 본문 시작 구분선 | 헤더가 끝났다는 신호 |
| 본문 (Body) | 실제 데이터 (없을 수도 있음) | 편지 내용 |

```
요청:  GET /posts HTTP/1.1
       ↑     ↑        ↑
     메서드  경로   HTTP버전

응답:  HTTP/1.1 200 OK
                 ↑
              상태코드
```

> 요청 메시지 = 주문서: `GET /menu HTTP/1.1 → Host: cafe.com → (빈줄) → (본문 없음)`  
> 응답 메시지 = 영수증+음식: `HTTP/1.1 200 OK → Content-Type: application/json → (빈줄) → {음식 데이터}`

---

#### 1-5. HTTP 상태 코드 (Status Code)

> 서버가 요청 처리 결과를 숫자로 알려주는 코드.

**핵심:**
- **2xx** = 성공 / **3xx** = 리다이렉트 / **4xx** = 클라이언트 잘못 / **5xx** = 서버 잘못
- `401` vs `403`: 401 = **"누구세요?"**(로그인 필요), 403 = **"알긴 아는데 안 돼"**(권한 없음)

| 코드  | 의미                    | 한마디                             |
| --- | --------------------- | ------------------------------- |
| 200 | OK                    | 요청 성공                           |
| 201 | Created               | 새 리소스 생성 성공 (POST 후)            |
| 400 | Bad Request           | 클라이언트가 요청을 잘못 보냄                |
| 401 | Unauthorized          | 로그인이 필요함                        |
| 403 | Forbidden             | 로그인은 됐는데 권한이 없음                 |
| 404 | Not Found             | 그런 주소 없음                        |
| 422 | Unprocessable Entity  | 형식은 맞는데 내용이 이상함 (FastAPI 자주 등장) |
| 500 | Internal Server Error | 서버 내부 오류                        |


---

#### 1-6. HTTP 요청 메서드 (Request Methods)

> HTTP 요청에서 클라이언트가 서버에게 "무엇을 하고 싶은지" 의도를 전달하는 동사.

URL만으로는 "이 주소에서 데이터를 가져오고 싶은 건지, 새로 만들고 싶은 건지, 지우고 싶은 건지" 알 수 없다. 메서드가 그 의도를 명확하게 전달한다.

**핵심:**
- **CRUD ↔ HTTP 메서드 매핑**: Create=POST / Read=GET / Update=PUT·PATCH / Delete=DELETE
- GET: 데이터 조회, 쿼리스트링으로 데이터 전달 (`GET /weather?city=seoul`)
- POST: 데이터 생성, Body에 데이터 첨부
- PUT: 데이터 **전체** 교체 (빠진 필드는 null/기본값)
- PATCH: 데이터 **일부** 수정
- DELETE: 데이터 삭제
- **멱등성(Idempotency)**: 같은 요청을 여러 번 해도 결과가 같은 것 (GET, PUT, DELETE = 멱등 / POST = 멱등 아님)

> GET = 메뉴 보기 / POST = 주문하기 / PUT = 주문 전체 바꾸기 / PATCH = 주문 일부 수정 / DELETE = 주문 취소

---

#### 1-7. REST (RESTful API)

> API를 설계하는 원칙. URL은 자원(명사)으로, 행동은 HTTP 메서드(동사)로 표현하자는 약속.

API를 어떻게 만들든 상관없다면 팀마다 제각각이 된다. REST는 "URL은 자원(명사)으로, 행동은 메서드(동사)로"라는 설계 원칙. API만 봐도 뭘 하는 건지 직관적으로 알 수 있다.

**핵심:**
- **REST ≠ JSON.** REST는 **방식(설계 원칙)**, JSON은 **형식(데이터 표현)**이다.
- URL = 자원(명사): `/users`, `/posts/1`
- 행동 = HTTP 메서드(동사): GET / POST / PUT / DELETE

```
❌ 나쁜 설계:  GET /getPosts  /  GET /createPost  /  GET /deletePost/1
✅ REST식:    GET /posts     /  POST /posts       /  DELETE /posts/1
```

URL만 보면 **뭘 다루는지**, 메서드 보면 **뭘 하는지** 바로 읽힌다.

🔗 [Naver D2 - REST API 제대로 알고 사용하기](https://d2.naver.com/helloworld/4911107)

---

#### 1-8. JSON (JavaScript Object Notation)

> 어떤 언어에서든 읽고 쓸 수 있는 공통 데이터 형식.

클라이언트와 서버가 서로 다른 언어(Python, JS, Java...)를 쓸 수 있다. JSON은 어떤 언어에서든 읽고 쓸 수 있는 공통 포맷이다.

**핵심:**
- REST API의 표준 데이터 형식 (XML보다 가볍고 읽기 쉬워서 웹 API 표준이 됨)
- 파이썬 딕셔너리와 비슷하지만 다르다: 키는 반드시 큰따옴표, `True` → `true`, `None` → `null`
- `Content-Type: application/json` 헤더로 "본문이 JSON이다"를 명시

```json
{
  "name": "다은",
  "age": 25,
  "is_student": true
}
```

```python
import json

json.dumps({"name": "다은"})    # 딕셔너리 → JSON 문자열 (직렬화)
json.loads('{"name": "다은"}')  # JSON 문자열 → 딕셔너리 (역직렬화)
```

> JSON = 국제 공용어 (한국어 서버, 영어 클라이언트가 둘 다 아는 언어로 대화)

🔗 [파이썬 공식 docs - json 모듈](https://docs.python.org/ko/3/library/json.html)

---

#### 1-9. FastAPI

> 파이썬으로 빠르고 쉽게 API 서버를 만들 수 있는 웹 프레임워크.

HTTP 요청을 직접 소켓으로 파싱하면 너무 복잡하다. FastAPI는 URL 경로 + 메서드 조합으로 어떤 함수를 실행할지 자동으로 연결해주는 프레임워크.

**핵심:**
- `@app.get`, `@app.post` 등 **데코레이터**로 HTTP 메서드 + URL 경로 연결
- Pydantic 모델이 요청 Body를 자동으로 검증 → 형식 틀리면 422 반환
- **ASGI 기반** → 비동기(async/await) 지원, 동기 방식 Flask보다 빠름
- **WSGI vs ASGI**: WSGI = 동기 방식(Flask, Django), ASGI = 비동기 지원(FastAPI)
- **Uvicorn**: FastAPI 앱을 실제로 실행시켜주는 ASGI 서버

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):        # 요청 Body의 형태 정의
    name: str
    price: float

@app.get("/items")            # GET /items 요청이 오면 이 함수 실행
def get_items():
    return {"items": []}

@app.post("/items")           # POST /items 요청이 오면 이 함수 실행
def create_item(item: Item):  # Body를 Item 형태로 자동 파싱
    return {"created": item}
```

> FastAPI = 가게 운영 시스템 (손님(클라이언트) 주문이 들어오면 어느 직원(함수)한테 갈지 자동으로 연결)

🔗 [FastAPI 공식 문서](https://fastapi.tiangolo.com/ko/)

---

#### 1-10. Pydantic / DTO

> 데이터의 형식과 유효성을 자동으로 검증해주는 라이브러리. FastAPI에서 요청 Body의 구조를 정의하고 검증할 때 쓴다.

클라이언트가 보내는 데이터가 항상 올바른 형식이라는 보장이 없다. Pydantic 모델을 정의해두면 FastAPI가 요청 때 자동 검증하고, 틀리면 422를 반환한다.

**핵심:**
- `BaseModel`을 상속받아 클래스를 정의 → 타입 검증, 필수 필드 강제, IDE 자동완성이 한 번에 해결됨
- `.model_dump()` → Pydantic 모델을 딕셔너리로 변환 (직렬화의 한 형태)
- **DTO(Data Transfer Object)**: 계층 간에 데이터를 안전하게 전달하기 위한 객체 — Pydantic 모델이 이 역할

| | 딕셔너리 | Pydantic 모델 |
|--|--|--|
| 타입 검증 | ❌ 없음 | ✅ 자동 |
| 필수 필드 | ❌ 없음 | ✅ 강제 |
| 자동완성 | ❌ 없음 | ✅ IDE에서 지원 |
| 접근 방식 | `data["title"]` | `post.title` |

```python
from pydantic import BaseModel

class Post(BaseModel):
    title: str            # 필수 필드, 문자열이어야 함
    content: str
    view_count: int = 0   # 선택 필드, 기본값 0

@app.post("/posts")
def create_post(post: Post):   # 요청 Body를 Post 형태로 자동 파싱 + 검증
    return post
```

> 딕셔너리 = 아무 내용이나 들어갈 수 있는 가방  
> Pydantic 모델 = "이 칸에는 문자열, 저 칸에는 숫자만"이 표시된 정리함

🔗 [Pydantic 공식 문서](https://docs.pydantic.dev)  
🔗 [FastAPI 공식 - Pydantic 모델](https://fastapi.tiangolo.com/ko/tutorial/body/)

---

### Day 2 (05/19) — 로컬 LLM, httpx, 예외처리

> 🔜 작성 예정

---

### Day 3 (05/20) — 데이터베이스 기초

> 🔜 작성 예정

---

### Day 4 (05/21) — 구조 개선, 프론트엔드

> 🔜 작성 예정

---

### Day 5 (05/22) — 딥다이브: HTTP vs HTTPS

> 🔜 작성 예정

---

## 🔗 이번 주 개념 흐름

> 🔜 작성 예정
>
> `소켓 → HTTP → FastAPI` 로 시작해 `LLM 연동 → DB → 서비스 구조 → 프론트` 로 이어지는 흐름.
> AI 모델을 실제 서비스로 만들기 위한 레이어를 처음부터 끝까지 쌓은 한 주.

---

## 🔄 주간 회고

**잘 이해한 것:**
>

**아직 부족한 것:**
>

**이번 주 가장 인상 깊었던 것:**
>

---

## 📎 딥다이브 & 참고 자료

---