"""
OIBC 2026 실행용 스크립트
- oibc2026_tester.py 와 같은 폴더에 두고:  python run.py
- 처음에는 아래 STEP 스위치에서 inspect / selftest 만 True 로 두고 단계별로 켜 가며 실행하세요.
- 사전 설치:  pip install -r requirements.txt
"""
import oibc2026_tester as T

# ----------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------
DATA_DIR = "."          # 대회 데이터 폴더 (sites.csv, smp.csv 가 들어 있는 곳)
OUT_DIR = "out"            # 결과 저장 폴더

# 검증에 쓸 (학습 연도, 평가 연도). inspect 출력의 '연도별 행 수'를 보고 실제 있는 연도로 바꾸세요.
YEAR_PAIRS = [(2023, 2024)]

# 실행 단계 스위치 (처음에는 앞의 둘만 True 권장)
RUN_INSPECT = True         # 1) 파일/컬럼/연도별 행 수 확인
RUN_SELFTEST = True        # 2) W 계산 검증
RUN_TESTER = True         # 3) 연도 검증 (오래 걸림)
RUN_SUBMIT = False         # 4) 제출 파일 생성 + 형식 점검 (오래 걸림)

# ----------------------------------------------------------------------
if __name__ == "__main__":
    T.CFG["data_dir"] = DATA_DIR
    T.CFG["out_dir"] = OUT_DIR
    # T.CFG["backend"] = "sklearn"    # LightGBM 오류가 나면 주석 해제 (느리지만 안전)

    if RUN_INSPECT:
        T.inspect()

    if RUN_SELFTEST:
        T.selftest()

    if RUN_TESTER:
        T.year_grid(YEAR_PAIRS, start_month=6)       # 여러 연도 쌍의 요약표 (score_total, score_comp 가 안정적으로 양수인지 확인)

    if RUN_SUBMIT:
        T.make_submission()           # out/composition.csv, forecast.csv, environment.txt 생성 + 자동 형식 점검
