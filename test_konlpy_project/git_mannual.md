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