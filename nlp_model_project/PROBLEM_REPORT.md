# 📋 LSTM IMDB Lightning 파일 문제점 전체 리포트

**파일:** `src/lstm_imdb_lightning.py`  
**작성일:** 2026-06-26  
**상태:** ✅ 모든 문제 해결 완료

---

## 🔴 심각 문제 (4개)

### 1️⃣ torchtext.legacy 호환성 문제
**심각도:** 🔴 심각  
**라인:** 14, 52-61  
**문제:**
```python
from torchtext.legacy.data import Field, BucketIterator
from torchtext.legacy.datasets import IMDB
```
- 최신 PyTorch (2.12.0)와 호환되지 않음
- `libtorchtext.pyd` 로드 실패 (WinError 127)
- OSError: [WinError 127] 지정된 프로시저를 찾을 수 없습니다

**원인:**
- torchtext.legacy는 구버전 API로 최신 버전에서 제거됨
- Windows 환경에서 C++ 의존성 문제
- torch 버전과 torchtext 버전 호환성 불일치

**해결 방법:**
- torchtext 완전 제거 (`pip uninstall -y torchtext`)
- 직접 데이터 로딩 방식으로 변경
- 파일 기반 IMDB 데이터 로더 구현

---

### 2️⃣ output_size 설정 오류
**심각도:** 🔴 심각  
**라인:** 179  
**문제:**
```python
def __init__(self, ..., output_size=3):
```
- IMDB 데이터셋은 2개 클래스 (긍정/부정)만 존재
- 라벨 데이터: 0(neg), 1(pos)
- 모델 출력: 3차원
- 크기 불일치로 손실 함수 오류 발생 가능

**원인:**
- 코드 작성 시 일반적인 3분류를 가정
- 실제 IMDB는 2진 분류 태스크

**해결 방법:**
- `output_size=2` 로 고정
- 손실 함수: `CrossEntropyLoss()` (2클래스 지원)
- 메트릭: `task="binary"` 로 변경

---

### 3️⃣ batch.text 인덱싱 오류
**심각도:** 🔴 심각  
**라인:** 264, 294  
**문제:**
```python
x, y = batch.text[0].T, batch.label
```
- torchtext Field의 `include_lengths=True` 설정 시
- `batch.text`는 `(텐서, 길이)` 튜플 반환
- `[0]` 인덱싱 후 `.T` 전치 형태가 잘못됨
- BucketIterator 출력 형태와 불일치

**원인:**
- torchtext.legacy API의 복잡한 배치 형태
- 문서화 부족으로 인한 형태 오해

**해결 방법:**
- Custom Dataset 클래스 구현
- 명확한 배치 형태: (batch_size, seq_len)
- 직접 데이터 처리로 형태 제어

---

### 4️⃣ load_imdb_data 함수 오류
**심각도:** 🔴 심각  
**라인:** 124  
**문제:**
```python
def load_imdb_data(...):
    if not os.path.exists(path):
        return None  # None 반환

# 호출 코드
train_texts, train_labels = load_imdb_data(split='train')
# TypeError: cannot unpack non-iterable NoneType object
```
- 경로 없을 때 `None` 반환
- 호출 코드에서 언팩 시도 → TypeError 발생
- None 체크 전에 언팩 시도

**원인:**
- 반환 타입 불일치 (None vs 튜플)
- 삼항 연산자 우선순위 오류

**해결 방법:**
- 항상 `(texts, labels)` 튜플 반환
- 경로 없을 때: `(None, None)` 반환
- 호출 코드에서 None 체크 후 처리

---

## 🟡 중간 문제 (5개)

### 5️⃣ 잘못된 임베딩 방식
**심각도:** 🟡 중간  
**라인:** 187, 234  
**문제:**
```python
self.embedding = embedding  # 임베딩 벡터 행렬을 직접 저장
x = self.embedding[X]       # 직접 인덱싱
```
- 사전 학습 임베딩을 numpy/tensor로 직접 인덱싱
- nn.Embedding 레이어로 관리되지 않음
- 경사도 계산에 문제 가능성
- 모델 저장/로드 시 호환성 문제

**원인:**
- torchtext의 임베딩 벡터를 직접 사용하려는 의도
- PyTorch best practice 미적용

**해결 방법:**
```python
self.embedding = nn.Embedding(
    vocab_size, 
    embedding_dim, 
    padding_idx=pad_idx
)
```

---

### 6️⃣ 비표준 LSTM 구조
**심각도:** 🟡 중간  
**라인:** 245-251  
**문제:**
```python
x = self.lin(x)           # (batch_size, seq_len, output_dim)
x = x.sum(dim=1)          # 모든 시점 점수 합산
```
- LSTM의 모든 시점 출력에 선형층 적용
- 모든 위치의 점수를 합산하는 비표준 방식
- 일반적 RNN/LSTM 분류에서 사용되지 않음

**원인:**
- 실험적인 아키텍처 설계
- 마지막 hidden state만 사용하는 표준 방식 미인식

**해결 방법:**
```python
_, (hidden, _) = self.lstm(embedded)  # (num_layers, batch_size, hidden_dim)
last_hidden = hidden[-1]               # (batch_size, hidden_dim)
logits = self.fc(last_hidden)          # (batch_size, output_dim)
```

---

### 7️⃣ Accuracy 메트릭 설정 오류
**심각도:** 🟡 중간  
**라인:** 220, 223  
**문제:**
```python
self.train_accuracy = Accuracy(task="multiclass", num_classes=3)
```
- output_size=3 설정과 실제 라벨 2개 불일치
- 메트릭 계산 오류 발생 가능
- output_size 수정 후에도 task 타입이 맞지 않음

**원인:**
- output_size 오류의 연쇄 영향
- task 타입을 multiclass로 고정

**해결 방법:**
```python
self.train_accuracy = Accuracy(task="binary")
self.val_accuracy = Accuracy(task="binary")
```

---

### 8️⃣ devices 파라미터 오류
**심각도:** 🟡 중간  
**라인:** 364-366  
**문제:**
```python
trainer = pl.Trainer(
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1 if torch.cuda.is_available() else None,  # ❌
)
# TypeError: `devices` selected with `CPUAccelerator` should be an int > 0.
```
- CPU 사용 시 `devices=None` 설정 불가
- PyTorch Lightning: CPU는 devices를 정수로 설정해야 함
- GPU가 없으면 devices는 1 이상의 정수여야 함

**원인:**
- PyTorch Lightning API 오해
- CPU에서도 devices 정수 필수

**해결 방법:**
```python
trainer = pl.Trainer(
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1,  # GPU/CPU 모두 1 설정
    max_epochs=num_epochs,
)
```

---

### 9️⃣ requirements.txt 인코딩 문제
**심각도:** 🟡 중간  
**파일:** `requirements.txt`  
**라인:** 1-4  
**문제:**
```
# Python 3.11 기준 패키지 목록
# PyTorch는 설치 환경(CPU/GPU, CUDA 버전)에 따라...
# 우선 PyCharm 터미널에서 아래 파일로 설치를 시도합니다.
# pip install -r requirements.txt
```
- Windows cp949 인코딩과 UTF-8 호환 오류
- `pip install -r requirements.txt` 실패
- UnicodeDecodeError: 'cp949' codec can't decode byte

**원인:**
- 파일이 UTF-8로 저장되었으나 Windows에서 cp949로 읽음
- 한글 주석의 인코딩 충돌

**해결 방법:**
- 한글 주석 제거
- ASCII 호환 영문 주석으로 변경

---

## 📊 문제 심각도 분류

| 심각도 | 개수 | 문제 | 영향 |
|--------|------|------|------|
| 🔴 심각 | 4개 | torchtext.legacy<br>output_size<br>batch.text<br>load_imdb_data | 실행 불가 |
| 🟡 중간 | 5개 | 임베딩 방식<br>LSTM 구조<br>Accuracy<br>devices<br>인코딩 | 실행 오류/부정확 |

---

## ✅ 해결 사항 요약

### 주요 변경사항
1. **torchtext 제거**
   - torchtext.legacy 완전 제거
   - 직접 데이터 로딩 구현
   - 파일 기반 IMDB 로더 작성

2. **데이터 처리 개선**
   - Custom Dataset 클래스 구현
   - 명확한 배치 형태 정의
   - 샘플 데이터 자동 생성 기능

3. **모델 구조 수정**
   - nn.Embedding 레이어 사용
   - 표준 LSTM 구조 적용
   - output_size=2 고정

4. **설정 수정**
   - Accuracy task="binary"
   - devices=1 고정
   - 파라미터 일관성 확보

### 테스트 상태
- ✅ 코드 구문 오류 제거
- ✅ 런타임 오류 모두 해결
- ✅ 호환성 문제 완전 해결
- ✅ 샘플 데이터로 학습 가능

---

## 🚀 실행 방법

```bash
python src/lstm_imdb_lightning.py
```

**IMDB 실제 데이터 사용 (선택사항):**
1. [Stanford AI Lab](http://ai.stanford.edu/~amaas/data/sentiment/) 에서 다운로드
2. `aclImdb/` 폴더에 압축 해제
3. 자동으로 실제 데이터로 학습

**샘플 데이터 자동 사용:**
- IMDB 폴더 없으면 자동 생성
- 긍정/부정 2000개 훈련 데이터
- 500개 테스트 데이터

---

**최종 상태:** 모든 문제 해결 완료 ✅  
**테스트 가능 상태:** YES ✅
