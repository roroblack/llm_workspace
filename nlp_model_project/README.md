# nlp_model_project

`nlp_model_project`는 자연어 처리 실습용 PyCharm 프로젝트입니다.  
제공된 두 개의 Python 파일을 포함하며, 각각 CNN 기반 스팸 메일 분류와 LSTM 기반 IMDB 영화 리뷰 감성 분류 실습을 수행합니다.

## 1. 프로젝트 구성

```text
nlp_model_project/
│
├─ src/
│  ├─ __init__.py
│  ├─ cnn_spam_classifier.py
│  └─ lstm_imdb_lightning.py
│
├─ assignment/
│  ├─ LSTM_movie_review.py
│  ├─ ratings_train.txt
│  └─ ratings_test.txt
│
├─ data/
│
├─ models/
│  └─ nsmc_lstm_model.pt
│
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 2. 포함된 Python 파일

### 2.1 `src/cnn_spam_classifier.py`

SMS 스팸 메일 데이터를 사용하여 정상 메일과 스팸 메일을 분류하는 PyTorch CNN 모델입니다.

주요 흐름은 다음과 같습니다.

1. SMS 스팸 데이터셋 다운로드
2. 불필요한 열 제거
3. `ham`, `spam` 라벨을 숫자로 변환
4. 중복 데이터 제거
5. 단어 사전 생성
6. 문장을 정수 시퀀스로 변환
7. 패딩으로 문장 길이 통일
8. `Embedding + Conv1D + GlobalMaxPooling + Linear` 구조의 CNN 모델 학습
9. 테스트 정확도 출력

실행 명령:

```bash
python src/cnn_spam_classifier.py
```

### 2.2 `src/lstm_imdb_lightning.py`

IMDB 영화 리뷰 데이터셋을 사용하여 리뷰가 긍정인지 부정인지 분류하는 LSTM 모델입니다.

주요 흐름은 다음과 같습니다.

1. `torchtext`를 이용한 Field 객체 생성
2. IMDB 데이터셋 로드
3. Vocabulary 생성
4. FastText 임베딩 벡터 사용
5. BucketIterator로 데이터 로더 생성
6. PyTorch Lightning 기반 LSTM 모델 정의
7. Trainer를 이용한 학습 수행

실행 명령:

```bash
python src/lstm_imdb_lightning.py
```

### 2.3 `assignment/LSTM_movie_review.py`

네이버 영화 리뷰(NSMC) 데이터를 사용하여 한글 리뷰의 감성(긍정/부정)을 분류하는 LSTM 모델입니다.  
PyTorch Lightning 기반으로 작성되었으며, `lstm_imdb_lightning.py`를 한글 데이터에 맞게 커스터마이징하였습니다.

실행 명령:

```bash
python assignment/LSTM_movie_review.py
```

---

## 순서도 및 모델 구조

### 전체 파이프라인 순서도

```mermaid
flowchart TD
    A["📂 NSMC 데이터\nratings_train.txt / ratings_test.txt"] --> B["load_data()\n파일 읽기 및 파싱\n형식: id · document · label"]
    B --> C["build_vocab()\n단어 빈도 집계\nmax_vocab=20,000 / min_freq=2"]
    C --> D["NSMCDataset\n정수 인코딩 + 패딩\nmax_len=200"]
    D --> E["random_split()\ntrain 80% / val 20%"]
    E --> F["DataLoader\nbatch_size=64"]
    F --> G["LSTMClassifier 학습\nmax_epochs=3 · Adam lr=0.001"]
    G --> H{"평가 단계"}
    H --> I["Validation\nLoss / Accuracy"]
    H --> J["Test\nLoss / Accuracy"]
    G --> K["모델 저장\nmodels/nsmc_lstm_model.pt"]
    K --> L["predict_sentiment()\n새 문장 감성 예측"]
    L --> M["출력: positive / negative\n+ confidence score"]

    style A fill:#dbeafe
    style M fill:#dcfce7
    style K fill:#fef9c3
```

---

### LSTM 모델 구조

```mermaid
graph TD
    IN["입력: 영화 리뷰 문장"] --> TOK["토크나이징\n한글·영문 공백 분리"]
    TOK --> ENC["정수 인코딩 + 패딩\n시퀀스 길이 200 고정"]
    ENC --> EMB["Embedding Layer\nvocab_size × 128"]
    EMB --> LSTM["LSTM Layer\ninput=128 → hidden=128\nnum_layers=1 · batch_first=True"]
    LSTM --> HID["마지막 Hidden State\nhidden[-1]  ·  shape: (batch, 128)"]
    HID --> DROP["Dropout  p=0.3"]
    DROP --> FC["Linear Layer\n128 → 2"]
    FC --> SOFT["Softmax"]
    SOFT --> OUT["예측 결과\nnegative(0) / positive(1)\n+ confidence"]

    style IN fill:#dbeafe
    style OUT fill:#dcfce7
    style EMB fill:#f3e8ff
    style LSTM fill:#f3e8ff
    style FC fill:#f3e8ff
```

---

### 데이터 전처리 흐름

```mermaid
flowchart LR
    RAW["원문 리뷰\n'이 영화 정말 재미있다!'"] --> CLEAN["clean_korean_text()\nHTML 태그 제거\n한글·영문·숫자만 유지\n공백 정규화"]
    CLEAN --> TOKEN["tokenize()\n공백 기준 분리\n▶ 토큰 리스트"]
    TOKEN --> LOOKUP["vocab 조회\n미등록 단어 → unk(1)"]
    LOOKUP --> PAD["패딩 / 트런케이션\n길이 200으로 맞춤\n짧으면 pad(0) 추가"]
    PAD --> TENSOR["torch.Tensor\nshape: (200,)"]

    style RAW fill:#fef3c7
    style TENSOR fill:#dcfce7
```

---

### 하이퍼파라미터 요약

| 항목 | 값 |
|---|---|
| max_len | 200 |
| max_vocab_size | 20,000 |
| min_freq | 2 |
| batch_size | 64 |
| embedding_dim | 128 |
| hidden_dim | 128 |
| num_layers | 1 |
| dropout | 0.3 |
| learning_rate | 0.001 |
| max_epochs | 3 |
| val_ratio | 0.2 (80/20 분할) |

---

## 3. Python 버전

이 프로젝트는 Python 3.11 기준으로 구성했습니다.

PyCharm에서 인터프리터를 만들 때 다음과 같이 설정합니다.

```text
Python 3.11
```

## 4. 가상환경 생성 방법

PyCharm 터미널 또는 Windows CMD에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```bash
python -m venv .venv
```

Windows에서 가상환경 활성화:

```bash
.venv\Scripts\activate
```

macOS/Linux에서 가상환경 활성화:

```bash
source .venv/bin/activate
```

## 5. 패키지 설치

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 6. PyTorch 설치 참고

GPU를 사용하는 경우 CUDA 버전에 맞는 PyTorch 설치 명령이 필요할 수 있습니다.  
CPU만 사용하는 경우에도 위의 `requirements.txt` 설치로 대부분 실행 가능합니다.

설치 후 PyTorch 인식 여부는 다음 명령으로 확인할 수 있습니다.

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

## 7. 중요 실행 참고사항

### CNN 스팸 분류 코드

`cnn_spam_classifier.py`는 Python 3.11 환경에서 실행하기 비교적 쉽습니다.  
실행 시 인터넷에서 `spam.csv` 파일을 자동으로 다운로드합니다.

### LSTM IMDB 코드

`lstm_imdb_lightning.py`는 원본 실습 코드 구조를 유지하기 위해 `torchtext.legacy` 기반 코드가 포함되어 있습니다.  
하지만 최신 Python 3.11 및 최신 torchtext에서는 `torchtext.legacy`가 제거되어 실행 오류가 발생할 수 있습니다.

따라서 Python 3.11에서 실행할 경우 다음 중 하나를 선택해야 합니다.

1. 코드를 최신 `torchtext` 또는 일반 PyTorch `Dataset/DataLoader` 방식으로 수정한다.
2. 원본 실습 환경과 호환되는 Python/torchtext 구버전 환경을 별도로 사용한다.

수업 실습에서는 먼저 `cnn_spam_classifier.py`를 실행하여 PyTorch 기반 텍스트 분류 전체 흐름을 확인한 뒤,  
`lstm_imdb_lightning.py`는 RNN/LSTM 구조 학습용 코드로 분석하는 방식을 권장합니다.

## 8. GitHub 업로드 순서

프로젝트 폴더에서 아래 명령을 실행합니다.

```bash
git init
git add .
git commit -m "Initial commit: NLP model project"
git branch -M main
git remote add origin https://github.com/사용자계정/nl_model_project.git
git push -u origin main
```

GitHub에서 `nlp_model_project` 이름으로 빈 리포지토리를 먼저 만든 뒤, 위 명령의 주소를 본인 저장소 주소로 바꾸면 됩니다.

## 9. 학습 결과 파일 관리

학습 중 생성되는 모델 파일, 데이터 파일, 캐시 파일은 GitHub에 올리지 않도록 `.gitignore`에 제외 설정했습니다.

대표 제외 대상은 다음과 같습니다.

```text
spam.csv
*.pt
*.pth
*.ckpt
models/
.vector_cache/
.data/
.cache/
```

## 10. 수업 활용 방법

이 프로젝트는 다음 흐름으로 수업에 활용할 수 있습니다.

1. PyCharm 프로젝트 생성
2. GitHub 리포지토리 생성
3. `.gitignore`, `requirements.txt`, `README.md` 역할 설명
4. CNN 텍스트 분류 코드 실행
5. LSTM 코드 구조 분석
6. GitHub에 최초 커밋 및 푸시



