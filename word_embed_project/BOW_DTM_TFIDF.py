# BOW_DTM_TFIDF.py

'''
BOW (bag of words)
: 단어의 순서는 고려하지 않고, 단어가 몇번 등장했는지에 집중하는 텍스트 수치화 방법

DTM (document-term matrix)
: 여러 문서의 BOW 를 하나의 행렬로 모은 것

TF-IDF (term frequency-inverse document frequency)
: TF 는 특정 문서 안에서 단어가 얼마나 자주 등장하는지 나타냄
: IDF 는 특정 단어가 여러 문서에서 얼마나 자주 등장하는지 나타냄
'''

import sys
import subprocess
from math import log

try :
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
except ModuleNotFoundError as e:
    raise ModuleNotFoundError("scikit-learn 모듈이 설치되어 있지 않습니다. 'pip install scikit-learn' 명령어로 설치해주세요.") from e

try :
    from konlpy.tag import Okt
    okt = Okt()
    KONLPY_AVAILABLE = True
except ModuleNotFoundError as e:
    print("konlpy 모듈이 설치되어 있지 않습니다. 'pip install konlpy' 명령어로 설치해주세요.")
    print("또한, konlpy는 Java 환경이 필요하므로, Java가 설치되어 있는지 확인해주세요.")
    KONLPY_AVAILABLE = False

try :
    import nltk
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ModuleNotFoundError as e:
    print("nltk 모듈이 설치되어 있지 않습니다. 'pip install nltk' 명령어로 설치해주세요.")
    NLTK_AVAILABLE = False
    stopwords = None
    nltk = None



# ==============================================
# 공통 출력 함수 정의
# ==============================================
def print_separator(title): # 실습에서 단계별 제목을 보기좋게 출력
    '''콘솔에서 실습 구간을 구분하기 위한 제목 출력 함수입니다.'''
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80 + "\n")

# BOW 직접 구현 : 한국어 현태소 분석 기반 Bag of Words 생성
print_separator("1. BOW 직접 구현 : 한국어 문장을 단어 빈도 벡터로 변환")

if not KONLPY_AVAILABLE:
    print("[안내] konlpy 모듈이 설치되어 있지 않아 BOW 직접 구현을 진행할 수 없습니다.")
    print('[대체 실행] 현재 코드는 공백 기반 토큰화를 사용하여 계속 실행합니다.')
    sys.exit(1)

def tokenize_korean(document):
    '''Okt 가 가능하면 형태소 분석을 사용하고, 
        불가능하면 공백 기준으로 토큰화'''
    cleaned_document = document.replace('.', '') # 마침표 제거 (불필요한 기호 제거 : 정제)
    cleaned_document = cleaned_document.replace(',', '') # 쉼표 제거 (불필요한 기호 제거 : 정제)
    if KONLPY_AVAILABLE:
        return okt.nouns(cleaned_document)
    
    return cleaned_document.split() # 공백 기준으로 단어를 나눔 : 토큰화

def build_bag_of_words(document):
    '''인자 문서에서 단어 인덱스 사전과 단어 빈도 벡터를 생성하는 함수'''
    tokenized_documents = tokenize_korean(document)
    word_to_index = {}
    bow = []

    for word in tokenized_documents: # bow 사전과 빈도 벡터 생성
        if word not in word_to_index:
            word_to_index[word] = len(word_to_index)
            bow.append(1)  # 새로운 단어는 빈도 1로 초기화
        else:
            index = word_to_index[word]
            bow[index] += 1  # 기존 단어는 빈도 증가
    return word_to_index, bow # 단어 인덱스 사전과 빈도 벡터 리턴

    # for document in document:
    #     tokens = tokenize_korean(document)
    #     for token in tokens:
    #         if token in bow:
    #             bow[token] += 1
    #         else:
    #             bow[token] = 1
    return bow

# bow 사용 테스트
doc1 = '파이썬 이용 텍스트 빈도수 카운트 실습 진행'
vocab, bow = build_bag_of_words(doc1)

print("입력 문장:", doc1)
print("단어 인덱스 사전:", vocab)
print("단어 빈도 벡터:", bow)



# =============================================
# 2. CountVectorizer 를 이용한 BOW 생성
# =============================================

print_separator("2. CountVectorizer 를 이용한 BOW 생성")

corpus = ['you know I want your love. I love you']
vec = CountVectorizer()
bow_matrix = vec.fit_transform(corpus).toarray() 
# 코퍼스를 학습, 단어 빈도 행렬 (희소행렬) 을 배열로 변환
print('입력 코퍼스 : ', corpus)
print('bag of words matrix : ')
print(bow_matrix)
print('Vocabulary : ')
print(vec.vocabulary_) # 단어 인덱스 사전 확인



# =============================================
# 3. 불용어 제거
# =============================================
print_separator("3. 사용자 정의 불용어 제거")

text = ['Family is not an important thing. It\'s everything.']
custom_stop_words = ['the', 'a', 'is', 'an', 'it', 's', 'not']  # 사용자 정의 불용어 리스트
vect_custom = CountVectorizer(stop_words=custom_stop_words)
custom_matrix = vect_custom.fit_transform(text).toarray()
print('입력 문장 : ', text)
print('직접 정의한 불용어 :', custom_stop_words)
print('불용어 제거 후 BOW 행렬 :')
print(custom_matrix)
print('Vocabulary : ')
print(vect_custom.vocabulary_)

# nltk 가 제공하는 불용어 사전 이용해서 불용어 제거
# CountVectroizer 에서 제공하는 stop_words='english' 옵션을 사용하면, 영어 불용어 사전을 자동으로 적용할 수 있습니다.



# =============================================
# 4. 워드 임베딩 
# =============================================
print_separator("4. DTM 과 TF-IDF 를 이용한 워드 임베딩")

docs = [
    '배우고 싶은 자연어',                       # 첫 문서
    '딥러닝 머신러닝 배우고 싶은 강화학습',     # 두번째
    '자연어 처리 좋아요',                       # 세번째
    '배우고 싶은 딥러닝',                       # 네번째 문서
]

vocab = sorted(set(word for doc in docs for word in doc.split())) # 단어 사전 생성
N = len(vocab)
print('문서 목록')
for idx, doc in enumerate(docs, start=1):
    print(f'문서 {idx}: {doc}') # 번호 : 문서 출력

print('vocabulary : ', vocab)
print('문서개수 N : ', N)

