'''
자연어 텍스트 데이터 전처리 프로젝트 과제

프로젝트명 : konlpy_practice_project
깃 리포지토리 이름도 동일하게 생성함
main 브렌치 사용함

뉴스 기사, PDF 텍스트, 크롤링 데이터 중 하나를 수집하여 다음 과정을 수행하시오.

텍스트 수집
텍스트 정제
형태소 분석
불용어 제거
단어 빈도 계산
PyTorch Tensor 변환
워드클라우드 생성
상위 20개 단어 시각화
결과 분석 보고서 작성

작성한 모든 내용을 깃허브에 푸시하시오.

내일 수업 시작 전까지 깃 주소를 디스코드 '실시간' 채널에 업로드하시오.
'''

# ============================================
# PyTorch 기반 한국어 워드 클라우드 작성 실습
# ============================================

# 정규표현식을 사용하기 위한 re 모듈을 불러옵니다.
import os
os.environ["JAVA_HOME"] = "C:/Program Files/Java/jdk-21.0.2"

import re

# 단어 빈도 계산을 쉽게 하기 위해 Counter를 불러옵니다.
from collections import Counter

# PyTorch 텐서 처리를 위해 torch를 불러옵니다.
import torch

# 표 형태 데이터 처리를 위해 pandas를 불러옵니다.
import pandas as pd

# 그래프 출력을 위해 matplotlib을 불러옵니다.
import matplotlib.pyplot as plt

# 워드 클라우드 생성을 위해 WordCloud를 불러옵니다.
from wordcloud import WordCloud

# 한국어 형태소 분석을 위해 Okt 형태소 분석기를 불러옵니다.
from konlpy.tag import Okt


okt = Okt(max_heap_size=256)
word_dic = {}
lines = []



# ========================================================================
# 텍스트 수집
# ========================================================================

with open('./data/gpt3_tr_korean_only.txt', encoding='utf-8') as raws:
    for line in raws:
        lines.append(line.strip())



# ========================================================================
# 텍스트 정제
# ========================================================================

lines = [line for line in lines if line]
clean_text = re.sub('[^ㄱ-ㅎㅏ-ㅣ가-힣 ]', '', ' '.join(lines))
clean_text = re.sub(' +', ' ', clean_text).strip()  # 여러 개의 공백을 하나로 줄이고 양쪽 공백 제거

# print("정제된 텍스트:")
# print(clean_text)
print(f"총 글자 수: {len(clean_text)}")

# print('nouns     : ', okt.nouns(clean_text))



# ========================================================================
# 형태소 분석
# ========================================================================
print(clean_text.split()) 

pos = okt.pos(clean_text)
morphs = okt.morphs(clean_text)
nouns = okt.nouns(clean_text)

# print('pos      : ', pos)
# print('morphs   : ', morphs)
# print('nouns    : ', nouns)



# ========================================================================
# 불용어 제거
# ========================================================================

stopwords = ['는', '이', '가', '을', '를', '의', '에', '도', '로', '과', '와', '한', '하다', '있다', '되다', '수', '것', '그']

tokens = [token for token in nouns if token not in stopwords]
# print(tokens)


# ========================================================================
# 단어 빈도 계산
# ========================================================================
vocab           =   sorted(set(nouns))
word_to_id      =   {word: idx for idx, word in enumerate(vocab)}
word_ids        =   [word_to_id[word] for word in nouns]
word_ids_tensor =   torch.tensor(word_ids, dtype=torch.long)

word_counts_tensor = torch.bincount(word_ids_tensor)

word_freq = {
    vocab[i]: int(word_counts_tensor[i].item())
    for i in range(len(vocab))
}

sorted_word_freq = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

# print("\n단어 빈도:")
# for word, freq in sorted_word_freq:
#     print(f"{word}: {freq}")


word_freq_series = pd.Series(word_freq)

top_words_cnt = 20
print(f"\n상위 단어 {top_words_cnt}:")
print(word_freq_series.sort_values(ascending=False).head(top_words_cnt))


# ========================================================================
# PyTorch Tensor 변환
# ========================================================================

# 위에서 이미 텐서 변환 해둠
# print("word_ids_tensor   :", word_ids_tensor)
# print("word_counts_tensor:", word_counts_tensor)

# ========================================================================
# 워드클라우드 생성
# ========================================================================
font_path = "./fonts/malgunsl.ttf"  # 한글 폰트 경로 설정

wordcloud = WordCloud(
    font_path=font_path,
    width=400,
    height=300,
    background_color='white'
).generate_from_frequencies(dict(sorted_word_freq[:top_words_cnt]))

# ========================================================================
# 상위 20개 단어 시각화
# ========================================================================

# 그래프 크기를 설정합니다.
plt.figure(figsize=(12, 8))

# 워드 클라우드 이미지를 화면에 표시합니다.
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title("워드 클라우드", fontsize=20)
plt.show()

# ========================================================================
# 결과 분석 보고서 작성
# ========================================================================

top20 = sorted_word_freq[:20]

report = f"""
========================================================
        자연어 텍스트 데이터 전처리 결과 분석 보고서
========================================================

1. 개요
   본 보고서는 GPT-3 논문(Language Models are Few-Shot Learners)의
   한국어 번역 텍스트를 대상으로 자연어 처리 파이프라인을 적용한
   결과를 기술합니다.

2. 데이터 수집
   - 출처 : GPT-3 논문 한국어 번역본 (gpt3_tr_korean_only.txt)
   - 총 줄 수 : {len(lines)}줄
   - 정제 후 글자 수 : {len(clean_text)}자

3. 텍스트 정제
   - 한글 및 공백 이외의 모든 문자(영문, 숫자, 특수기호) 제거
   - 연속 공백 단일화 및 빈 줄 제거

4. 형태소 분석
   - 분석기 : KoNLPy Okt (Open Korean Text)
   - 추출 품사 : 명사(Noun) 중심 분석
   - 추출된 명사 토큰 수 : {len(nouns)}개
   - 고유 명사 종류 수 : {len(vocab)}개

5. 불용어 제거
   - 제거 대상 : 조사·대명사·형식명사 등 의미가 낮은 단어
   - 불용어 제거 후 토큰 수 : {len(tokens)}개

6. 단어 빈도 계산 (PyTorch Tensor 활용)
   - torch.tensor()로 단어 ID 텐서 생성
   - torch.bincount()로 단어별 빈도 산출

   [ 상위 20개 단어 빈도 ]
   {"".join([f"   {rank+1:>2}. {word:<12} {freq}회{chr(10)}" for rank, (word, freq) in enumerate(top20)])}

7. 워드클라우드 생성
   - 상위 20개 단어를 기반으로 워드클라우드 시각화
   - 사용 폰트 : 맑은 고딕 (malgunsl.ttf)

8. 결론
   GPT-3 논문의 핵심 주제어인 '모델', '학습', '언어', '성능' 등의
   단어가 높은 빈도로 등장하며, 대규모 언어 모델의 학습 방법론과
   성능 평가에 관한 내용이 본문의 중심임을 확인할 수 있습니다.
========================================================
"""

print(report)

with open('./report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("보고서가 report.md 파일로 저장되었습니다.")
