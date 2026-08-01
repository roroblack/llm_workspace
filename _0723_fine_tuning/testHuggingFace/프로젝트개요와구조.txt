[프로젝트 개요와 구조]
 HuggingFace (Transformers) 모델 사용 테스트 웹 에플리케이션
 핵심 구현: 
  HuggingFace pipeline 구성 : 전처리 -> 추론 -> 후처리 묶어서 추론을 수행

* Hugging Face Transformers : 
  BERT, RoBERTa, T5, BART, MarianMT 같은 사전학습(Pretrained) Transformer 모델을
  쉽게 다운로드/로딩하여 추론(inference) 또는 파인튜닝(fine-tuning)에 사용하는 라이브러리임
  - 모델과 토크나이저를 모델 이름만으로 불러오는 Auto Classes (AutoTokenizer, AutoModel,...)를 제공함 
  - pipeline(task=...) 방법이 가장 쉬움

* 사용 목적:
 - 빠른 적용 : 이미 학습된 모델을 가져와서 바로 분류/요약/번역 등 작업을 수행할 수 있음
 - 프로덕션 서비스 : REST API(FastAPI 등)로 감싸서 사내 문서 처리, 고객 문의 분류, 다국어 번역 API 등 제공

* 활용 분야:
 - Text Classification : 감성분석(긍정/부정), 스팸 분류, 주제 분류, 위험/유해 발화 감지 등
 - Summarization : 뉴스/보고서 요약, 회의록 요약 (추상적 요약)
 - Translation : 다국어 번역 (한<->영 등), 다국어 고객지원/문서 현지화

[구현 핵심 내용]
1. 모델 로딩 : 
  - pipeline 개념, 캐시 폴더, 첫 다운로드 시간 등
2. Text Classification : 
  - 입력/출력 형식, 라벨(label)과 score 해석, 배치 처리
3. Summarization :
  - 입력 길이 제한, max_length / min_length, 긴 문서 분할 전략
4. Translation :
  - 언어쌍 모델 선택, 번역 품질/도메인 이슈
5. FastAPI 서비스화 :
  - 모델 싱글톤 로딩, endpoint 설계, 요청/응답 스키마

[개발 환경]
windows + cpu + python 3.11

- 가상환경 구성 -> 활성화
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

- requirements.txt : 설치 패키지 목록 작성 -> 저장
  transformers : Hugging Face 모델/파이프라인
  torch (CPU) : 제공되는 대부분의 모델이 PyTorch 기반임 (windows cpu 지원)
  * 별도 설치도 방법임
  pip install transformers torch --index-url https://download.pytorch.org/whl/cpu

- 패키지 설치 : 
pip install -U -r requirements.txt

[웹 에플리케이션 구조]
testHuggingFace/
  app/
    main.py
    core/
      config.py
      hf/
        pipelines.py
    models/
      schemas.py
    routers/
      nlp_router.py
  requirements.txt
  .venv


[Swagger UI 실행 테스트]


1 감성 분석 `/nlp/classify`:
    중립·긍정·부정 경계**, 문맥 반전(sarcasm), 복합 감정 확인용

# 기본 긍정:
{
  "text": "The lecture was clear, well structured, and very helpful for understanding AI fundamentals."
}


# 명확한 부정"
{
  "text": "This service is extremely slow, unreliable, and the support team never responds."
}


# 문맥 반전(중요 테스트):
{
  "text": "I thought this course would be great, but it turned out to be a complete waste of time."
}


# 약한 부정(애매한 케이스)"
{
  "text": "The product works, but it feels outdated and lacks important features."
}



2️ 요약 `/nlp/summarize`"
  긴 입력, 핵심 추출, max/min 길이 효과 검증

# 실전 기사형 텍스트 (권장): (반드시 한줄 문장일 것)
{
  "text": "Artificial intelligence has rapidly transformed various industries over the past decade.
In healthcare, AI is being used to assist doctors in diagnosing diseases more accurately and efficiently. In finance, machine learning models analyze vast amounts of data to detect fraud and optimize investment strategies. However, despite these advancements, concerns remain regarding data privacy, algorithmic bias, and job displacement. Experts emphasize that responsible AI development, combined with proper regulation and ethical guidelines, is essential to ensure that the benefits of AI outweigh its potential risks.",
  "max_length": 120,
  "min_length": 40
}


# 더 긴 문서(분할 요약 테스트용):
{
  "text": "Large language models have become a central topic in artificial intelligence research. These models are trained on massive datasets and are capable of performing tasks such as translation, summarization, and question answering. Despite their impressive capabilities, they require significant computational resources and raise concerns related to environmental impact. Researchers are now focusing on model efficiency, parameter reduction, and knowledge distillation techniques to address these challenges. As AI systems become more integrated into daily life, transparency and explainability are increasingly important.",
  "max_length": 100,
  "min_length": 30
}



3 번역 `/nlp/translate` (NLLB 기준):
  단문·복문·전문 문장 테스트

# 일상 문장"
{
  "text": "Hello, how are you doing today?"
}


# 복문(문법 구조 테스트):
{
  "text": "Although the project was challenging, the team successfully completed it on time."
}

# 기술 문장 (실무 테스트):
{
  "text": "Large language models require careful fine-tuning and evaluation to ensure reliable performance in real-world applications."
}


# 질문형 문장:
{
  "text": "What are the ethical challenges associated with deploying AI systems in healthcare?"
}

