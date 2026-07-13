# 다른 사람의 GitHub 레포지토리를 클론한 뒤 배정받은 브랜치로 푸시하는 방법

## 1. 목적

다른 사람이 만든 GitHub 레포지토리를 내 컴퓨터로 클론한 뒤, 내가 배정받은 브랜치에 작업한 파일을 추가하고 원격 저장소에 푸시하는 방법을 정리한다.

이 문서의 핵심은 다음과 같다.

- 원격 레포지토리를 로컬 컴퓨터로 가져온다.
- 내가 배정받은 브랜치로 이동한다.
- 작업 파일을 추가하거나 수정한다.
- 변경 내용을 커밋한다.
- 배정받은 브랜치로만 푸시한다.

## 2. 사전 준비

작업 전에 다음 사항을 확인한다.

1. Git이 설치되어 있어야 한다.
2. GitHub 계정이 있어야 한다.
3. 해당 레포지토리에 접근 권한이 있어야 한다.
4. 레포지토리 주소를 알고 있어야 한다.
5. 내가 배정받은 브랜치 이름을 알고 있어야 한다.

예시에서는 다음 값을 사용한다.

```bash
레포지토리 주소: https://github.com/owner/project-name.git
배정받은 브랜치: feature/my-name
```

실제 작업할 때는 위 값을 본인의 레포지토리 주소와 브랜치 이름으로 바꾸어 사용한다.

## 3. 레포지토리 클론하기

먼저 작업할 위치로 이동한 뒤, GitHub 레포지토리를 클론한다.

```bash
git clone https://github.com/owner/project-name.git
```

클론이 완료되면 생성된 프로젝트 폴더로 이동한다.

```bash
cd project-name
```

현재 원격 저장소가 잘 연결되어 있는지 확인한다.

```bash
git remote -v
```

정상적으로 연결되어 있다면 `origin`이라는 이름으로 GitHub 주소가 표시된다.

## 4. 브랜치 목록 확인하기

원격 저장소에 있는 브랜치 목록을 확인한다.

```bash
git branch -a
```

예를 들어 다음과 같이 보일 수 있다.

```bash
* main
  remotes/origin/main
  remotes/origin/feature/my-name
```

여기서 `remotes/origin/feature/my-name`이 내가 배정받은 브랜치라고 가정한다.

## 5. 배정받은 브랜치로 이동하기

원격에 이미 만들어진 브랜치를 로컬에서 사용하려면 다음 명령어를 실행한다.

```bash
git switch -c feature/my-name origin/feature/my-name
```

이미 로컬에 같은 브랜치가 존재한다면 다음 명령어로 이동한다.

```bash
git switch feature/my-name
```

현재 내가 어떤 브랜치에 있는지 확인한다.

```bash
git branch
```

현재 브랜치 앞에는 `*` 표시가 붙는다.

```bash
* feature/my-name
  main
```

작업 전 최신 상태를 가져오기 위해 pull을 실행한다.

```bash
git pull origin feature/my-name
```

## 6. 작업 파일 추가 또는 수정하기

이제 프로젝트 폴더 안에서 내가 제출해야 할 파일을 추가하거나 수정한다.

예를 들어 `reports/my_report.md` 파일을 추가했다고 가정한다.

작업 후 변경 상태를 확인한다.

```bash
git status
```

변경된 파일 목록이 표시된다.

## 7. 변경 파일 스테이징하기

특정 파일만 추가하려면 다음과 같이 입력한다.

```bash
git add reports/my_report.md
```

현재 변경된 모든 파일을 추가하려면 다음 명령어를 사용할 수 있다.

```bash
git add .
```

단, `git add .`를 사용할 때는 불필요한 파일까지 포함되지 않았는지 반드시 `git status`로 확인해야 한다.

```bash
git status
```

## 8. 커밋하기

스테이징한 파일을 커밋한다.

```bash
git commit -m "Add my report"
```

커밋 메시지는 작업 내용을 짧고 명확하게 작성한다.

좋은 예시는 다음과 같다.

```bash
git commit -m "Add sentiment analysis report"
git commit -m "Update preprocessing code"
git commit -m "Fix model training script"
```

## 9. 배정받은 브랜치로 푸시하기

가장 중요한 단계이다. 반드시 내가 배정받은 브랜치로 푸시해야 한다.

```bash
git push origin feature/my-name
```

여기서 `feature/my-name`은 본인이 배정받은 브랜치 이름으로 바꾼다.

절대로 확인 없이 `main` 브랜치에 직접 푸시하지 않는다.

```bash
# 잘못된 예시
git push origin main
```

푸시가 완료되면 GitHub 레포지토리에서 해당 브랜치에 파일이 올라갔는지 확인한다.

## 10. 전체 명령어 흐름 정리

처음 클론부터 푸시까지의 전체 흐름은 다음과 같다.

```bash
git clone https://github.com/owner/project-name.git
cd project-name

git branch -a
git switch -c feature/my-name origin/feature/my-name

git pull origin feature/my-name

git status
git add .
git status

git commit -m "Add my work"
git push origin feature/my-name
```

## 11. 자주 발생하는 문제와 해결 방법

### 11.1 권한 오류가 발생하는 경우

푸시할 때 다음과 같은 오류가 발생할 수 있다.

```bash
Permission denied
403 Forbidden
```

이 경우 해당 레포지토리에 푸시 권한이 없을 가능성이 높다.

해결 방법은 다음과 같다.

- 레포지토리 소유자에게 collaborator 권한을 요청한다.
- organization 레포지토리라면 팀 권한을 확인한다.
- GitHub 로그인이 올바른 계정으로 되어 있는지 확인한다.

### 11.2 브랜치 이름을 잘못 입력한 경우

브랜치 목록을 다시 확인한다.

```bash
git branch -a
```

원격 브랜치 정보를 최신으로 가져온다.

```bash
git fetch origin
```

그 후 정확한 브랜치 이름으로 다시 이동한다.

```bash
git switch -c feature/my-name origin/feature/my-name
```

### 11.3 푸시 전에 최신 내용이 아니라고 나오는 경우

다른 사람이 같은 브랜치에 먼저 푸시했을 수 있다. 먼저 pull을 실행한다.

```bash
git pull origin feature/my-name
```

충돌이 없다면 다시 푸시한다.

```bash
git push origin feature/my-name
```

충돌이 발생하면 충돌 파일을 수정한 뒤 다시 add, commit, push를 진행한다.

```bash
git add .
git commit -m "Resolve merge conflict"
git push origin feature/my-name
```

## 12. 최종 확인 체크리스트

푸시 전 다음 내용을 확인한다.

- 현재 브랜치가 내가 배정받은 브랜치인지 확인했다.
- `git status`로 추가될 파일 목록을 확인했다.
- 불필요한 파일이 커밋에 포함되지 않았다.
- 커밋 메시지를 작성했다.
- `git push origin 브랜치명` 형식으로 푸시했다.
- GitHub에서 내 브랜치에 파일이 올라간 것을 확인했다.

## 13. 결론

다른 사람의 레포지토리를 클론해서 작업할 때는 브랜치 확인이 가장 중요하다. 반드시 내가 배정받은 브랜치로 이동한 뒤 작업하고, 푸시할 때도 `git push origin 브랜치명` 형식으로 정확히 입력해야 한다. 이렇게 하면 공동 작업 중 다른 사람의 작업이나 `main` 브랜치에 영향을 주지 않고 안전하게 자료를 제출할 수 있다.
