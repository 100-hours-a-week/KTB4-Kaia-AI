# 전이학습, 하이퍼파라미터 튜닝 & 언어모델

> 위클리챌린지 5주차 - ResNet50/VGG16 전이학습 비교, GridSearch/RandomSearch 튜닝, 한국어 언어모델 구현

**위클리챌린지:** [weekly_challenge.ipynb](./weekly_challenge.ipynb)

---

## 개요

사전학습된 ResNet50과 VGG16을 CIFAR-10에 fine-tuning해 성능을 비교했다. 또한 RandomForest를 활용해 GridSearch와 RandomSearch의 탐색 효율을 비교했다.
추가로 Decoder-only Transformer 기반의 한국어 언어모델(Mini GPT)을 구현하고 학습 및 서빙 과정을 실습했다.

---

## 구현 내용

### Transfer Learning

- ResNet50 전이학습
- VGG16 전이학습
- CIFAR-10에 맞는 구조 수정
- Freeze / Unfreeze 전략 적용
- 학습 곡선 비교

### Hyperparameter Tuning

- GridSearch
- RandomSearch
- 탐색 횟수와 성능 비교

### Language Model (Mini GPT)

- Decoder-only Transformer 구현
- 한국어 코퍼스 학습
- FastAPI 기반 추론 API 구현
- 자세한 내용: [MiniGPT.md](./MiniGPT.md)

---

## 주요 결과

### CIFAR-10 Transfer Learning

#### 실험 설정

| 항목 | 값 |
|---|---|
| Dataset | CIFAR-10 (train 50,000 / test 10,000, 32×32) |
| Optimizer | AdamW (`lr=1e-4`, `weight_decay=1e-4`) |
| Scheduler | CosineAnnealingLR (`T_max=30`) |
| Epochs | 30 |
| Batch Size | 128 |

#### 성능

| Model | Test Accuracy |
|---------|---------:|
| ResNet50 | 84.22% |
| VGG16 | 83.35% |

두 모델 모두 ImageNet 사전학습 가중치를 활용했다.

ResNet50은 CIFAR-10 입력 크기에 맞게 Conv1과 MaxPool을 수정했고, VGG16은 Feature Map 크기를 유지하기 위해 일부 MaxPool을 제거했다.

이번 실험에서는 대부분의 레이어를 Freeze하고 마지막 블록과 분류기만 학습했다.

---

### GridSearch vs RandomSearch

| Method | Search Count | Test Accuracy |
|---------|---------:|---------:|
| GridSearch | 27 | 0.925 |
| RandomSearch | 20 | 0.925 |

RandomSearch가 더 적은 탐색 횟수로 비슷한 결과를 얻을 수 있음을 확인했다.

---

### Mini GPT

- Decoder-only Transformer 직접 구현
- 약 50M 파라미터 규모
- 한국어 Wikipedia, FineWeb 기반 학습
- FastAPI 추론 서버 구현

---

## 회고

### 배운 점

- 전이학습은 단순히 마지막 분류기만 교체하는 것이 아니라 어떤 레이어를 Freeze할지 결정하는 과정이라는 점을 이해하게 되었다. 처음에는 "특징 추출기는 그대로 두고 FC만 바꾸면 된다"고 생각했지만, 실제로는 freeze 범위에 따라 성능이 크게 달라질 수 있다는 것을 확인했다.
- 모델 비교 실험에서는 아키텍처보다 먼저 학습 조건을 통제해야 한다는 점을 배웠다.
- CIFAR-10과 같이 입력 크기가 작은 데이터셋에서는 ImageNet용 구조를 그대로 사용하는 것보다 입력 크기에 맞게 수정하는 것이 중요했다. ResNet50의 Conv1과 MaxPool을 수정하고, VGG16의 MaxPool 일부를 제거하면서 입력 크기에 맞게 모델 구조를 조정하는 이유를 이해할 수 있었다.

### 어려웠던 점

- ResNet50과 VGG16의 Freeze 범위를 결정하는 과정이 가장 어려웠다.
- CIFAR-10 입력 크기에 맞게 Conv, Pooling 구조를 수정하면서 Feature Map 크기를 계산하는 과정이 쉽지 않았다.

### 보완하고 싶은 점

- ResNet50에서 layer4만 학습한 경우와 layer3+layer4를 학습한 경우를 비교해보고 싶다.
- 전체 Fine-Tuning도 진행하여 부분 Fine-Tuning의 차이를 실험해보고 싶다.
- Bayesian Optimization을 추가해 GridSearch, RandomSearch와 비교해보고 싶다.
- Mini GPT의 데이터 규모와 학습 시간을 늘려 성능을 개선해보고 싶다.

> MiniGPT-KO (한국어 언어모델 사전학습) 회고는 별도 정리: [MiniGPT 회고](https://github.com/100-hours-a-week/KTB4-Kaia-AI/blob/main/weekly-challenge/week-05/MiniGPT.md#8-%ED%9A%8C%EA%B3%A0)
