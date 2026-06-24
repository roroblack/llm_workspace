# git 에서 'create repository' 로 프로젝트 저장소 생성
# url 주소 복사해 두기

# 파이참에서 '새 프로젝트' 생성
# 기본 설정 파일 작성 : .gitignore, requirements.txt, README.md 작성

# 저장소 연결
git remote add origin https://github.com/roroblack/llm_workspace.git

# 연결 확인
git remote -v

# 브랜치 (branch) 확인
git branch

# .gitignore 작성

# PyCharm GUI   : git 메뉴 > commit > 커밋 메세지 작성 > 커밋 클릭
# 터미널        : 
git add .
git commit -m "initial commit"

# 만약 master 라면 main 으로 변경
git branch -M main
# 확인
git branch

# 최초 업로드 : Main 브랜치 push
git push -u origin main
# 옵션 설명
# -u : 현재 브랜치(main) 와 GitHub 의 main 을 연결

# 브라우저 github 에서 새로고침하고 업로드 확인

# 최초 업로드 이후 작업 방법
# 1. 코드 파일 추가 | 코드 수정 작업 > 저장
# 2. 지역 저장소에 추가 : 커밋 (commit) 
# 파이참에서 커밋 방법 3가지 중 선택 사용함
# 방법 1 : git 메뉴 > 커밋 클릭
# 방법 2 : 왼쪽 '커밋' 뷰 > 변경 파일 중 선택해서 커밋
# 방법 3 : 터미널에서 명령어 입력
git add .
git commit -m 'second commit - 텍스트 파일을 추가'

# 3. 커밋한 다음, github 로 전송 : push
# 3 가지 방법 중 선택 후
git push
