# README 검증 체크리스트

README.md의 3~8절 서술을 실제 소스 코드와 하나씩 대조한 결과입니다.
검증일 기준 코드: `src/config.py`, `src/data_utils.py`, `src/model.py`, `src/train.py`, `src/predict.py`, `app/streamlit_app.py`

- ✅ 코드와 일치
- ⚠️ 코드와 불일치 / 과장 (수정 필요)

---

## 3. 동작 방식

- [x] ✅ 하나의 모델로 영어→한국어 + 한국어→영어 양방향 학습
  → `data_utils.load_translation_pairs`가 `("<EN2KO> "+en, ko)`와 `("<KO2EN> "+ko, en)` 두 쌍을 모두 생성
- [x] ✅ 영어 입력에 `<EN2KO>`를 붙여 한국어를 정답으로 학습
  → `pairs.append(("<EN2KO> " + row["en"], row["ko"]))`
- [x] ✅ 한국어 입력에 `<KO2EN>`를 붙여 영어를 정답으로 학습
  → `pairs.append(("<KO2EN> " + row["ko"], row["en"]))`
- [x] ✅ 문자 단위 Seq2Seq (글자를 정수 인덱스로 처리)
  → `build_vocab`이 `charset.update(list(source))`로 글자 단위 사전 구성
- [x] ✅ 한글·영어를 하나의 문자 사전으로 처리
  → `build_vocab`이 입력·출력 문장 모두에서 단일 `char2idx` 생성 (인코더/디코더 공유)
- [x] ✅ 특수 토큰 `<PAD>` / `<SOS>` / `<EOS>` / `<UNK>`
  → `config.py`에 정의, `collate_batch` 패딩(0=PAD), `TranslationDataset`에서 SOS/EOS 사용, `encode_text`에서 UNK 처리
- [x] ✅ 한글 포함 시 한국어→영어, 아니면 영어→한국어 자동 판별
  → `predict.detect_language`가 한글 정규식 `[가-힣㄰-㆏]`으로 판별

## 4. 모델 학습

- [x] ✅ `python -m src.train` 실행 가능
  → `train.py` 하단 `if __name__ == "__main__": train_model()`
- [x] ✅ `models/smart_translator.pt` = 학습된 모델 가중치
  → `torch.save(model.state_dict(), MODEL_PATH)`
- [ ] ⚠️ `models/translator_meta.pt` 설명 중 **"문장 최대 길이"** 는 실제로 저장되지 않음
  → 메타 dict에 저장되는 키: `char2idx`, `idx2char`, `vocab_size`, `embed_size`, `hidden_size`, `pad_index`
  → `max_src_len` / `max_tar_len` 같은 최대 길이 값은 저장 안 함 (패딩은 배치마다 `collate_batch`가 동적으로 처리)
  → **수정 제안:** "문장 최대 길이" 문구 삭제 또는 "문자 사전, 모델 구성값(vocab/embed/hidden), PAD 인덱스"로 교체
- [x] ✅ 메타 파일에 문자 사전(`char2idx`, `idx2char`) 함께 저장
  → 위 메타 dict에 포함

### 하이퍼파라미터 표 (config.py 대조)

- [x] ✅ `EMBED_SIZE` = 64
- [x] ✅ `HIDDEN_SIZE` = 128
- [x] ✅ `EPOCHS` = 700
- [x] ✅ `BATCH_SIZE` = 16
- [x] ✅ `LEARNING_RATE` = 0.003
- [x] ✅ `MAX_OUTPUT_LEN` = 60

## 5. Streamlit 실행

- [x] ✅ `streamlit run app/streamlit_app.py`
- [x] ✅ `번역` 버튼으로 결과 출력
  → `st.button("번역", type="primary")`
- [x] ✅ 모델 파일 없으면 첫 실행 시 자동 학습
  → `cached_load_or_train_model`이 `MODEL_PATH`/`META_PATH` 부재 시 `train_model(epochs=500)` 호출
  → 참고: 자동 학습 에폭은 500이므로 "짧은 학습"이라는 표현은 다소 느슨함 (오류는 아님)
- [x] ✅ `@st.cache_resource`로 캐싱
  → `cached_load_or_train_model`에 데코레이터 적용

## 6. 사용 예시

- [x] ✅ 영어 예시 4개 모두 데이터에 존재
  → `hello`, `thank you`, `i am a student`, `what are you doing` 모두 `translation_pairs.csv`에 있음
- [x] ✅ 한국어 예시 4개 모두 데이터에 존재
  → `안녕하세요`, `감사합니다`, `나는 학생입니다`, `무엇을 하고 있나요` 모두 있음

## 7. 코드 구성 핵심

- [x] ✅ `src/config.py`: 경로, 하이퍼파라미터, 특수 토큰 관리
- [x] ✅ `src/data_utils.py`: 양방향 학습 쌍, 문자 사전 생성, 정수 인코딩, `TranslationDataset`, `collate_batch`
- [x] ✅ `src/model.py`: `Encoder`, `Decoder`, `Seq2Seq` 정의
- [ ] ⚠️ `src/train.py` 설명 중 **"학습·평가"** 의 "평가"는 코드에 없음
  → `train.py`에는 검증 데이터 분리, `evaluate` 함수, `val_loader`가 없음. 학습(train)만 수행하고 저장함
  → **수정 제안:** "데이터를 불러와 모델을 학습하고, 모델 가중치와 사전 메타 정보를 저장합니다." (평가 문구 삭제)
    또는 train.py에 검증 분리 + 평가 루프를 추가하여 README에 맞추기
- [x] ✅ `src/predict.py`: `detect_language`, `load_model`, `translate`
- [x] ✅ `app/streamlit_app.py`: 입력·결과 확인 화면

## 8. 참고

- [x] ✅ "문자 단위 Seq2Seq 모델" 서술 정확
- [x] ✅ 품질 향상 방향(더 많은 말뭉치, Transformer, SentencePiece, BLEU/chrF) 안내 — 일반 서술로 문제 없음

---

## 요약

| 구분 | 개수 |
| --- | --- |
| ✅ 일치 | 대부분 (약 26항목) |
| ⚠️ 불일치 | 2항목 |

### ⚠️ 조치가 필요한 2가지

1. **4절 – 메타 파일 "문장 최대 길이"**: 실제 저장 안 됨. 문구 삭제 또는 실제 저장 키로 교체 필요.
2. **7절 – train.py "학습·평가"**: 평가(검증) 로직 없음. 문구를 "학습·저장"으로 고치거나, train.py에 검증 루프 추가.

두 항목 모두 **README 문구를 코드에 맞춰 수정**하는 것이 가장 간단합니다.
반대로 노트북 원본처럼 기능을 채우려면, train.py에 (a) 메타에 최대 길이 저장, (b) train/val 분리 + `evaluate` 추가를 구현하면 됩니다.
