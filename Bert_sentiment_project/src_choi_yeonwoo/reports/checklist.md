# 실습문제 진행 체크리스트

> 대상: `Bert_sentiment_project` / 브랜치: `choi_yeonwoo`
> 한국어 감성분석 모델을 `src_choi_yeonwoo/` 패키지로 추가하고 Streamlit 앱에 연결한다.

## 실습문제 원문
1. `Bert_sentiment_project` 를 복제한 다음 본인의 브랜치로 연결함
2. 새 패키지 추가함: `src_브랜치명/` (= `src_choi_yeonwoo/`)
3. 파일 구조는 동일하게 하여, 한국어 감성분석 모델을 적용하여 한국어 리뷰 문장을 입력하면 감성분석 결과가 출력되게 함
4. 본인의 코드를 `app/streamlit_app.py` 에 연결함
   - 영어 리뷰 문장 입력 필드는 그대로 두고 추가함
   - 한국어 리뷰 문장: `input_text` 를 통해 입력받고, '감성분석' 버튼 클릭시 결과 출력되게 함

## 체크리스트

- [x] **1. 복제 + 본인 브랜치 연결**
  - [x] `choi_yeonwoo` 브랜치 생성/체크아웃
  - [x] origin 을 본인 레포(`study-ai-skn/Bert_sentiment_project`)로 연결
  - [x] 부모 레포(`sarastudy1009-svg`)는 `upstream` 으로 보존 (푸시 금지)
- [x] **2. 새 패키지 `src_choi_yeonwoo/` 추가 (구조 동일)**
  - [x] `__init__.py`
  - [x] `config.py`
  - [x] `data_loader.py`
  - [x] `dataset.py`
  - [x] `modeling.py`
  - [x] `predict.py`
  - [x] `train.py`
  - [x] `utils.py`
- [x] **3. 한국어 감성분석 모델 적용**
  - [x] (빠른 경로) 사전학습 NSMC 모델(`monologg/koelectra-base-finetuned-nsmc`) → NSMC 5,000개 정확도 **90.0%**, 커스텀 20/20
  - [x] (느린 경로) NSMC 직접 파인튜닝(풀) → NSMC 5,000개 정확도 **84.3%**, 커스텀 20/20
  - [x] 정량 평가 표본 확대: 6문장 → NSMC 공식 테스트 **5,000개** + 커스텀 20문장
- [x] **4. Streamlit 앱 연결**
  - [x] 영어 리뷰 입력 필드 유지
  - [x] 한국어 리뷰 입력 필드 추가 (`input_text` + '감성분석' 버튼)
  - [x] 버튼 클릭 시 한국어 감성분석 결과 출력
- [x] **5. 결과 리포트**
  - [x] 구현 보고서 (`구현_보고서.md`)
  - [x] 사전학습 모델 리포트 (`report_pretrained_nsmc.md`)
  - [x] 파인튜닝 모델 리포트 (`report_finetuned_nsmc.md`)
- [ ] **6. 본인 레포로 커밋/푸시** (`origin/choi_yeonwoo`)

## 환경 메모
- 프로젝트 전용 `.venv` 생성 + `requirements.txt` 설치 (transformers 4.48.3 / torch 2.5.1 CPU)
- CUDA 미사용(CPU). 파인튜닝은 CPU 시간 제약으로 NSMC 표본(6,000~8,000)을 사용함.
- 리포트는 모두 `src_choi_yeonwoo/reports/` 에 위치.
