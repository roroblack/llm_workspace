# test1.py
# 한글 형태소 분석기 사용 테스트 1

# Hannanum : KAIST 말뭉치를 이용해서 생성된 사전 분석기
from konlpy.tag import Hannanum, Komoran, Okt

hannanum = Hannanum()

# 제공 메소드 : 레퍼런스.메소드명() 사용
# analyze() : 구 (parse) 분석
# morphs() : 형태소 분석
# nouns() : 명사만 분석
# pos() : 형태소 분석 + 태깅

# 사용
print('Hannanum 분석기 이용 ---------------------------------')
text = u'길동 마트의 흑마늘 양념 치킨이 논란이 되고 있다.'
print('analyze  : ', hannanum.analyze(text))
print('morphs   : ', hannanum.morphs(text))
print('nouns    : ', hannanum.nouns(text))
print('pos      : ', hannanum.pos(text))

# KKma (꼬꼬마) : 세종 말뭉치를 이용해 생성된 사전 분석기 (서울대에서 만듦)
from konlpy.tag import Kkma
kkma = Kkma()

# 메소드 정리
# sentences() : 문장 분석
# morphs() : 형태소 분석
# nouns() : 명사만 분석
# pos() : 형태소 분석 + 태깅

print('Kkma 분석기 이용 -----------------------------')
print('sentences : ', kkma.sentences(text))
print('morphs    : ', kkma.morphs(text))
print('nouns     : ', kkma.nouns(text))
print('pos       : ', kkma.pos(text))

# Komoran : Java 로 만들어진 오픈소스 한글 형태소 분석기
from konlpy.tag import Komoran
kom = Komoran()

print('Komoran 분석기 이용 ---------------------------------')
print('morphs    : ', kom.morphs(text))
print('nouns     : ', kom.nouns(text))
print('pos       : ', kom.pos(text))


from konlpy.tag import Okt
okt = Okt()
print('Okt 분석기 이용 --------------------------------------')
print('phrases   : ', okt.phrases(text))
print('morphs    : ', okt.morphs(text))
print('nouns     : ', okt.nouns(text))
print('pos       : ', okt.pos(text))



# stem : 각 단어에서 어간 추출 처리 매개변수
print('Okt method : stem parameter using ------------------------')
print('stem : ', okt.morphs(text, stem=True))
print('stem : ', okt.morphs(text, stem=True, norm=True))

