# MiniGPT-KO

데이터 수집부터 토크나이저 학습, Transformer 구현, 사전학습, 그리고 FastAPI 기반 추론 서비스 구축까지 언어모델 개발의 전체 과정을 직접 경험하는 것을 목표로 했다.

최종적으로 약 11.5GB 규모의 한국어 코퍼스를 구축하고, 54.3M 파라미터 규모의 Mini GPT 모델을 학습하였다.

---

## 1. 전체 파이프라인

```text
Wikipedia + FineWeb-2 Korean
                ↓
      SentencePiece BPE
                ↓
          tokens.bin
                ↓
            MiniGPT
                ↓
            FastAPI
                ↓
           Streamlit
```

실제 구성은 다음과 같다.

```text
data_preprocess.py  →  corpus.txt (~11.5GB)
        ↓
tokenizer.py        →  tokenizer.model
        ↓
prepare_data.py     →  tokens.bin (~4.9GB)
        ↓
train.py            →  mini_gpt.pt (~54.3M params)
        ↓
FastAPI             →  Streamlit UI
```

데이터 생성, 토큰화, 학습은 Google Colab(A100)에서 수행하였고, 추론 서버와 UI는 로컬 환경(Mac)에서 실행하였다.

---

## 2. 데이터 & 토크나이저

### 데이터셋

한국어 Wikipedia 전체 데이터를 사용하고, 부족한 분량은 FineWeb-2 Korean으로 보충하여 최종적으로 약 11.5GB 규모의 코퍼스를 구축하였다.

| Dataset | Size | 특징 |
|----------|--------:|--------|
| Korean Wikipedia | ~1GB | 고품질 문어체 |
| FineWeb-2 Korean | ~10.5GB | 대규모 웹 문체 |
| Total | ~11.5GB | 학습용 코퍼스 |

### 토크나이저

토크나이저는 SentencePiece BPE를 사용하였다. vocab_size=16,000은 54M 규모 모델에서 임베딩 파라미터 비중이 과도해지지 않으면서 한국어 서브워드를 충분히 커버하는 절충값이다.

토큰화된 데이터는 `uint16` 기반의 `tokens.bin`으로 저장하고, 학습 시에는 `np.memmap`을 사용해 전체 데이터를 메모리에 올리지 않고 처리하였다.

---

## 3. 모델

GPT 계열과 동일한 Decoder-only Transformer 구조를 구현하였다.

```text
MiniGPT
├── Token Embedding
├── Position Embedding
├── Transformer Block × 12
│   ├── LayerNorm
│   ├── Multi-Head Causal Self-Attention
│   ├── Residual Connection
│   ├── LayerNorm
│   ├── Feed Forward Network
│   └── Residual Connection
└── LM Head
```

### 모델 구조

| 파라미터 | 값 | 설명 |
|---|---:|---|
| `n_layer` | 12 | Transformer 블록 수 |
| `n_head` | 8 | 어텐션 헤드 수 (head_dim=64) |
| `n_embd` | 512 | 임베딩 차원 |
| `block_size` | 256 | 최대 컨텍스트 길이 |
| `vocab_size` | 16,000 | SentencePiece BPE |
| `dropout` | 0.1 | 드롭아웃 비율 |
| 총 파라미터 수 | ~54.3M | |

---

## 4. 학습

언어모델은 Next Token Prediction 방식으로 학습하였다.

```text
입력 : 나는 오늘 밥을
출력 : 먹었다
```

와 같이 현재까지의 토큰을 보고 다음 토큰을 예측하는 방식이다.

### 학습 설정

- **Objective**: Next Token Prediction
- **Loss**: `CrossEntropyLoss`
- **Optimizer**: `AdamW` (lr=1e-3)
- **Batch Size**: 128
- **Steps**: 30,000 (Google Colab A100) — Chinchilla 법칙 기준 54M × 20 ≈ 10.9억 토큰에 맞춘 값
- **체크포인트**: 2,000 step마다 저장, `--resume`으로 중단된 학습 재개 가능

---

## 5. 추론 및 서빙

Pretraining만 수행한 모델은 멀티턴 대화에 적합하지 않다. 대신, **동일한 입력에 대해 생성 파라미터 조합을 최대 3개까지 동시에 실행하고 결과를 비교**하는 모델 성능 확인기 형태로 구성했다.

### FastAPI

생성 요청을 처리하고 결과를 SQLite에 저장한다.

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/tests` | 입력 텍스트 + 파라미터 조합(1~3개)으로 생성 실행 |
| GET | `/tests` | 전체 test 목록 조회 |
| GET | `/tests/{id}` | 단일 test 상세 조회 |
| DELETE | `/tests/{id}` | test 삭제 |

### Streamlit

입력 텍스트 하나에 대해 최대 3개 채널(CH1/CH2/CH3)을 동시에 실행하고, 생성 결과·소요 시간·tokens/sec를 나란히 비교하는 UI.

### 생성 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|------:|------|
| `temperature` | 0.8 | 분포 날카로움 조절 |
| `top_k` | 40 | 후보 토큰 수 제한 |
| `repetition_penalty` | 1.0 | 반복 억제 강도 |
| `max_new_tokens` | 80 | 최대 생성 토큰 수 |

---

## 6. 실험 결과 및 관찰

**streamlit UI**:
![Streamlit 결과 비교 화면](assets/screenshot.png)

### 실험 1 — repetition_penalty 3단계 비교

입력: `"딥러닝이란"` / temperature=0.8, top_k=40

| 채널 | repetition_penalty | 생성 결과 | tokens/sec |
|:----:|------------------:|:----------|----------:|
| CH1 | 1.0 | "딥러닝이란 무엇인가? 1.개념과 경험의 개념 2.실험과 분석 3.방법의 구조 3.실험과 분석 4.실험과 분석..." | 13.8 |
| CH2 | 1.2 | "딥러닝이란 무엇일까요? 우선 구글의 인공지능 기술을 어떻게 해석해야 할까요? AI를 이용해서 머신러닝을 하면..." | 35.1 |
| CH3 | 1.5 | "딥러닝이란, ‘언어학습’이라는 용어만으로도 통용된다... Symbolic Application (Contextual applications for your recurrence times...)" | 32.7 |

`repetition_penalty=1.0`은 "실험과 분석"을 10회 이상 반복했다. 1.2에서 반복이 사라지고 다양한 문장이 나왔으나, 1.5로 높이자 영어가 섞이는 과보정 현상이 나타났다.

### 실험 2 — temperature 3단계 비교

입력: `"한국의 역사는"` / repetition_penalty=1.2, top_k=40

| 채널 | temperature | 생성 결과 | tokens/sec |
|:----:|----------:|:----------|----------:|
| CH1 | 0.6 | "한국의 역사는 지금과 같은 수준이다. ≪현대문학≫은 그의 첫 번째 작품으로, 19세기 초에 한국문학의 시작을 알리는..." | 29.4 |
| CH2 | 0.8 | "한국의 역사는 어디에서 볼 수 있을까? 이 책은 ‘역사의 탄생’이라는 책을 통해 우리에게 새로운 의미와 역사가 탄생하게 되는..." | 33.4 |
| CH3 | 1.0 | "한국의 역사는 ‘미워도’이다. 한국에서는 현재 일본에서 가장 많이 번역되고 있는 책이며, 미국이나 캐나다와 같은 나라들은..." | 27.3 |

temperature가 낮을수록 위키피디아 스타일의 정돈된 문체, 높을수록 더 다양하지만 일관성이 떨어지는 출력이 나왔다. repetition_penalty로 반복을 억제한 상태에서 temperature 효과가 잘 드러난다.

---

## 7. 실행 방법

### Requirements

```bash
pip install -r requirements.txt
```

### 학습

```bash
python train.py
```

### FastAPI 실행

```bash
uvicorn main:app --reload
```

### Streamlit 실행

```bash
streamlit run frontend.py
```

> 현재 학습 데이터(`corpus.txt`, `tokens.bin`)와 모델 가중치(`mini_gpt.pt`)는 용량 문제로 저장소에 포함되어 있지 않습니다.

---

## 8. 회고

**배운 점**
- Transformer를 직접 구현하면서 Attention, Residual Connection, LayerNorm이 단순한 구성 요소가 아니라 학습 안정성을 위한 설계라는 점을 코드 수준에서 이해할 수 있었다.
- 처음에는 모델 구조가 성능을 결정한다고 생각했지만, 실제 학습 결과를 보면서 데이터 품질과 데이터 규모가 생성 품질에 더 큰 영향을 줄 수 있다는 점을 체감했다.
- 동일한 모델이라도 temperature, repetition_penalty 같은 디코딩 파라미터에 따라 출력 특성이 크게 달라진다는 점이 흥미로웠다. 모델 성능은 학습뿐 아니라 추론 전략에도 영향을 받는다는 사실을 배웠다.
- 모델 학습과 서비스 개발은 서로 다른 문제라는 점을 경험했다. FastAPI와 Streamlit을 연결하면서 모델 구현 외에도 API 설계, 응답 관리, 사용자 인터페이스가 필요하다는 것을 알게 되었다.
- 54M 규모 모델을 직접 학습해보며 현대 LLM의 성능이 단순히 모델 구조 때문이 아니라 데이터, 연산량, 학습 토큰 수, 후속 튜닝의 결과라는 점을 체감했다.

**어려웠던 점**
- 기대했던 수준의 생성 품질이 나오지 않았다. 처음에는 구현 문제라고 생각했지만, 모델 규모와 데이터 품질, 학습 예산이 결과에 큰 영향을 준다는 점을 이해하게 되었다.
- 적절한 하이퍼파라미터를 찾는 과정이 어려웠다. 특히 어떤 설정이 왜 성능에 영향을 주는지 설명하기 어려운 경우가 많았고, 체계적인 실험 설계의 필요성을 느꼈다.
- Google Colab 환경에서는 학습 시간과 자원이 제한적이어서 다양한 실험을 충분히 수행하기 어려웠다.

**보완하고 싶은 점**
- Instruction Tuning을 적용하여 단순 언어모델에서 사용자 지시를 따르는 모델로 발전시켜 보고 싶다.
- RoPE(Rotary Position Embedding)를 적용하여 더 긴 문맥을 효과적으로 처리할 수 있는지 실험해보고 싶다.
- 학습 로그와 평가 지표를 체계적으로 수집하는 평가 파이프라인을 구축하고 싶다.
- 추론 최적화 및 모델 압축 기법을 적용하여 실제 서비스 환경에서도 활용 가능한 수준으로 개선해보고 싶다.


---

**배운 점**
- ResNet50(24M)과 VGG16(138M)의 파라미터 수가 5배 이상 차이나는데 CIFAR-10 정확도는 48.50% vs 47.48%로 거의 같았다. 더 큰 모델이 항상 좋은 게 아니라, 태스크에 맞는 구조와 데이터가 중요하다는 걸 수치로 확인했다
- GridSearch(27회)와 RandomSearch(20회)가 동일한 Test Accuracy(0.9250)를 냈다. 탐색 횟수가 적어도 랜덤 샘플링이 충분히 좋은 조합을 찾을 수 있고, 탐색 공간이 커질수록 RandomSearch의 효율 이점이 더 커진다는 걸 배웠다
- pretrained conv layer를 그대로 두고 커스텀 헤드만 학습해도 빠르게 수렴했다. feature extractor를 건드리지 않아도 downstream 태스크에 적용된다는 걸 직접 확인했다

**어려웠던 점**
- 두 모델 모두 정확도가 50% 미만이었다. CIFAR-10은 32×32 저해상도 이미지라 ImageNet으로 학습된 feature가 충분히 전이되지 않은 것으로 보이는데, conv layer를 freeze한 채 헤드만 학습하는 방식의 한계를 느꼈다

**보완하고 싶은 점**
- conv layer 일부를 unfreeze해서 fine-tuning했을 때 성능이 얼마나 달라지는지 비교해보고 싶다
- Bayesian Optimization도 적용해서 GridSearch / RandomSearch와 탐색 효율을 비교해보고 싶다

> MiniGPT-KO (한국어 언어모델 사전학습) 회고는 규모가 달라 별도 정리: [MiniGPT.md](./MiniGPT.md)