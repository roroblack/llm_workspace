# 프로젝트 설명
자연어 텍스트 데이터 전처리와 워드 임베딩 테스트 프로젝트

# 실행환경
- Windows 11
- Python 3.11
- PyCharm Professional
- Java/OpenJDK 설치 : KoNLPy 에서 필요

# 필요 패키지 설치 방법
PyCharm 에서 프로젝트 폴더 열기한 다음 터미널에서 실행 :
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 프로젝트 구조
word_embed_project/
    |- .venv/
    |- .git/
    |- .gitignore
    |- requirements.txt
    |- README.md
    |- main.py
    |- 실습파일.py

# 패키지 폴더/파일명.py 설명

# GitHub 업로드 방법 (각자 브렌치에서 진행)
# 마스터가 올린 프로젝트를 각 브랜치로 복제받음
# 각자 작업 수행함 > save
git add .
git commit -m 'Add test.py word embedding test code.'
<!-- git push origin main -->
git push

git init
git add .
git commit -m 'initial text preprocessing test project'
git branch -M main
git remote add origin https://github.com/마스터아이디/저장소이름.git
git push -u origin main