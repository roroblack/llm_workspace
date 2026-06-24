# test3.py
# 공공 데이터 포털 (https://www.data.go.kr) 에서 csv 파일 다운받기
# csv 파일을 읽어 들여서, 읽어 들인 데이터에서 가장 많이 사용된 명사 찾기

import codecs
import csv

from konlpy.tag import Okt

from test2 import mal_list # 다른 py 파일의 리스트 임포트함

okt = Okt()
word_dic = {}
lines = []

# 파일변수 = open('파일명.확장자', '열기모드')
# 파일변수.read(), 파일변수.write()
# 파일 처리가 끝나면 반드시 파일변수.close()


# csv 파일에서 데이터 읽어 들이기 : codecs 모듈이 제공하는 함수 이용
# 파일 입출력이 끝나면, 자동 close 되게 하려면 with resource 문 사용하면 됨
with open('./data/sample2.csv') as raws: # 파일변수가 raws 임
    reader = csv.reader(raws) # csv 파일 읽기용 객체
    for row in reader: # reader 를 통해서 한 줄씩 문장 읽어들이기
        lines.append(row)
        # print(row)
# with---------------------------------------

# 저장 구조 : [[...], [...], [...], ... ]
for line in lines:
    # print(' '.join(line)) # '구분자'.join() -> str : 리스트 안의 값들을 공백으로 구분해서 하나의 문자열로 반환
    mal_list = okt.pos(' '.join(line))
    # print(mal_list)
# 명사들을 수집해서 반복되는 명사를 count 함
for word in mal_list:
    # print(word)
    if word[1] == 'Noun':
        if not word[0] in word_dic:
            word_dic[word[0]] = 0 # [단어 : 0] 저장 - 해당 단어가 없으면 0 으로 해서 키값 주라는 말
        # if not -----------------
        word_dic[word[0]] += 1 # 해당 단어가 있다면, 단어(키)의 값을 1 증가 시킴
# for ----------------------------

# print (word_dic)

# 단어 빈도수에 대해 내림차순정렬 처리
keys = sorted(word_dic.items(), key=lambda x :x[1], reverse=True)

# 50 개까지 정렬 결과 출력
# for word, count in keys[:50]:
#     print(f'(word) : (count)', end=',')

# wordcloud (말구름) 차트 만들기
# wordcloud 패키지 설지하고 사용함 => matplotlib 도 자동 같이 설치됨

from wordcloud import WordCloud
import matplotlib.pyplot as plt

# wordcloud = WordCloud(font_path='./fonts/malgunsl.ttf',
#                       background_color='white',
#                       width=1000,
#                       height=800,
#                       ).generate_from_frequencies(word_dic)
#
# plt.figure(figsize=(10, 10))
# plt.imshow(wordcloud)
# plt.axis("off")
# plt.show()


# wordcloud 모양을 원하는 도형 모양으로 변경하기
# mask 옵션 사용함
from PIL import Image # 이미지 파일 열기용 클래스
import numpy as np

img = Image.open('./images/heart.png')
imgArray = np.array(img)

wordcloud = WordCloud(
    font_path='./fonts/malgunsl.ttf',
    background_color='white',
    width=400,
    height=400,
    max_font_size=100, # 빈도수가 가장 큰 글자의 크기 지정
    mask=imgArray, # 사용하고자 하는 이미지의 수치 배열
)

wordcloud.generate_from_frequencies(word_dic)

plt.figure(figsize=(10, 10))
plt.imshow(wordcloud)
plt.axis("off")
plt.show()
