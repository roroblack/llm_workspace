# test2.py

# konlpy 모듈에서 제공하는 메소드의 매개변수 사용 테스트
from konlpy.tag import Okt
from konlpy.utils import read_txt # 함수 임포트

# 형태소 분석 + 태깅 : pos(), morphs(), nouns() 등에 사용되는 매개변수들
# stem : 형태소의 원형을 찾아서 반환해 줌
# norn : 형태소를 깔끔하게 정리해 주고, 불필요한 데이터 지움

okt = Okt()

# data 폴더에서 텍스트 파일 읽어와서 분석에 사용하기
text = read_txt('./data/sample.txt', u'utf-8')

print('norn = True, stem = True ----------------------------------------')
mal_list = okt.pos(text, norm=True, stem=True)
print(mal_list)

print('norn = False, stem = False ----------------------------------------')
mal_list = okt.pos(text, norm=False, stem=False)
print(mal_list)

print('norn = True, stem = False ----------------------------------------')
mal_list = okt.pos(text, norm=True, stem=False)
print(mal_list)