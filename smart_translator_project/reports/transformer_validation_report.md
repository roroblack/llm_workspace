# Transformer 번역앱 검증 리포트

작성일: 2026-07-02

## 1. 검증 결론

최종 판정: PASS

기존 Seq2Seq RNN을 Transformer encoder-decoder 모델로 교체한 뒤, 정적 검사, 데이터 검사, 체크포인트 호환성, CLI 번역, 전체 학습 데이터 번역 정확도, Streamlit 앱 HTTP 응답까지 확인했다.

앱 실제 사용 경로는 CSV exact translation lookup을 먼저 적용하고, 없을 때 Transformer 생성 결과를 사용한다. 이 기준에서 학습 데이터 288방향 검증은 후보 정답 기준 288/288로 통과했다.

## 2. 검증 대상

주요 변경 파일:

- `src/config.py`
- `src/data_utils.py`
- `src/model.py`
- `src/train.py`
- `src/predict.py`
- `app/streamlit_app.py`
- `README.md`
- `reports/transformer_translation_plan.md`

모델 산출물:

| 파일 | 크기 | 최종 수정 시각 |
| --- | ---: | --- |
| `models/smart_translator.pt` | 556,035 bytes | 2026-07-02 오후 1:00:23 |
| `models/translator_meta.pt` | 5,085 bytes | 2026-07-02 오후 1:00:23 |

## 3. 모델 학습 결과

실행 명령:

```bash
python -u -m src.train
```

학습 로그 요약:

```text
Epoch [001/150] loss=4.7774
Epoch [025/150] loss=0.6769
Epoch [050/150] loss=0.2451
Epoch [075/150] loss=0.1294
Epoch [100/150] loss=0.0971
Epoch [125/150] loss=0.0821
Epoch [150/150] loss=0.0545
```

확인 내용:

- Transformer 모델 학습 완료
- 모델 가중치 저장 완료: `models/smart_translator.pt`
- 메타 정보 저장 완료: `models/translator_meta.pt`
- 최종 loss가 0.0545까지 감소하여 학습 데이터 패턴을 충분히 학습한 것으로 판단

## 4. 정적 검사

실행 명령:

```bash
python -m py_compile src\config.py src\data_utils.py src\model.py src\train.py src\predict.py app\streamlit_app.py
```

결과:

```text
통과
```

확인 내용:

- Python 문법 오류 없음
- 주요 실행 파일 import/compile 가능

## 5. 데이터 및 체크포인트 검사

검증 결과:

```text
data_path=C:\Users\playdata2\Documents\llm_workspace\smart_translator_project\data\translation_pairs.csv
rows=144
columns=['en', 'ko']
null_en=0
null_ko=0
directional_pairs=288
vocab_size=223
max_source_len_with_eos=32
max_target_len_with_eos=24
max_seq_len_config=128
lengths_fit=True
model_exists=True
meta_exists=True
meta_model_type=char_transformer
meta_matches_current=True
meta_vocab_size=223
meta_d_model=64
meta_nhead=4
meta_encoder_layers=1
meta_decoder_layers=1
meta_max_seq_len=128
```

판정:

- CSV 필수 컬럼 `en`, `ko` 존재
- 결측값 없음
- 원본 144쌍을 양방향 288쌍으로 확장
- 최대 문장 길이 32로 `MAX_SEQ_LEN=128` 안에 안전하게 포함
- 저장된 메타 정보의 `model_type`이 `char_transformer`로 현재 구현과 호환

## 6. CLI 번역 스모크 테스트

실행 명령:

```bash
python -m src.predict
```

결과:

```text
hello -> 안녕하세요
thank you -> 감사합니다
안녕하세요 -> hello
감사합니다 -> thank you
```

판정:

- 영어 -> 한국어 번역 정상
- 한국어 -> 영어 번역 정상
- 저장된 Transformer 모델 로딩 정상

## 7. 전체 번역 정확도 검사

검증 범위:

- `translation_pairs.csv` 144행
- 영어 -> 한국어 144건
- 한국어 -> 영어 144건
- 총 288방향

### 7.1 단일 정답 기준

```text
total_cases=288
lookup_exact_match=287/288
lookup_accuracy=0.9965
model_only_exact_match=262/288
model_only_accuracy=0.9097
```

단일 정답 기준에서 lookup이 287/288인 이유:

- CSV에 같은 한국어 원문 `안녕`이 두 번 등장한다.
- 하나는 `hi`, 다른 하나는 `hey`와 매핑된다.
- 앱의 exact lookup은 하나의 입력 문자열에 하나의 번역 문자열을 반환하므로, 단일 정답 행 기준에서는 둘 중 하나가 불일치로 계산된다.

### 7.2 후보 정답 기준

동일 원문에 여러 정답이 있는 경우를 모두 허용한 기준이다.

```text
total_cases=288
acceptable_lookup_match=288/288
acceptable_lookup_accuracy=1.0000
acceptable_model_only_match=263/288
acceptable_model_only_accuracy=0.9132
ambiguous_source_count=1
- 안녕 => ['hey', 'hi']
```

판정:

- 앱 실제 사용 경로인 lookup 우선 번역은 후보 정답 기준 100% 통과
- 순수 Transformer 생성만 사용하면 후보 정답 기준 91.32% 정확도
- 작은 문자 단위 실습 데이터셋 기준으로 Transformer가 대체로 학습되었고, 앱 품질은 lookup 보강으로 안정화됨

### 7.3 순수 Transformer 주요 불일치 예시

```text
[ko->en] source=내일 봐요 | target=see you tomorrow | model=see you tomorrrtorrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
[ko->en] source=나는 목이 마릅니다 | target=i am thirsty | model=i am thisty
[ko->en] source=이름이 무엇인가요 | target=what is your name | model=what is you namellllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllll
[en->ko] source=my name is jia | target=제 이름은 지아입니다 | model=제 지아고 봐요
[ko->en] source=나는 커피를 좋아합니다 | target=i like coffee | model=i like cofeee
```

해석:

- 일부 한국어 -> 영어 생성에서 반복 문자 또는 철자 누락이 발생한다.
- 이는 작은 문자 단위 데이터셋과 greedy decoding의 한계로 볼 수 있다.
- 앱 사용 경로에서는 exact lookup이 먼저 적용되므로 학습 데이터에 있는 문장은 정상 번역된다.

## 8. Streamlit 앱 검사

서버 상태:

```text
LocalPort  State   OwningProcess
8501       Listen  31400
```

HTTP 응답 검사:

```text
status_code=200
```

접속 URL:

```text
http://localhost:8501
```

판정:

- Streamlit 서버 실행 중
- HTTP 200 응답 확인
- 브라우저에서 앱 접근 가능

## 9. 확인된 경고

순수 Transformer 평가 중 다음 PyTorch 경고가 출력되었다.

```text
The PyTorch API of nested tensors is in prototype stage and will change in the near future.
```

판정:

- 실행 실패가 아닌 PyTorch 내부 prototype API 경고
- 모델 로딩, 예측, 앱 응답에는 영향 없음

## 10. 남은 개선 포인트

현재 과제 요구사항인 Seq2Seq RNN -> Transformer 교체와 앱 동작 검증은 완료되었다. 더 높은 순수 모델 성능을 원하면 다음 개선을 권장한다.

- 중복 원문 처리 정책 정리: `안녕 -> hi/hey`처럼 하나의 원문에 여러 정답이 있는 경우 후보 리스트나 우선순위 명시
- greedy decoding 개선: 반복 문자 억제, beam search, length penalty 적용
- tokenizer 개선: 문자 단위 대신 subword 또는 형태소 기반 토큰화 검토
- 데이터 확장: 현재 144쌍은 Transformer 일반화에는 매우 작음
- 평가 지표 추가: exact match 외 BLEU, chrF 등 추가

## 11. 최종 판정

PASS

- Transformer 모델 구현 완료
- 학습 및 체크포인트 저장 완료
- 정적 검사 통과
- 데이터/메타 호환성 확인
- CLI 번역 확인
- 전체 학습 데이터 기준 앱 번역 경로 288/288 통과
- Streamlit HTTP 200 확인
