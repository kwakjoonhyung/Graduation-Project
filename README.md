# Graduation-Project

## 초록
일반적인 전처리 기법은 길이가 다른 음성 데이터를 처리하는데 있어 중요 정보의 손실이나 데이터 길이 증가로 인한 계산 복잡성이 증가하는 문제가 있다. 어텐션 메커니즘을 이용하여 음성 데이터 내 중요 부분을 나타내는 어텐션 가중치를 추출한다. 본 연구에서 제안하는 기법인 다이나믹 윈도우 알고리즘을 통해 중요 부분을 포함하는 윈도우의 위치를 찾아 학습에 활용한다. 이를 통해 중요 정보의 손실을 최소화하여 음성 데이터의 학습 효율과 모델의 성능을 높인다.

## 서론
- 음성 데이터는 다양한 길이를 가지는 특성상 일관된 길이를 유지하는 전처리 과정이 필요
- 기존의 전처리 기법은 중요 정보의 손실이나 메모리 효율의 저하 등의 문제 발생
- 본 연구는 어텐션 메커니즘을 활용하여 중요 정보를 데이터셋의 평균 길이로 잘라내고 패딩 과정에서도 중요 정보를 이용하여 패딩하는 중요 패턴 패딩을 도입
- 본 기법은 모델의 성능 향상과 메모리 효율성 개선, 처리 속도 향상에 기여할 것으로 기대
- 이를 통해 기존 전처리 방식의 한계를 극복하고, 음성 데이터 처리의 새로운 패러다임을 제시하는 것이 본 연구의 목표

## 연구 방법
### 1. 데이터
- 데이터셋 명 : 감성 및 발화 스타일별 음성합성 데이터 ( 출처 : [AI hub](https://www.aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=realm&dataSetSn=466) )
- 7가지 대표 감정 (기쁨, 슬픔, 분노, 불안, 상처, 당황, 중립)으로 분류된 음성데이터셋
- 각각의 데이터는 1~7초 사이로 구축
- DW Former 학습, 전처리 기법 평가(TIM Net)를 위해 각 감정 별 랜덤 10,000개씩 총 70,000개 두 세트, 총 140,000개의 데이터를 사용


### 2. 사용모델
① TIM Net (Temporal Information Modeling Network)
   - 음성 데이터에 대한 감정 인식 분야에서 SOTA를 달성하고 있는 딥러닝 모델
   - TIM Net의 성능 비교를 통해 전처리 기법의 평가를 수행
     
② DW Former
   - 어텐션 메커니즘을 이용하여 감정 인식을 수행하는 감정 인식 딥러닝 모델
   - Pre-trained 된 WavLM*의 결과를 음성 데이터의 feature로 사용
   - Pre-train을 시켜 각 음성 데이터에 대한 어텐션 가중치 추출을 수행 


### 3. 전처리 기법
① 기존 전처리 기법
  - 본 연구에서는 TIM Net에서 사용하는 MFCC를 기존 전처리 기법으로 명하여 사용
  - 데이터셋의 평균길이에 맞게 데이터의 중간부분을 자름
- 데이터의 길이가 평균길이보다 짧은 경우 데이터의 앞과 뒤를 0으로 패딩

② 어텐션 기반의 다이나믹 윈도우 기법
   - DW Former를 이용하여 각 음성 데이터의 어텐션 가중치를 추출하여 중요 부분을 파악
   - 어텐션 가중치를 가장 많이 포함하도록 윈도우를 이동한 후, 윈도우에 맞게 데이터를 잘라냄
   - 이 과정은 중요한 정보의 손실을 최소화하면서도 데이터셋의 평균 길이로 일관된 길이를 유지

③ 중요 패턴 패딩 기법
   - 데이터가 데이터셋의 평균 길이에 못 미치는 경우, 길이를 맞추기 위해 패딩을 적용
   - 단순히 0으로 패딩하는 것이 아닌, DW Former를 이용하여 찾아낸 중요 부분의 정보를 	패딩 값에 반영
   - 이를 통해 패딩 된 부분이 원본 데이터의 중요 특성을 유지하게 되어, 패딩이 데이터의 전체 정보에 미치는 영향을 줄이며 더욱 효과적인 학습이 가능해짐

![image](https://github.com/kwakjoonhyung/Graduation-Project/assets/84233813/10bd2527-a46f-4d8b-b14a-5a425910cbc4)

## References
[Temporal Modeling Matters: A Novel Temporal Emotional Modeling Approach for Speech Emotion Recognition](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10096370), Ye, Jiaxin, et al. ICASSP 2023-2023 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). IEEE, 2023.





