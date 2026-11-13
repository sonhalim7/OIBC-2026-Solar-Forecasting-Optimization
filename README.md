# ⚡ OIBC 2026: 태양광 집합자원 구성 최적화 및 하루 전 발전량 예측 파이프라인

> **제6회 POSTECH·KAIST·UNIST AI & 데이터사이언스 경진대회 (DataEn / OIBC-2026)**  
> **정산금 페널티(W) 최소화를 위한 가중 L1 발전량 예측, 가중중앙값 편향 보정 및 시뮬레이티드 어닐링(SA) 기반 253개 발전소 집합자원 최적 분해 시스템**

![Python](https://shields.io)
![LightGBM](https://shields.io)
![Pandas](https://shields.io)
![NumPy](https://shields.io)

---

## 📌 1. 프로젝트 개요

전력중개시장(VPP) 환경에서 소규모 태양광 발전소 253개소를 2개의 집합자원(`G1`, `G2`)으로 구성하고, 하루 전(전날 17:00 기준) 시간대별 집합 발전량을 예측하여 **예측 오차 페널티(W)를 최소화**하는 End-to-End ML & 최적화 파이프라인입니다.

* **핵심 목적함수 (W 최소화):**
  \[W = \sum_{t} \text{SMP}_t \cdot k_t \cdot \left\vert{} \hat{Y}(g, t) - A(g, t) \right\vert{}\]
  * 피크 시간대(라벨 기준 11~15시) 가중치 \(k_t = 3\), 그 외 시간대 \(k_t = 1\) 적용
  * 동일 집합 내 발전소 간 반대 부호 오차는 상쇄되나, 집합(`G1`, `G2`) 간 오차는 상쇄되지 않는 구조 반영
  * 각 집합별 최소 설비용량 제약 조건(≥ 20,000 kW) 준수

---

## 🛠️ 2. 기술 스택 (Tech Stack)

* **Language:** Python 3.11.4
* **Machine Learning:** LightGBM 4.6.0 (`deterministic=True`), Scikit-learn 1.9.1
* **Data Processing & Optimization:** NumPy 2.4.6, Pandas 3.0.6, PyArrow 26.0.0
* **Optimization Algorithm:** Simulated Annealing (Swap & Move 기반 조합 최적화)

---

## 📂 3. 저장소 구조 (Repository Structure)

```text
my_git_lab/ (OIBC-2026)
├── oibc2026_tester.py           # 기본 W 채점 테스터 및 제출 검증 파이프라인
├── oibc2026_tester - 찐.py     # 인과적 이용률(causal site_cf), 편향 보정, 페널티 분해 진단 포함 고도화 엔진
├── run.py                       # 실험 스위칭, 하이퍼파라미터 탐색 및 다중 후보(Variants) 생성 실행 스크립트
└── README.md                    # 프로젝트 아키텍처 및 핵심 알고리즘 문서
```

---

## ⚙️ 4. 핵심 아키텍처 및 알고리즘 (Key Engineering)

### ① 도메인 물리량 및 기상 예보 피처 엔지니어링 (`solar_features`, `fc_features`)
* **천문학적 태양 위치 계산:** 외부 데이터 없이 위·경도 및 KST 시각(우측닫힘 구간 중앙)으로부터 태양 천정각 여현(`cosz`), 대기권 외 일사량(`etr`), 시간각(`ha`), 계절 주기(`doy_sin/cos`)를 수식으로 직접 산출
* **이종 기상 예보 통합:** 두 기상 제공사(`A`, `B`)의 단위계 차이를 보존하기 위해 분리 처리하고, 예보 발행 라운드(10시·17시) 간 **평균(`_avg`)**과 **예보 변동성(`_d`)** 피처를 생성

### ② 목적함수 정렬 LightGBM 예측 및 가중중앙값 편향 보정 (`fit_predict`, `fit_bias_scale`)
* **페널티 가중 L1 회귀:** 발전소별 이용률($\text{CF} = \text{Generation} / \text{Capacity}$)을 타깃으로 설정하고, 학습 샘플 가중치로 $\text{SMP} \cdot k$를 부여하여 고단가·피크 시간대 예측 정밀도 극대화
* **닫힌 형태(Closed-form) 편향 보정:** 학습 구간 OOF 예측에서 발생하는 시간대별 과대·과소 치우침을 보정하기 위해 $\sum w \cdot |c \cdot P - A|$를 최소화하는 **가중중앙값(Weighted Median)** 기반 피크/비피크 곱셈 보정 계수 적용

### ③ 시뮬레이티드 어닐링(SA) 기반 집합자원 구성 최적화 (`optimize_groups`)
* **OOF 오차 행렬 기반 상쇄 극대화:** 학습 구간의 주(Week) 블록 교차검증(OOF) 오차 행렬 $E \in \mathbb{R}^{253 \times T}$을 구축하여, 같은 집합 내에서 양(+)의 오차와 음(-)의 오차가 서로 상쇄되도록 발전소 배정 최적화
* **제약 조건 보장 탐색:** 반복(200,000 iters) 과정에서 `Swap(70%)` 및 `Move(30%)` 연산을 수행하며 두 집합 모두 설비용량 $20,000\text{ kW}$ 이상 제약을 실시간 검증

### ④ 엄격한 데이터 누수(Data Leakage) 차단 및 인과성 보장
* **인과적 이용률 계산 (`_causal_site_cf`):** 미래 실적 참조를 원천 차단하기 위해 각 대상일 $D$의 예측 시점(전날 17:00) 이전에 확정된 발전 실적만 누적 합산(`merge_asof`)하여 발전소별 평균 이용률 산출
* **엄격한 학습/평가 분리:** 결측 대체 중앙값(`med`)은 학습 구간에서만 산출해 전달하고, 예보 결측 보간은 과거 방향(`ffill(limit=6)`)만 허용하며, 평가 프레임에는 SMP 정보를 배제

### ⑤ 다각도 오차 진단 및 무결성 검증 프레임워크 (`run.py`)
* **페널티 분해 및 진단 모듈:** 월별·시각별·가중치 구간별 페널티 쏠림(`penalty_breakdown`), 구름 예보 수준별 편향(`cloud_bin_check`), 기상 예보 결손 노출도(`missing_forecast_report`) 분석 기능 내장
* **제출 무효 방지 자동 점검 (`check_submission`):** 발전소 누락/중복, 그룹 배정, 최소 용량($20\text{MW}$) 미달, 타임존 표기(KST), 결측·음수 여부 등 6가지 무효 조건을 자동 검증

---

## 🚀 5. 실행 방법 (Quick Start)

```bash
# 1. 데이터 스키마 및 연도별 행 수 점검
python oibc2026_tester.py inspect --data-dir data

# 2. 목적함수(W) 및 집합 간 상쇄 규칙 단위 테스트
python oibc2026_tester.py selftest

# 3. 시계열 시즌(6월~익년 5월) 교차 검증 및 진단 실행
python run.py

# 4. 최종 제출 파일(composition.csv, forecast.csv) 생성 및 6대 무효 조건 점검
python oibc2026_tester.py submit --data-dir data
```
