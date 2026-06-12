# Mini GPT 한국어 언어모델 프로젝트

> 사전학습된 LLM을 쓰지 않고, **Transformer Decoder를 직접 구현 → 한국어로 학습 → FastAPI로 서빙**하는 것이 핵심 목표.

---

## 1. 프로젝트 목표

### 기술 목표
- Decoder-only Transformer를 PyTorch로 직접 구현
- Multi-Head Attention, QKV Projection, Causal Mask 직접 구현
- GPT 방식의 Next Token Prediction 학습
- 모델 저장/로드 + FastAPI 기반 API 서버 구현

### 학습 목표
- Transformer 구조를 코드 수준에서 이해
- 언어 모델의 학습(Pretraining) 과정을 직접 경험
- 실제 LLM 제작 파이프라인(데이터 → 토크나이저 → 학습 → 서빙) 경험

### 최종 목표
> 사전학습된 모델을 사용하는 수준을 넘어, 한국어 Transformer Decoder 기반 언어 모델을 직접 구현하고 학습하여 서비스화까지 경험한다.

---

## 2. 전체 파이프라인

```
데이터 수집
  ↓
토크나이저 학습
  ↓
Transformer 구현
  ↓
Pretraining
  ↓
모델 저장 (.pt)
  ↓
FastAPI 서빙
  ↓
챗봇 / 텍스트 생성 API
```

---

## 3. 전체 아키텍처

```
Corpus
  ↓
Tokenizer
  ↓
Token IDs
  ↓
Token Embedding + Position Embedding
  ↓
Transformer Decoder Block × n_layer
  ├── LayerNorm
  ├── Multi-Head (Causal) Self-Attention
  │     Input → Wq/Wk/Wv → Q,K,V → Attention Score → Causal Mask
  │           → Softmax → Weighted Sum → Wo
  ├── Residual Connection
  ├── LayerNorm
  ├── FeedForward (Linear → GELU → Linear)
  └── Residual Connection
  ↓
LM Head (Linear → vocab_size)
  ↓
Vocabulary Logits → Softmax → Next Token Prediction
```

---

## 4. 스택

| 역할 | 도구 |
|---|---|
| 모델 구현 & 학습 | PyTorch, Google Colab (GPU) |
| 서빙 | FastAPI, Mac (CPU) |
| 토크나이저 | SentencePiece BPE (vocab_size 8000~16000) |
| 데이터 | 한국어 위키피디아 + FineWeb Korean (100~500MB) |

---

## 5. 프로젝트 구조

```
project/
├── model.py          # MiniGPT, Block(TransformerBlock), CausalSelfAttention 클래스
├── tokenizer.py       # SentencePiece BPE 토크나이저 학습/적용
├── train.py           # 학습 루프 (Colab에서 실행, Pretraining)
├── main.py            # FastAPI 서버
├── data/
│   └── corpus.txt     # 한국어 학습 텍스트
└── checkpoints/
    └── mini_gpt.pt    # 학습된 가중치
```

---

## 6. 모델 구조 & 하이퍼파라미터

### 모델 구조

```
MiniGPT
├── Token Embedding   : nn.Embedding(vocab_size, n_embd)
├── Position Embedding: nn.Embedding(block_size, n_embd)
├── TransformerBlock × n_layer
│   ├── LayerNorm
│   ├── CausalSelfAttention (Multi-Head)
│   ├── Residual Connection
│   ├── LayerNorm
│   ├── FeedForward (Linear → GELU → Linear)
│   └── Residual Connection
└── LM Head: Linear(n_embd, vocab_size)
```

### 하이퍼파라미터 (기본값)

토크나이저(SentencePiece BPE)와 데이터셋(위키피디아 + FineWeb Korean, 100~500MB) 구성에 따른 값.

| 파라미터 | 기본값 | 의미 | 비고 |
|---|---|---|---|
| `block_size` | 128 | 최대 컨텍스트 길이 | |
| `n_embd` | 256 | 임베딩 차원 (`d_model`) | |
| `n_head` | 4 | 멀티헤드 어텐션 헤드 수 (`head_dim = 64`) | |
| `n_layer` | 6 | 트랜스포머 블록 수 | |
| `batch_size` | 64 | 배치 크기 | |
| `steps` | 20000 | 학습 스텝 수 | |
| `lr` | 1e-3 | 학습률 (AdamW) | |
| `dropout` | 0.1 | 드롭아웃 비율 | 대규모 코퍼스(위키+FineWeb) 기준 |
| `vocab_size` | 8000~16000 | 어휘 사전 크기 | SentencePiece BPE 기준 (7.1 참고) |

---

## 7. 토크나이저 & 데이터셋

### 7.1 토크나이저: SentencePiece BPE

- **방식**: 서브워드 단위 (SentencePiece BPE)
- **vocab_size**: 8000~16000
- **선정 이유**: 한국어에 효율적이고 GPT 계열에서 널리 사용되는 표준 방식 — 문자 단위보다 시퀀스가 짧아져 학습 효율이 좋음
- **참고**: 별도의 토크나이저 학습 단계가 필요 (`tokenizer.py`에서 corpus 기반으로 학습 후 저장)

### 7.2 데이터셋: 한국어 위키피디아 + FineWeb Korean

| 데이터 | 비율 | 특징 |
|---|---|---|
| 한국어 위키피디아 | 70% | 고품질, 노이즈 적음, 문법/어휘/문장구조 학습에 적합 |
| FineWeb Korean | 30% | 대규모, 다양한 주제, 자연스러운 웹 문체 학습 |

---

## 8. 학습 단계

### Stage 1: Pretraining (필수)

- **Objective**: Next Token Prediction
  - 예: 입력 `나는 오늘 밥을` → 정답 `먹었다`
- **Loss**: `CrossEntropyLoss()`
- **Optimizer**: `AdamW()`
- **저장**: `torch.save(model.state_dict(), "checkpoints/mini_gpt.pt")`

### Stage 2: Instruction Tuning (선택/확장)

Pretraining 완료 후, 대화형 응답이 가능하도록 추가 학습.

- **데이터 형태**:
  ```json
  {
    "instruction": "자기소개 해줘",
    "response": "안녕하세요. Mini GPT입니다."
  }
  ```
- **후보 데이터**: AI Hub 일상대화, AI Hub 질의응답, 직접 생성한 QA 데이터

---

## 9. Inference (텍스트 생성)

```
Prompt → Tokenizer → Model → Next Token → (반복) → 생성된 텍스트
```

---

## 10. 작업 순서 (체크리스트)

- [ ] 1. 데이터 준비 — 한국어 위키피디아 + FineWeb Korean 수집/전처리, `corpus.txt` 구성 (목표 100~500MB, 7:3 비율)
- [ ] 2. 토크나이저 — SentencePiece BPE 학습 (vocab_size 8000~16000), `tokenizer.py` 작성
- [ ] 3. 모델 구현 — `model.py` 작성 (CausalSelfAttention → TransformerBlock → MiniGPT)
- [ ] 4. 학습 — Colab에서 `train.py` 실행 (Stage 1: Pretraining) → `mini_gpt.pt` 저장
- [ ] 5. FastAPI 서버 — `main.py` 작성, `POST /generate` 로컬 테스트
- [ ] 6. 결과 확인 — 생성 품질 확인 및 하이퍼파라미터 조정
- [ ] 7. (확장) Instruction Tuning 데이터 구축 및 `finetune.py` 작성
- [ ] 8. (확장) `POST /chat` 엔드포인트 추가

---

## 11. 참고 / 향후 확장

- 강사님 Mini GPT 노트북(`llms-from-scratch/`) 기반으로 구현
- 학습(Colab) ↔ 서빙(Mac) 역할 분리
- 가중치는 `.pt` 파일로 저장 후 FastAPI 서버 시작 시 로드
- 향후 확장: 오픈소스 모델(Kanana, Qwen) 버전 엔드포인트를 추가해 자체 구현 모델과 성능 비교
