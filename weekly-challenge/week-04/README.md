# ML/DL 기초 구현

> 위클리챌린지 4주차 - 데이터 전처리부터 CNN까지, ML/DL의 전체 흐름을 직접 구현

**위클리챌린지:** [weekly_challenge.ipynb](./weekly_challenge.ipynb)  \
**학습 TIL:** [week-04-TIL](https://github.com/100-hours-a-week/KTB4-Kaia-AI/blob/main/TIL/week-04.md)

---

## 전체 흐름

```
[원시 데이터]
    ↓ 전처리 (결측값 / 정규화 / 인코딩)
    ↓ 증강 (회전 / 반전)
    ↓ 분할 (Train / Validation / Test)
[전통적 ML]
    KNN → SVM → Random Forest → Naive Bayes
    ↓ (고차원, 비선형 데이터에서 한계)
[딥러닝]
    퍼셉트론 → MLP → CNN
    ↓
[결과] MLP 51.92% → CNN 74.71% (+22.79%p)
```

---

## 요약

세부 코드와 출력은 노트북에서 확인. 여기서는 무엇을 구현했고 무엇을 알게 됐는지만 정리.

### Data Preprocessing
- 결측치 처리
- 정규화
- 인코딩
- Train / Validation / Test 분할

### Traditional ML
- KNN Classification
- KNN Regression
- Perceptron (직접 구현)
- SVM
- Random Forest
- Naive Bayes

### Deep Learning
- Activation Function 시각화
- MLP 구현
- CNN 구현

### Additional Experiments
- Data Augmentation 적용
- Epoch(5, 10, 15)별 성능 비교
- 증강 이미지 시각화 및 검증

---

## 주요 결과

| Model | Accuracy |
|---------|---------:|
| Perceptron | 0.82 |
| SVM | 0.87 |
| Random Forest | 0.91 |
| Naive Bayes | 0.90 |

### CIFAR-10

| Model | Basic | Augmented |
|---------|---------:|---------:|
| MLP | 51.92% | 50.82% |
| CNN | 74.71% | 73.95% |

### Additional Experiment(CIFAR-10): Epoch Comparison

데이터 증강 효과를 추가로 검증하기 위해 Epoch 수를 늘려가며 실험을 진행하였다.

| Epoch | MLP Base | MLP Aug | CNN Base | CNN Aug |
|---------|---------:|---------:|---------:|---------:|
| 5 | 51.74 | 50.83 | 74.73 | 75.19 |
| 10 | 53.94 | 51.30 | 75.30 | 78.21 |
| 15 | 53.54 | 52.83 | 75.83 | 79.28 |

---

## 회고

#### 배운 점

- 역전파는 가중치를 수정하는 과정이 아니라 Gradient를 계산하는 과정이며, 실제 파라미터 업데이트는 Optimizer가 수행한다는 점을 직접 구현하며 이해할 수 있었다.
- MLP와 CNN을 동일한 데이터셋에서 비교하며, CNN이 공간 정보를 유지하며 특징을 추출하기 때문에 더 높은 성능을 보인다는 점을 확인했다.
- 데이터 증강은 항상 성능 향상을 보장하지 않으며, 학습 시간(Epoch)과 같은 조건에 따라 효과가 달라질 수 있다는 점을 실험으로 확인했다.
- 예상과 다른 결과가 나왔을 때 구현 오류를 단정하기보다 가설을 세우고 검증하는 과정의 중요성을 배웠다.

#### 어려웠던 점

- 데이터 증강 적용 후 성능이 오히려 감소하여 원인 분석이 필요했다. 증강 이미지를 직접 확인하고 Epoch를 늘려가며 추가 실험한 결과, 짧은 학습 환경에서는 증가한 데이터 다양성을 충분히 학습하지 못할 수 있음을 확인했다.
- CNN 모델을 설계하면서 Convolution, Pooling 이후 Feature Map 크기 변화와 차원 계산을 이해하는 과정이 어려웠다.

#### 보완하고 싶은 점

- SGD, Momentum, RMSProp, Adam 등 다양한 Optimizer를 적용하여 학습 속도와 성능 차이를 비교해보고 싶다.
- Loss Curve와 Feature Map 시각화를 추가하여 모델의 학습 과정과 특징 추출 과정을 더 깊게 분석해보고 싶다.