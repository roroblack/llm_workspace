# 깃 저장소 상위 프로젝트의 깃에서 분리시키기

# 1. 부모 저장소에서 추적 해제
git rm -r --cached <폴더명>/

# 2. 부모 .gitignore에 추가 (다시 추적 안 되게)
echo "<폴더명>/" >> .gitignore
git add .gitignore
git commit -m "Remove <폴더명> from tracking"

# 3. 해당 폴더로 이동 후 독립 저장소 초기화
cd <폴더명>
git init
git remote add origin <원격 주소>

# 4. 첫 커밋 후 push
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main

# -----------------------------------------

# 다시 연결하기

# 1. 하위 폴더의 .git 제거 (독립 저장소 해제)
rm -rf <폴더명>/.git

# 2. 부모 .gitignore에서 해당 폴더 제거
# (직접 편집해서 <폴더명>/ 줄 삭제)

# 3. 부모 저장소에서 추적 시작
git add <폴더명>/
git commit -m "Add <폴더명> back to tracking"
