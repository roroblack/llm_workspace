# llm_workspace

자연어 처리(NLP) 및 LLM 관련 학습 프로젝트를 통합 관리하는 워크스페이스입니다.

---

## 프로젝트 구성

| 폴더 | 설명 | 개별 GitHub |
|------|------|------------|
| `konlpy_practice_project` | KoNLPy 기반 한글 텍스트 전처리 파이프라인 | [study-ai-skn/konlpy_practice_project](https://github.com/study-ai-skn/konlpy_practice_project) |
| `nlp_model_project` | CNN 스팸 분류 / LSTM 영화 리뷰 감성 분석 | [study-ai-skn/nlp_model_project](https://github.com/study-ai-skn/nlp_model_project) |
| `word_embed_project` | 워드 임베딩 / BOW / DTM / TF-IDF 실습 | [study-ai-skn/word_embed_project](https://github.com/study-ai-skn/word_embed_project) |
| `test_konlpy_project` | KoNLPy 설치 테스트 및 워드클라우드 실습 | — |

---

## 실행 환경

- Windows 11
- Python 3.11
- PyCharm Professional / VSCode
- Java/OpenJDK (KoNLPy 사용 시 필요)

---

## Git Remote 구성

```
origin      https://github.com/roroblack/llm_workspace        (전체 워크스페이스)
konlpy      https://github.com/study-ai-skn/konlpy_practice_project
nlp_model   https://github.com/study-ai-skn/nlp_model_project
word_embed  https://github.com/study-ai-skn/word_embed_project
```

remote 목록 확인:

```bash
git remote -v
```

---

## Push 방법

### 워크스페이스 전체를 llm_workspace에 push

```bash
git add .
git commit -m "커밋 메시지"
git push origin main
```

### 개별 프로젝트를 각자의 GitHub repo에 push (subtree)

```bash
# konlpy_practice_project
git subtree push --prefix=konlpy_practice_project konlpy main

# nlp_model_project
git subtree push --prefix=nlp_model_project nlp_model main

# word_embed_project
git subtree push --prefix=word_embed_project word_embed main
```

> `git subtree push`는 해당 폴더의 내용만 추출해서 개별 repo의 main 브랜치로 push합니다.  
> 중간에 remote가 diverge된 경우 `--force` 옵션을 추가합니다.

---

## Remote 초기 설정 (새 환경에서 클론 후)

```bash
git remote add konlpy https://github.com/study-ai-skn/konlpy_practice_project.git
git remote add nlp_model https://github.com/study-ai-skn/nlp_model_project.git
git remote add word_embed https://github.com/study-ai-skn/word_embed_project.git
```
