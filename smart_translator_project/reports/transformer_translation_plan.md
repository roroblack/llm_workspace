# Transformer 기반 스마트 번역앱 구현 계획서

작성일: 2026-07-02

## 1. 과제 목표

기존 한국어 <-> 영어 번역 프로젝트의 모델을 문자 단위 Seq2Seq RNN에서 Transformer 기반 번역 모델로 변경한다. Streamlit 앱의 사용 흐름은 유지하되, 학습과 추론 내부 구조를 Transformer encoder-decoder 방식으로 바꾸고 번역 성능을 개선한다.

## 2. 참고 자료

- 참고 폴더: `C:\Users\playdata2\Documents\llm_workspace\from_colab_llm\0702-s`
- 참고 노트북: `Transformer_구현_및_적용_실습.ipynb`
- 확인한 핵심 내용:
  - Self-Attention은 Query, Key, Value를 만들고 `QK^T / sqrt(d_k)` 후 softmax를 적용한다.
  - Transformer Block은 Self-Attention, Residual Connection, Layer Normalization, Feed Forward Network로 구성된다.
  - RNN을 사용하지 않으므로 token embedding에 positional embedding을 더해야 한다.
  - 참고 노트북은 감성분석 분류 모델 예제이므로, 번역 프로젝트에는 encoder-decoder 생성 모델 형태로 확장 적용한다.

## 3. 현재 프로젝트 상태

현재 프로젝트는 `src/`에 학습, 데이터 처리, 모델, 예측 코드가 분리되어 있다.

- `src/data_utils.py`
  - `translation_pairs.csv`의 `en`, `ko` 컬럼을 읽는다.
  - `<EN2KO>`, `<KO2EN>` 방향 토큰을 붙여 하나의 모델이 양방향 번역을 학습한다.
  - 문자 단위 vocab, 인코더 입력, 디코더 입력, 디코더 정답을 만든다.
- `src/model.py`
  - 현재는 LSTM 기반 `Encoder`, `Decoder`, `Seq2Seq` 구조이다.
- `src/train.py`
  - `CrossEntropyLoss(ignore_index=pad_index)`로 학습한다.
  - 모델 가중치와 문자 사전 메타 정보를 `models/`에 저장한다.
- `src/predict.py`
  - 입력 언어를 판별하고 방향 토큰을 붙인 뒤 한 글자씩 greedy decoding한다.
- `app/streamlit_app.py`
  - 모델이 없으면 자동 학습 후 번역 결과를 표시한다.

## 4. 구현 방향

데이터 전처리와 Streamlit 앱 흐름은 최대한 유지하고, 모델과 학습/추론 호출부를 Transformer에 맞게 교체한다.

1. `src/model.py`를 Transformer 번역 모델로 변경한다.
   - token embedding과 positional embedding을 추가한다.
   - encoder-decoder Transformer 구조를 사용한다.
   - source padding mask, target padding mask, target future mask를 생성한다.
   - 출력은 `(batch, target_len, vocab_size)` logits 형태로 유지하여 기존 손실 계산과 맞춘다.

2. `src/config.py`에 Transformer 하이퍼파라미터를 추가한다.
   - `D_MODEL`
   - `NHEAD`
   - `NUM_ENCODER_LAYERS`
   - `NUM_DECODER_LAYERS`
   - `DIM_FEEDFORWARD`
   - `DROPOUT`
   - `MAX_SEQ_LEN`
   - 기존 `EMBED_SIZE`, `HIDDEN_SIZE`는 제거하거나 호환용으로 정리한다.

3. `src/train.py`를 Transformer 학습에 맞게 수정한다.
   - `build_model(...)` 호출 인자를 Transformer 설정으로 변경한다.
   - teacher forcing 방식은 현재의 `decoder_input`, `decoder_target` 구조를 유지한다.
   - optimizer는 Adam 또는 AdamW를 사용한다.
   - gradient clipping을 유지한다.
   - 작은 데이터셋에서 더 잘 외우도록 epoch, learning rate, dropout을 재조정한다.

4. `src/predict.py`의 추론 로직을 Transformer decoding으로 변경한다.
   - LSTM의 `hidden`, `cell` 사용을 제거한다.
   - source 전체를 한 번 넣고, target은 `<SOS>`부터 시작해 누적 생성한다.
   - 매 단계마다 target future mask를 적용해 다음 문자를 greedy 방식으로 선택한다.
   - `<EOS>`가 나오면 생성을 종료한다.

5. `app/streamlit_app.py`는 최소 변경한다.
   - 모델명/설명 문구를 Transformer 기반으로 수정한다.
   - 자동 학습 epoch 수는 Transformer 학습 시간에 맞게 조정한다.

## 5. 성능 개선 전략

작은 실습용 병렬 말뭉치에서는 대형 번역 모델처럼 일반화하기보다, 제공된 예제 문장을 안정적으로 학습하고 양방향 번역 품질을 높이는 것이 현실적인 목표다.

- 방향 토큰 유지
  - 한 모델에서 영어->한국어, 한국어->영어를 모두 처리한다.
- positional embedding 추가
  - RNN 없이도 문자 순서를 학습할 수 있게 한다.
- mask 처리 강화
  - PAD 위치는 attention과 loss에서 제외한다.
  - decoder는 미래 토큰을 보지 못하도록 causal mask를 적용한다.
- 학습 안정화
  - `CrossEntropyLoss(ignore_index=pad_index)` 유지
  - gradient clipping 유지
  - learning rate를 Transformer에 맞게 낮춘다.
  - dropout을 너무 크게 두지 않아 작은 데이터에서 과소학습을 피한다.
- 저장 메타 확장
  - vocab과 함께 Transformer 구조 설정을 저장하여 재실행 시 같은 구조로 로드한다.
- 샘플 검증
  - `hello`, `thank you`, `i am a student`, `안녕하세요`, `감사합니다`, `나는 학생입니다` 같은 기존 예시를 학습 후 확인한다.

## 6. 파일별 작업 목록

| 파일 | 작업 내용 |
| --- | --- |
| `src/config.py` | Transformer 하이퍼파라미터 추가, 기존 RNN 설정 정리 |
| `src/model.py` | LSTM Seq2Seq를 Transformer encoder-decoder 모델로 교체 |
| `src/train.py` | 모델 생성 인자와 저장 메타를 Transformer 기준으로 수정 |
| `src/predict.py` | hidden/cell 기반 추론을 autoregressive Transformer decoding으로 변경 |
| `app/streamlit_app.py` | 화면 문구와 자동 학습 epoch 조정 |
| `README.md` | Seq2Seq 설명을 Transformer 설명으로 갱신 |

## 7. 검증 계획

1. 정적 확인
   - `python -m py_compile src/config.py src/data_utils.py src/model.py src/train.py src/predict.py app/streamlit_app.py`

2. 짧은 학습 실행
   - `python -m src.train`
   - 학습 완료 후 `models/smart_translator.pt`, `models/translator_meta.pt` 생성 확인

3. 예측 함수 확인
   - `python -m src.predict`
   - 영어 입력과 한국어 입력이 모두 반대 언어로 출력되는지 확인

4. Streamlit 앱 확인
   - `streamlit run app/streamlit_app.py`
   - 브라우저에서 번역 버튼 동작 확인

## 8. 예상 결과물

- Transformer 기반 번역 모델 코드
- 기존 Streamlit 번역 앱에서 그대로 사용할 수 있는 학습/예측 흐름
- Transformer 구조와 실행 방법이 반영된 README
- 모델 교체 후 학습 및 샘플 번역 검증 결과

## 9. 다음 단계

이 계획서 작성 후 실제 구현은 다음 순서로 진행한다.

1. Transformer 모델 코드 작성
2. 학습 코드와 메타 저장 형식 수정
3. 추론 코드 수정
4. 앱 문구와 README 갱신
5. 학습 및 샘플 번역 검증
