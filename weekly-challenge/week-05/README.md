# 전이학습, 하이퍼파라미터 튜닝 & 언어모델

> 위클리챌린지 5주차 - ResNet50/VGG16 전이학습 비교, GridSearch/RandomSearch 튜닝, 한국어 챗봇 만들기

**위클리챌린지:** [weekly_challenge.ipynb](./weekly_challenge.ipynb)

---

## 개요

사전학습된 ResNet50과 VGG16에 동일한 커스텀 헤드를 붙여 CIFAR-10에서 전이학습 성능을 비교하고, RandomForest로 GridSearch와 RandomSearch의 튜닝 효율을 비교했다. 

---

## 구현 내용

### 1~3. ResNet50 vs VGG16 (CIFAR-10 전이학습)
- pretrained ResNet50 / VGG16의 conv(feature) layer만 가져와 GAP + FC(256) + FC(10) 커스텀 헤드 부착
- 동일한 DataLoader, 동일한 epoch(10)으로 각각 학습 후 비교
- Loss curve, 전체/클래스별 정확도, 예측 샘플 시각화로 비교

### 4. GridSearch vs RandomSearch
- `make_classification`으로 가상 데이터셋 생성 (1000 samples, 20 features)
- RandomForest 기준 GridSearch(27회 탐색) vs RandomSearch(20회 탐색) 비교

### 5. 한국어 챗봇 (Mini GPT)
- 사전학습 LLM 없이 Decoder-only Transformer를 직접 구현 (54.3M params, vocab=16000)
- Wikipedia + FineWeb-2 한국어 코퍼스(~11.5GB)로 사전학습 (30000 steps)
- FastAPI로 서빙 — 입력 텍스트 1개에 생성 파라미터 조합 최대 3개를 비교하는 `/tests` API
- 자세한 내용: [MiniGPT.md](./MiniGPT.md)

---

## 주요 결과

### ResNet50 vs VGG16 (CIFAR-10)

| Model | 전체 파라미터 | Test Accuracy |
|---------|---:|---:|
| ResNet50 | 24,035,146 | 48.50% |
| VGG16 | 138,491,442 | 47.48% |

### GridSearch vs RandomSearch

| Method | 탐색 횟수 | Best CV | Test Acc |
|--------|---:|---:|---:|
| GridSearch | 27 | 0.9275 | 0.9250 |
| RandomSearch | 20 | 0.9263 | 0.9250 |

---

## 회고
> MiniGPT-KO (한국어 언어모델 사전학습) 회고는 규모가 달라 별도 정리: [MiniGPT.md](./MiniGPT.md)