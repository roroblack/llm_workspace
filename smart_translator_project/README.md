# Torch 기반 Transformer 스마트 번역기 Streamlit 프로젝트

문자 단위 Seq2Seq RNN 모델을 Transformer encoder-decoder 모델로 교체한 한국어 <-> 영어 양방향 번역 앱입니다.
Streamlit 화면에서 문장을 입력하면 입력 언어를 자동 판별하고 반대 언어 번역 결과를 출력합니다.

핵심 흐름은 다음과 같습니다.

- 번역 데이터 구축
- 문자 사전 생성
- `<EN2KO>`, `<KO2EN>` 방향 토큰을 이용한 양방향 학습 데이터 구성
- Transformer encoder-decoder 모델 구현
- positional embedding, padding mask, future mask 적용
- 손실 함수와 옵티마이저를 이용한 지도 학습
- CSV에 정확히 있는 문장은 translation memory로 우선 반환하여 앱 번역 품질 보강
- 학습된 모델로 새 문장 번역

## 1. 프로젝트 구조
```text
smart_translator_project/
├─ app/
│  └─ streamlit_app.py          # 번역 화면 실행 파일
├─ data/
│  └─ translation_pairs.csv     # en, ko 두 컬럼으로 구성된 영어-한국어 예제 데이터
├─ models/                      # 학습된 모델(.pt)과 메타 정보가 저장되는 폴더
├─ reports/
│  └─ transformer_translation_plan.md
├─ src/
│  ├─ config.py                 # 경로, Transformer 하이퍼파라미터, 특수 토큰 설정
│  ├─ data_utils.py             # 데이터 로딩, 문자 사전 생성, Dataset/패딩 구성
│  ├─ model.py                  # Transformer 번역 모델 정의
│  ├─ predict.py                # 언어 판별, 모델 로딩, 문장 번역 함수
│  └─ train.py                  # 학습, 모델·사전 저장 실행 스크립트
├─ README.md
└─ requirements.txt
```

## 2. 설치
```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

주요 패키지는 `torch`, `streamlit`, `pandas`, `numpy`, `scikit-learn`입니다.

## 3. 동작 방식
이 프로젝트는 하나의 Transformer 모델로 **영어->한국어**와 **한국어->영어**를 모두 학습합니다.

- 학습 데이터를 읽을 때 각 문장 앞에 방향 토큰을 붙입니다.
  - 영어 입력에는 `<EN2KO>`를 붙여 한국어를 정답으로 학습합니다.
  - 한국어 입력에는 `<KO2EN>`를 붙여 영어를 정답으로 학습합니다.
- 모델은 문자 단위 Transformer 구조입니다.
  - token embedding에 positional embedding을 더해 문자 순서를 반영합니다.
  - padding mask로 `<PAD>` 위치를 attention에서 제외합니다.
  - future mask로 디코더가 미래 정답 문자를 미리 보지 못하게 합니다.
- 특수 토큰은 `<PAD>`, `<SOS>`, `<EOS>`, `<UNK>`입니다.
- 번역 시에는 입력 문장에 한글이 포함되어 있으면 한국어->영어, 그렇지 않으면 영어->한국어로 자동 판별합니다.
- CSV에 정확히 있는 문장은 먼저 정답 번역을 반환하고, 그 외 문장은 Transformer가 autoregressive 방식으로 생성합니다.

## 4. 모델 학습
```bash
python -m src.train
```

학습이 완료되면 다음 파일이 생성됩니다.
```text
models/smart_translator.pt      # 학습된 Transformer 모델 가중치
models/translator_meta.pt       # 문자 사전, 모델 구조, 하이퍼파라미터 등 메타 정보
```

주요 설정값은 `src/config.py`에서 조절합니다.

| 설정값 | 의미 | 기본값 |
| --- | --- | --- |
| `D_MODEL` | Transformer 내부 표현 차원 | 96 |
| `NHEAD` | Multi-Head Attention head 수 | 4 |
| `NUM_ENCODER_LAYERS` | Encoder layer 수 | 2 |
| `NUM_DECODER_LAYERS` | Decoder layer 수 | 2 |
| `DIM_FEEDFORWARD` | Feed Forward Network 차원 | 192 |
| `DROPOUT` | Dropout 비율 | 0.05 |
| `MAX_SEQ_LEN` | positional embedding 최대 길이 | 128 |
| `EPOCHS` | 학습 반복 횟수 | 500 |
| `BATCH_SIZE` | 미니배치 크기 | 32 |
| `LEARNING_RATE` | 학습률 | 0.0015 |
| `MAX_OUTPUT_LEN` | 번역 결과 최대 문자 수 | 80 |

## 5. Streamlit 실행
```bash
streamlit run app/streamlit_app.py
```

- 브라우저 화면에서 문장을 입력한 뒤 `번역` 버튼을 누르면 번역 결과가 출력됩니다.
- 모델 파일이 없거나 기존 Seq2Seq RNN 체크포인트가 남아 있으면 첫 실행 시 Transformer 모델을 자동 학습합니다.
- 품질과 실행 속도를 위해서는 `python -m src.train`으로 미리 학습해 두는 것이 좋습니다.
- 모델은 `@st.cache_resource`로 캐싱되어 재실행 때마다 다시 로딩되지 않습니다.

## 6. 사용 예시
영어 입력:
```text
hello
thank you
i am a student
what are you doing
```

한국어 입력:
```text
안녕하세요
감사합니다
나는 학생입니다
무엇을 하고 있나요
```

## 7. 코드 구성 핵심
- `src/config.py`: 데이터·모델 경로, Transformer 하이퍼파라미터, 특수 토큰을 관리합니다.
- `src/data_utils.py`: CSV를 읽어 양방향 학습 쌍을 만들고, 문자 사전과 패딩 배치를 구성합니다.
- `src/model.py`: positional embedding과 mask를 포함한 Transformer 번역 모델을 정의합니다.
- `src/train.py`: 모델을 학습하고 가중치와 메타 정보를 저장합니다.
- `src/predict.py`: 언어 자동 판별, 체크포인트 호환성 확인, 모델 로딩, 번역 생성을 담당합니다.
- `app/streamlit_app.py`: 사용자가 문장을 입력하고 번역 결과를 확인하는 화면입니다.

## 8. 실습 과제 반영

- 기존 모델: 문자 단위 Seq2Seq RNN
- 변경 모델: 문자 단위 Transformer encoder-decoder
- 성능 개선:
  - 방향 토큰 유지로 하나의 모델에서 양방향 번역
  - positional embedding, padding mask, future mask 적용
  - 작은 데이터셋에 맞춘 경량 Transformer 설정
  - 정확히 학습 데이터에 있는 문장은 translation memory로 보강
