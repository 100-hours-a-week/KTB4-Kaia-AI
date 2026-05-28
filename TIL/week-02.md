# week2 TIL — HTTP, LLM 연동, DB, 서비스 구조

> 브라우저의 요청이 AI 모델 응답으로 돌아오기까지, 백엔드 서비스의 전체 흐름을 한 층씩 이해한 한 주

**기간:** 2026-05-18 ~ 2026-05-22

**키워드:** `HTTP` `FastAPI` `Ollama` `httpx` `직렬화` `스트리밍` `예외처리` `Database` `SQL` `디자인패턴` `CORS` `HTTPS`

---

## 📋 이번 주 학습 지도

| 날짜 | 주제 | 핵심 개념 |
|------|------|-----------|
| 05/18 | 클라이언트-서버, HTTP | 소켓, HTTP 메시지, FastAPI, REST, Pydantic |
| 05/19 | 로컬 LLM, 비동기 통신 | Ollama, httpx, 직렬화, 스트리밍, 예외처리 |
| 05/20 | 데이터베이스 기초 | RDB, SQL, ERD, Index, Transaction, NoSQL |
| 05/21 | 구조 개선, 프론트엔드 | 디자인 패턴, Route-Controller-Model, 미들웨어, HTML/JS, CORS, Streamlit |
| 05/22 | 딥다이브 | HTTP vs HTTPS, TLS 핸드셰이크 |

---

## 📖 학습 내용

### Day 1 (05/18) — 클라이언트, 서버, HTTP

**개념 흐름:**

```
두 컴퓨터가 연결하고 싶다
    ↓ (어떻게?)
소켓으로 통로를 뚫는다
    ↓ (근데 뭐라고 말해야 할까?)
HTTP라는 말하는 규칙을 쓴다
    ↓ (규칙에 맞게 쓴 요청서가)
HTTP 메시지다 — 시작줄 + 헤더 + 빈줄 + 본문
    ↓ (요청서에 "나 뭐 하고 싶어" 표시하는 게)
HTTP 메서드다 — GET / POST / PUT / PATCH / DELETE
    ↓ (서버가 처리 후 결과를 알려주는 게)
Status Code다 — 200 / 404 / 500...
    ↓ (이걸 파이썬으로 쉽게 구현하는 도구가)
FastAPI다 — HTTP를 추상화해 API 서버를 쉽게 만들 수 있는 프레임워크
    그 위에서 REST 설계 원칙을 적용한다
```

---

#### 1-1. 클라이언트 - 서버

> **클라이언트**는 서버에 필요한 데이터나 응답을 요청하고, **서버**는 해당 요청을 받아서 결과를 반환한다.

**사용 이유** \
여러 사용자가 동일한 데이터를 공유하고 사용할 수 있도록 하기 위해서다.  
데이터와 비즈니스 로직을 중앙에서 관리하면 유지보수와 동기화가 쉬워진다.
  
**핵심** 
- 역할 구분이지 위치 구분이 아니다
- **같은 컴퓨터라도 요청하면 클라이언트, 응답하면 서버가 될 수 있다**
- 브라우저(클라이언트)는 서버에 요청하고, 서버는 HTML/JSON 등을 응답한다
- API 서버가 외부 API를 호출할 때는 서버도 클라이언트 역할을 한다

**흐름** \
웹 서비스는 대부분 다음 흐름으로 동작한다.
```text
클라이언트 → 요청 → 서버 → 처리 → 응답 → 클라이언트
```
이 구조 위에서 HTTP, FastAPI, DB, LLM 연동 같은 기술들이 하나씩 추가된다.

**비유**
> 클라이언트 = 주문하는 손님  
> 서버 = 주문을 처리하는 바리스타
  

🔗 [MDN - 클라이언트-서버 개요](https://developer.mozilla.org/ko/docs/Learn/Server-side/First_steps/Client-Server_overview)


---  

#### 1-2. 소켓(Socket) / 포트(Port) / localhost

> 소켓은 네트워크 통신 기능에 프로그래밍적으로 접근하기 위한 인터페이스다. 포트는 한 컴퓨터에서 여러 프로그램을 구분하는 번호이고, localhost는 자기 자신(이 컴퓨터)을 가리키는 주소다.

**사용 이유** \
두 컴퓨터가 데이터를 주고받으려면 연결 통로가 필요하다.  
소켓은 그 통로를 만들고 데이터를 송수신할 수 있게 해준다.

**핵심**
- 소켓이 서버보다 큰 개념이다. 서버는 소켓을 사용하는 것이지, 소켓 = 서버가 아니다.
- 소켓은 TCP/IP 네트워크 기능을 사용할 수 있게 해주는 인터페이스
- 서버는 특정 포트에 바인딩되어 요청을 기다린다

**비유** 
> 소켓 = 전화기 자체  
> 포트 = 내선 번호  
> localhost = 자기 자신의 전화번호
  
**코드**

```python
import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))
server_socket.listen(1)

client_socket, addr = server_socket.accept()
client_socket.sendall("Hello".encode('utf-8'))
```

- 문자 → 바이트: `encode('utf-8')`
- 바이트 → 문자: `decode('utf-8')`


**🔍 탐구 내용:**
- **잘 알려진 포트:**
    - `22`: SSH
    - `80`: HTTP
    - `443`: HTTPS
    - `8000`: FastAPI 개발 서버에서 자주 사용
- 포트 `0~1023`은 well-known ports — 시스템 예약, 임의로 쓰면 충돌

  

---

#### 1-3. HTTP (HyperText Transfer Protocol)

> 웹에서 클라이언트와 서버가 데이터를 주고받기 위한 애플리케이션 계층 프로토콜.

**사용 이유** \
TCP는 데이터를 신뢰성 있게 전달해주지만, 메시지 형식 자체는 정의하지 않는다.  
HTTP는 요청과 응답이 어떤 구조로 오갈지 표준화한다.

**HyperText란** \
링크를 통해 다른 정보로 이동할 수 있는 텍스트. 웹에서 문서들이 서로 연결되는 방식의 기반이다.
(HTML, CSS, JS, 이미지 등 다양한 미디어를 포함한 형식으로 전달된다)

**핵심**
- HTTP는 TCP 위에서 동작한다
- 요청(Request)과 응답(Response) 구조를 정의한다
- HTTP는 **Stateless(무상태)** 프로토콜이다
- 이전 요청 상태를 기억하지 않기 때문에 쿠키/세션/JWT 등이 필요하다

**흐름** 
```text
TCP = 데이터를 안전하게 전달
HTTP = 어떤 형식으로 전달할지 정의
FastAPI = HTTP 요청을 실제 함수와 연결
```
HTTPS에서는 중간에 TLS 암호화 계층이 추가된다.

**HTTP의 역할** \
HTTP는 브라우저와 서버가 서로 다른 언어와 환경에서도 같은 방식으로 통신할 수 있게 해준다.
```text
브라우저(JS)
↕ HTTP
FastAPI(Python)
```

**비유**  
> TCP = 배달망 (내용물이 뭔지 상관없이 신뢰성 있게 전달)  
> HTTP = 주문서 형식 (메서드, URL, payload, 상태코드라는 약속)  
> HTTP 메시지가 TCP 배달망을 타고 전달된다  
  

---


#### 1-4. HTTP Message

> HTTP에서 실제로 주고받는 데이터 단위. 정해진 형식(시작줄 + 헤더 + 빈줄 + 본문)으로 구성된다.

**사용 이유** \ 
메시지 형식이 정해져 있어야 서버가 요청을 해석하고, 클라이언트가 응답을 이해할 수 있다.
HTTP Message가 그 표준 형식이다.

**핵심**

| 구성 요소 | 설명 | 비유 |
|---|---|---|
| 시작줄 (Start Line) | 뭘 요청/응답하는지 | 편지 제목 |
| 헤더 (Headers) | 본문에 대한 메타 정보 | 봉투에 적힌 정보 |
| 빈 줄 (Empty Line) | 헤더 끝, 본문 시작 구분선 | 헤더가 끝났다는 신호 |
| 본문 (Body) | 실제 데이터 (없을 수도 있음) | 편지 내용 |


```text
요청: GET /posts HTTP/1.1
      ↑     ↑      ↑
    메서드   경로  HTTP버전

응답: HTTP/1.1 200 OK
                ↑
              상태코드
```

**비유**  
> 요청 메시지 = 주문서: `GET /menu HTTP/1.1 → Host: cafe.com → (빈줄) → (본문 없음)`  
> 응답 메시지 = 영수증+음식: `HTTP/1.1 200 OK → Content-Type: application/json → (빈줄) → {음식 데이터}`


---

#### 1-5. HTTP 상태 코드 (Status Code)

> 서버가 요청 처리 결과를 숫자로 알려주는 코드.

**사용 이유** \
클라이언트는 요청이 성공했는지, 실패했는지, 권한이 없는지 등을 알아야 한다.

**핵심**
- **2xx** = 성공 / **3xx** = 리다이렉트 / **4xx** = 클라이언트 잘못 / **5xx** = 서버 잘못
- `401` vs `403`: 401 = **"누구세요?"**(로그인 필요), 403 = **"알긴 아는데 안 돼"**(권한 없음)
- 상태 코드는 클라이언트와 서버 간 "결과 피드백" 역할

**대분류:**

| 번호대 | 설명 |
| --- | ----------------------- |
| 1xx | 정보 메시지 (Informational) |
| 2xx | 성공 (Successful) |
| 3xx | 리다이렉션 (Redirection) |
| 4xx | 클라이언트 오류 (Client Error) |
| 5xx | 서버 오류 (Server Error) |
 

**주요 상태 코드:**

| 코드 | 의미 | 한마디 |
| --- | --------------------- | ------------------------------- |
| 200 | OK | 요청 성공 |
| 201 | Created | 새 리소스 생성 성공 (POST 후) |
| 400 | Bad Request | 클라이언트가 요청을 잘못 보냄 |
| 401 | Unauthorized | 로그인이 필요함 |
| 403 | Forbidden | 로그인은 됐는데 권한이 없음 |
| 404 | Not Found | 그런 주소 없음 |
| 422 | Unprocessable Entity | 형식은 맞는데 내용이 이상함 (FastAPI 자주 등장) |
| 500 | Internal Server Error | 서버 내부 오류 |


---

#### 1-6. HTTP 요청 메서드 (Request Methods)

> HTTP 요청에서 클라이언트가 서버에게 "무엇을 하고 싶은지" 의도를 전달하는 동사.

**사용 이유** \
같은 URL이라도 데이터를 조회하는지, 생성하는지, 수정하는지 구분해야 하기 때문이다.

**핵심**
- **CRUD ↔ HTTP 메서드 매핑**: Create=POST / Read=GET / Update=PUT·PATCH / Delete=DELETE
- GET: 데이터 조회, 쿼리스트링으로 데이터 전달 (`GET /weather?city=seoul`)
- POST: 데이터 생성, Body에 데이터 첨부
- PUT: 데이터 **전체** 교체 (빠진 필드는 null/기본값)
- PATCH: 데이터 **일부** 수정
- DELETE: 데이터 삭제

**비유** 
> GET = 메뉴 보기  
> POST = 주문하기  
> PUT = 주문 전체 바꾸기  
> PATCH = 주문 일부 수정  
> DELETE = 주문 취소  

**🔍 탐구 내용**
- **멱등성(Idempotency)**: 같은 요청을 여러 번 해도 결과가 같은 것 (GET, PUT, DELETE = 멱등 / POST = 멱등 아님)
- PUT과 PATCH의 차이: PUT = 리소스 **전체** 교체 / PATCH = **일부만** 수정


---

#### 1-7. REST (RESTful API)

> API를 설계하는 원칙. URL은 자원(명사)으로, 행동은 HTTP 메서드(동사)로 표현하자는 약속.

**사용 이유** \
API를 일관성 있게 설계하기 위해서다.  
REST 원칙을 따르면 API만 봐도 역할을 예측하기 쉬워진다.
  
**핵심**
- **REST ≠ JSON.** REST는 **방식(설계 원칙)**, JSON은 **형식(데이터 표현)**이다.
- URL = 자원(명사): `/users`, `/posts/1`
- 행동 = HTTP 메서드(동사): GET / POST / PUT / DELETE

**예시:**
```
❌ 나쁜 설계: GET /getPosts / GET /createPost / GET /deletePost/1
✅ REST식: GET /posts / POST /posts / DELETE /posts/1
```
- URL 보면 **뭘 다루는지**, 메서드 보면 **뭘 하는지** 알 수 있다.

  
---

#### 1-8. JSON (JavaScript Object Notation)

> 어떤 언어에서든 읽고 쓸 수 있는 공통 데이터 형식.

**사용 이유** \
클라이언트와 서버는 서로 다른 언어와 환경에서 동작할 수 있다.  
JSON은 대부분의 언어에서 쉽게 읽고 쓸 수 있는 표준 포맷이다.

**핵심**
- REST API의 표준 데이터 형식 (XML보다 가볍고 읽기 쉬워서 웹 API 표준이 됨)
- 파이썬 딕셔너리와 비슷하지만 다르다: 키는 반드시 큰따옴표, `True` → `true`, `None` → `null`
- `Content-Type: application/json` 헤더로 데이터 형식 명시

**코드**
```json
{
"name": "kaia",
"age": 25,
"is_student": true
}
``` 

```python
import json

json.dumps({"name": "kaia"}) # 딕셔너리 → JSON 문자열 (직렬화)
json.loads('{"name": "kaia"}') # JSON 문자열 → 딕셔너리 (역직렬화)
```

**흐름**
```text
파이썬 객체
→ JSON 직렬화
→ 네트워크 전송
→ JSON 역직렬화
→ 다시 객체로 사용
```

**비유**
> JSON = 국제 공용어 (한국어 서버, 영어 클라이언트가 둘 다 아는 언어로 대화)


🔗 [파이썬 공식 docs - json 모듈](https://docs.python.org/ko/3/library/json.html)


---

#### 1-9. FastAPI

> 파이썬으로 빠르고 쉽게 API 서버를 만들 수 있는 웹 프레임워크.

**사용 이유** \
HTTP 요청을 직접 소켓 단위로 처리하는 것은 매우 복잡하다.  
FastAPI는 URL과 HTTP 메서드를 함수와 연결해 API 서버를 쉽게 만들 수 있게 해준다.  

**핵심:**
- `@app.get`, `@app.post` 등 **데코레이터**로 HTTP 메서드 + URL 경로 연결
- Pydantic 모델이 요청 Body를 자동으로 검증 → 형식 틀리면 422 반환
- **ASGI 기반** → 비동기(async/await) 지원, 동기 방식 Flask보다 빠름
- **WSGI vs ASGI**: WSGI = 동기 방식(Flask, Django), ASGI = 비동기 지원(FastAPI)
- **Uvicorn**: FastAPI 앱을 실제로 실행시켜주는 ASGI 서버
  
**코드**

```python
from fastapi import FastAPI
from pydantic import BaseModel 

app = FastAPI()

class Item(BaseModel): # 요청 Body의 형태 정의
name: str
price: float

@app.get("/items") # GET /items 요청이 오면 이 함수 실행
def get_items():
return {"items": []}

@app.post("/items") # POST /items 요청이 오면 이 함수 실행
def create_item(item: Item): # Body를 Item 형태로 자동 파싱
return {"created": item}
```

**흐름**
```text
HTTP 요청
→ FastAPI 라우팅
→ 파이썬 함수 실행
→ JSON 응답 반환
```

**비유**
> FastAPI = 가게 운영 시스템 (손님(클라이언트) 주문이 들어오면 어느 직원(함수)한테 갈지 자동으로 연결)

🔗 [FastAPI 공식 문서](https://fastapi.tiangolo.com/ko/)


---


#### 1-10. Pydantic / DTO

> 데이터의 형식과 유효성을 자동으로 검증해주는 라이브러리. 데이터 구조와 타입을 검증하기 위한 모델.

**사용 이유** \
클라이언트가 보내는 데이터가 항상 올바른 형식이라는 보장이 없다. 
Pydantic 모델을 정의해두면 FastAPI가 요청 때 자동 검증할 수 있다.

  
**핵심**
- `BaseModel`을 상속받아 클래스를 정의 → 타입 검증
- 필수 필드 강제
- 자동완성이 지원
- `.model_dump()` → Pydantic 모델을 딕셔너리로 변환 (직렬화의 한 형태)
- **DTO(Data Transfer Object)**: 계층 간에 데이터를 안전하게 전달하기 위한 객체 <— Pydantic 모델

**코드**

```python
from pydantic import BaseModel

class Post(BaseModel):
title: str # 필수 필드, 문자열이어야 함
content: str
view_count: int = 0 # 선택 필드, 기본값 0

@app.post("/posts")
def create_post(post: Post): # 요청 Body를 Post 형태로 자동 파싱 + 검증
return post
```

  
**비유**  
> 딕셔너리 = 아무 내용이나 들어갈 수 있는 가방  
> Pydantic 모델 = "이 칸에는 문자열, 저 칸에는 숫자만"이 표시된 정리함  


🔗 [Pydantic 공식 문서](https://docs.pydantic.dev)
🔗 [FastAPI 공식 - Pydantic 모델](https://fastapi.tiangolo.com/ko/tutorial/body/)


---


### Day 2 (05/19) — 로컬 LLM, httpx, 예외처리

**개념 흐름:**

```
내 컴퓨터에서 LLM을 실행하고 싶다
    ↓ (어떻게?)
Ollama로 모델을 다운받아 로컬에서 실행
    ↓ (FastAPI 서버에서 이 LLM에 요청을 보내려면?)
httpx로 HTTP 요청을 직접 보낸다
    ↓ (요청에 담는 데이터는?)
페이로드(Payload) — JSON으로 직렬화해서 전달
    ↓ (응답이 한꺼번에 오지 않고 조금씩 오면?)
스트리밍(Streaming)으로 토큰 단위로 처리
    ↓ (요청 중 오류가 발생하면 어떻게 할까?)
try-except로 예외를 잡아 프로그램이 멈추지 않게 처리
    ↓ (네트워크 연결 같은 리소스는 쓰고 나서 꼭 닫아야 한다)
with문(컨텍스트 매니저)으로 자동으로 열고 닫는다
```
  
FastAPI 서버는 단순히 응답만 반환하는 것이 아니라,  
외부 LLM 서버(Ollama)에 다시 HTTP 요청을 보내고 결과를 가공해 클라이언트에게 전달하는 중간 계층 (middleware) 역할을 수행한다.

---

#### 2-1. Ollama

> 로컬 환경에서 LLM을 실행할 수 있게 해주는 오픈소스 플랫폼.  
  
**사용 이유** \
클라우드 API 없이 직접 LLM을 실행하기 위해 사용한다.
- 인터넷 없이 사용 가능
- API 비용 없음
- 데이터 외부 유출 최소화

**핵심**
- 모델 다운로드 및 실행 지원
- OpenAI API 호환 엔드포인트 제공
- 로컬 GPU/CPU에서 실행 가능
  
**비유**  
> 클라우드 LLM = 식당에서 시켜먹기, Ollama = 집에서 직접 요리하기  
> 더 느릴 수 있지만, 내 재료, 내 조리법, 외부 공개 없음  


**🔍 탐구 내용:**
- **엣지 AI**: 서버가 아닌 디바이스(노트북, 폰 등) 위에서 AI를 실행하는 개념
- 클라우드나 중앙 서버가 아닌 데이터가 생성되는 **'현장의 장치'에서 AI 모델을 직접 실행**
- 대부분 AI 프로세스는 상당한 컴퓨팅 용량이 필요해서 클라우드 기반 센터에서 수행하는데, 엣지 컴퓨팅은 데이터가 실제로 수집되는 곳에서 직접 계산을 수행

🔗 [엣지 AI란? — Superb AI Blog](https://blog-ko.superb-ai.com/real-time-ai-inference-edge-ai-innovation/)

---

#### 2-2. httpx
  
> Python에서 HTTP 요청을 보내기 위한 클라이언트 라이브러리.

**사용 이유** 
FastAPI 서버가 다른 서버(e.g. Ollama)에 다시 HTTP 요청을 보내야 하기 때문이다.

**핵심** \
- `requests`는 동기만 지원 → FastAPI의 async 환경에서는 `httpx`를 써야 한다
- `httpx.AsyncClient`를 사용하면 비동기로 다른 서버에 요청을 보낼 수 있다

**흐름**
```text
브라우저 → FastAPI
FastAPI → httpx → Ollama
```
- 클라이언트(브라우저, 앱) → FastAPI 서버 → Ollama LLM 서버: FastAPI가 중간에서 다시 HTTP 요청을 보내는 구조
- 브라우저 입장에서는 FastAPI가 **서버**, Ollama 입장에서는 FastAPI가 **클라이언트**
- Ollama한테 요청을 보내는 역할이 `httpx`


**코드:**

```python
import httpx

# 동기 방식
response = httpx.get("http://localhost:11434/v1/models")
print(response.json())

# 비동기 방식 (FastAPI에서 주로 이렇게 씀)
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:11434/v1/chat/completions",
        json={"model": "llama3", "messages": [...]}
    )
```

**🔍 탐구 내용:**
- HTTP/2: HTTP/1.1은 요청을 순차적으로 처리 / HTTP/2는 하나의 연결로 여러 요청을 동시에(멀티플렉싱)
- **비동기 지원이 왜 핵심 장점인가:** HTTP 요청은 "보내고 기다리는" 작업. 동기면 기다리는 동안 아무것도 못 하지만, 비동기(await)면 다른 사용자 요청을 처리할 수 있다.
    - 동기: 사용자 100명이면 스레드 100개 필요 → 메모리 문제
    - 비동기: await = "기다리되, 기다리는 동안 다른 일을 해도 된다"는 신호


---

#### 2-3. Payload & 직렬화

> **Payload(페이로드)** 는 HTTP 요청/응답의 본문에 담기는 실제 데이터. 헤더나 메타데이터를 제외한 순수 데이터,  
> **직렬화(Serialization)** 는 메모리 안 객체를 네트워크로 보낼 수 있는 형태(JSON 문자열/bytes)로 변환하는 과정  
> **역직렬화(Deserialization)** 는 받은 JSON/bytes를 다시 파이썬 객체로 복원하는 과정  

**사용 이유** \
네트워크에서는 결국 bytes 형태만 전달할 수 있기 때문이다.  

**핵심**
- `json.dumps()` = 직렬화 (파이썬 → JSON 문자열)
- `json.loads()` = 역직렬화 (JSON 문자열 → 파이썬)
- httpx에서 `json=` 파라미터를 쓰면 자동 직렬화 수행

**코드**

```python
import json

# 직렬화: 파이썬 → JSON 문자열
data = {"model": "llama3", "messages": [{"role": "user", "content": "안녕"}]}
json_str = json.dumps(data)

# 역직렬화: JSON 문자열 → 파이썬
parsed = json.loads(json_str)
  
# httpx는 자동 직렬화
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data) # json= 쓰면 자동 직렬화
    result = response.json() # 자동 역직렬화
```

**비유**
> 직렬화 = 택배 포장 (물건을 박스에 담기)  
> 역직렬화 = 택배 개봉 (박스에서 물건 꺼내기)  
> 페이로드 = 박스 안에 든 실제 물건  

---

#### 2-4. 스트리밍 (Streaming)

> 응답을 한 번에 모두 보내지 않고, 생성되는 즉시 조금씩 전달하는 방식.

**사용 이유** \
LLM 응답은 토큰 단위로 생성되기 때문에, 스트리밍을 사용하면 사용자는 응답이 생성되는 과정을 실시간으로 볼 수 있다.


**핵심**
- 응답을 청크(chunk) 단위로 받아 처리
- 서버는 SSE: Server-Sent Events 기반으로 데이터를 흘려보냄
- FastAPI에서는 `StreamingResponse`로 응답을 클라이언트에게 스트리밍할 수 있음
- 데이터가 다 왔을 때 `[DONE]` 신호가 옴

  
**코드**

```python
# httpx로 스트리밍 요청
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, json=payload) as response:
        async for chunk in response.aiter_text():
            if chunk:
                print(chunk, end="", flush=True)

  
# FastAPI에서 스트리밍 응답 반환
from fastapi.responses import StreamingResponse

async def generate():
    async with httpx.AsyncClient() as client:
        async with client.stream(...) as resp:
            async for chunk in resp.aiter_text():
                yield chunk
  
@app.post("/chat")
async def chat():
return StreamingResponse(generate(), media_type="text/event-stream")
```

**비유**
> 일반 응답 = 주방에서 밥 다 차려진 다음에 한꺼번에 서빙  
> 스트리밍 = 요리사가 만들면서 바로바로 접시에 올려 내보냄  

---

#### 2-5. 컨텍스트 매니저 (`with`문)
  
> 자원 관리 객체. 파일, 네트워크 연결 등 리소스를 쓸 때 코드 블록이 끝나면 자동으로 닫아주는 것
  
**사용 이유** \
자원의 생명 주기를 코드 구조로 강제하기 위함. 
직접 관리하게 되면 실수나 예외 상황에서 닫는 코드가 누락될 수 있는데, 자원 누수나 정리 누락 같은 실수를 방지할 수 있음.

**핵심**
- `with`가 끝나면 `__exit__`이 자동 호출됨 → 예외가 나도 반드시 닫힘
- `httpx.AsyncClient()`는 특히 커넥션 풀을 관리하므로, 반드시 `async with`로 써야 함
- `with`를 안 쓰면: 파일/연결이 안 닫혀 리소스 낭비


**코드**

```python
# ✅ with 사용 — 자동으로 닫힘
with open("data.txt", "r") as file:
content = file.read()
# with 블록 벗어나는 순간 file.close() 자동 호출

# httpx 비동기 예시
async with httpx.AsyncClient() as client:
re  ponse = await client.get("http://localhost:11434/...")
# 여기서 client가 자동으로 정리됨
```

```python
# with문의 동작 원리
class ResourceContext:
    def __enter__(self):
        print("시작 준비")
        return "실제 코드 실행"

def __exit__(self, exception_type, exception_value, traceback):
    print("마무리 정리") # 예외가 나도 항상 여기까지 옴
    
    with ResourceContext() as value:
        print(value)
```

🔗 [Python contextlib 공식 문서](https://docs.python.org/ko/3/library/contextlib.html)


---

#### 2-6. 예외 처리

> 프로그램 실행 중 발생 가능한 오류 상황에 대응하는 방법

**사용 이유** \
프로그램에서 예상치 못한 상황에 대비해 안정성을 높이고 오류를 관리하기 위해서. 
강제 종료될 만한 상황이 있을 때 강제 종료 상황을 만들지 않게 하기 위해 사용.
  
**early return (조기 반환)**

- 반환을 조기에 진행해서, 뒷코드 구조를 단순하게 만들어줌
- 코드 실행을 조건에 따라 빠르게 중단시켜 복잡한 조건문이나 중첩된 if문을 피하면서 **가독성을 높임**
- 언제? 일반적인 조건 분기, 유효성 검사

```python
# early return 미적용 — 끝까지 내려가는 구조
def check_age(age):
    if age >= 18:
      result = '성인입니다.'
    else:
        result = '미성년자입니다.'
    return result
  
# ✅ early return 적용 — 엣지케이스 먼저 처리
def check_age(age):
    if age < 18:
        return '미성년자입니다.'
        return '성인입니다.'
```

**try-except**
- try 블록 내에서 코드가 동작하는 동안 발생할 수 있는 **예외를 처리**
- 조기 리턴은 코드를 명확하고 간결하게 하기 위함(가독성), try-except는 에러가 발생했을 때를 처리하기 위함
- 언제? 네트워크 요청, 파일 I/O, 외부 API 호출


```python
# 기본 구조
try:
    # 동작 코드
    pass
    except Exception as error:
    return str(error)

# 실전: LLM 네트워크 요청
try:
    response = await client.post(url, json=payload, timeout=30.0)
    result = response.json()
    except httpx.TimeoutException:
        print("요청 시간 초과")
    except httpx.ConnectError:
        print("Ollama 서버에 연결할 수 없음. ollama serve가 실행 중인지 확인하세요.")
    except Exception as e:
        print(f"알 수 없는 오류: {e}")
finally:
    print("요청 완료") # 성공/실패 무관하게 항상 실행
```

  

**비유**  
> try = 시도해보기  
> except = 실패하면 이렇게 대응하기  
> finally = 성공이든 실패든 꼭 해야 할 마무리  

🔗 [Python 예외 처리 공식 문서](https://docs.python.org/ko/3/tutorial/errors.html)

  
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

  

```
[브라우저 / 클라이언트]
        ↓  HTTP 요청 (메서드 + URL + Body)
[FastAPI 서버]  ← Pydantic으로 요청 검증
        ↓  httpx로 HTTP 요청 (직렬화)
[Ollama LLM 서버]
        ↓  스트리밍 응답 (token by token)
[FastAPI]  ← 예외처리 / with문으로 리소스 관리
        ↓  StreamingResponse
[브라우저]

        + 중간에 DB 저장 (Day3)
        + 서비스 구조화 / 미들웨어 (Day4)
        + TLS 암호화 → HTTPS (Day5)
```

  

이번 주에는 단순히 개별 기술을 배우는 것이 아니라,
브라우저의 요청이 실제 AI 응답이 되어 돌아오기까지의 흐름을
하나의 시스템 관점에서 연결해보는 데 집중했다.

HTTP와 FastAPI로 API 서버를 만들고,
httpx를 통해 로컬 LLM 서버(Ollama)와 통신했으며,
스트리밍 응답과 예외처리를 통해 실제 서비스 구조를 경험했다.

여기에 DB로 데이터를 연결하고, 디자인 패턴으로 구조를 정리하고,
HTTPS로 전체 통신을 암호화하면 백엔드의 최소 가동 구조가 완성된다.

  

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