# Linux Mint 설치 · 실행 · GitHub 가이드

처음부터 GitHub 업로드, 그리고 매일 쓰는 루틴까지. 각 단계 끝의 **✅ 체크포인트**가 나오면 다음으로 넘어가세요.

---

## 0. 레포 안의 파일 지도

| 파일 | 역할 | 직접 고칠 일 |
|---|---|---|
| `src/converter.py` | 핵심 로직: allele 정규화 + 혈청형 룩업 | 자주 (학습 대상) |
| `src/cli.py` | 표 전체 변환 (pandas) | 2주차 |
| `src/generate_synthetic.py` | 가짜 타이핑 데이터 생성 (PHI 없음) | 가끔 |
| `data/reference/serologic_equivalents.csv` | 매핑 테이블 (교육용 subset) | **자주 — 도메인 지식이 들어가는 곳** |
| `tests/test_converter.py` | 자동 검증 | 기능 추가할 때마다 |
| `setup.sh` | 환경 1회 세팅 + 테스트 | 거의 없음 |
| `run.sh` | 생성 → 변환 → 요약 한 번에 | 거의 없음 |
| `.gitignore` | GitHub에 올리지 않을 것 목록 | 거의 없음 |
| `.venv/` | 이 프로젝트 전용 Python 환경 (자동 생성, 업로드 안 됨) | 손대지 않음 |

---

## 1단계. 터미널 열기 + 기본 도구 설치

터미널: 왼쪽 아래 메뉴 → `Terminal` 검색, 또는 **`Ctrl + Alt + T`**.

```bash
sudo apt update
sudo apt install -y git python3-venv python3-pip unzip
```

비밀번호 입력 시 화면에 아무것도 안 보이는 게 정상입니다.

✅ `git --version` 과 `python3 --version` 이 둘 다 버전 숫자를 출력

---

## 2단계. 프로젝트 풀기

zip을 Mint의 브라우저로 내려받으면 `~/Downloads`에 있습니다.

```bash
mkdir -p ~/projects
cd ~/projects
unzip ~/Downloads/hla-serologic-converter.zip
cd hla-serologic-converter
ls
```

✅ `README.md  data  docs  requirements.txt  run.sh  setup.sh  src  tests` 가 보임

---

## 3단계. 환경 세팅 (한 번만)

```bash
chmod +x setup.sh run.sh
./setup.sh
```

하는 일: `.venv` 생성 → pandas·pytest 설치 → 테스트 실행.

✅ 마지막에 `7 passed` 와 `Setup complete.`

> `venv module missing` 이 뜨면 1단계의 `python3-venv` 설치가 빠진 것. 설치 후 `./setup.sh` 재실행.

---

## 4단계. 실행

```bash
./run.sh          # 합성 샘플 20개
./run.sh 100      # 100개
```

단일 allele 변환:

```bash
.venv/bin/python -m src.cli --allele "DRB1*15:01"
# DRB1*15:01 -> DR15 (broad DR2)
```

✅ 출력 미리보기 + unmapped 개수가 표시됨 (A*99:01은 일부러 넣은 미매핑 allele)

---

## 5단계. Git 기본 설정 (한 번만)

```bash
git config --global user.name "EunSang"
git config --global user.email "GitHub에 가입한 이메일"
git config --global init.defaultBranch main
```

---

## 6단계. GitHub SSH 키 등록 (한 번만)

GitHub는 비밀번호 푸시를 막아두었기 때문에 키가 필요합니다. SSH 키는 한 번 등록하면 끝입니다.

```bash
ssh-keygen -t ed25519 -C "GitHub 이메일"
```

질문 3개는 전부 **Enter** (기본 위치, 암호 없음 — 원하면 암호 설정 가능).

```bash
cat ~/.ssh/id_ed25519.pub
```

출력된 `ssh-ed25519 AAAA...` 한 줄 전체를 복사 →
GitHub 웹 → 오른쪽 위 프로필 → **Settings → SSH and GPG keys → New SSH key** → 붙여넣기 → Add.

```bash
ssh -T git@github.com
```

처음엔 `Are you sure you want to continue connecting?` → `yes` 입력.

✅ `Hi <사용자명>! You've successfully authenticated` (뒤에 붙는 "shell access 없음" 문구는 정상)

---

## 7단계. 첫 커밋 (로컬)

```bash
cd ~/projects/hla-serologic-converter
git init
git add .
git status        # .venv 가 목록에 없어야 정상 (.gitignore가 막음)
git commit -m "Initial commit: HLA molecular to serologic converter scaffold"
```

✅ `git log --oneline` 에 커밋 1개

---

## 8단계. GitHub에 올리기

1. GitHub 웹 → 오른쪽 위 **+ → New repository**
2. 이름: `hla-serologic-converter`
3. Public / Private 선택 (합성 데이터뿐이라 Public도 안전)
4. **README, .gitignore, license 체크 전부 해제** (이미 로컬에 있음)
5. Create repository

```bash
git remote add origin git@github.com:<사용자명>/hla-serologic-converter.git
git push -u origin main
```

✅ GitHub 페이지 새로고침 → 파일들과 README가 보임

---

## 9단계. 매일 쓰는 루틴

```bash
cd ~/projects/hla-serologic-converter

# 1. 코드나 참조 테이블 수정 (편집기: xed, VS Code 등)
xed data/reference/serologic_equivalents.csv

# 2. 검증
.venv/bin/python -m pytest -q

# 3. 기록 + 업로드
git status
git add .
git commit -m "Add DRB1*09 family to reference table"
git push
```

**규칙: 테스트 통과 → 커밋 → 푸시.** 실패한 상태로는 커밋하지 않기 (랩 QC와 같은 원칙).

---

## 다른 컴퓨터에서 이어받기 (WSL, 다른 Linux 등)

```bash
git clone git@github.com:<사용자명>/hla-serologic-converter.git
cd hla-serologic-converter
./setup.sh
```

GitHub가 원본이 되므로, 어느 기기에서든 이 세 줄이면 같은 상태가 됩니다. (그 기기에서도 6단계 SSH 키 등록은 별도로 필요)

---

## 자주 막히는 곳

| 증상 | 원인 / 해결 |
|---|---|
| `Permission denied (publickey)` | 6단계 키 등록 누락 → 6단계 다시 |
| `remote origin already exists` | `git remote set-url origin git@github.com:<사용자명>/hla-serologic-converter.git` |
| `rejected ... fetch first` | GitHub 레포를 README 체크하고 만든 경우 → `git pull --rebase origin main` 후 `git push` |
| `externally-managed-environment` | `pip`를 `.venv` 밖에서 실행함 → 항상 `.venv/bin/python -m pip ...` |
| `./setup.sh: Permission denied` | `chmod +x setup.sh run.sh` |
| `ModuleNotFoundError: src` | 레포 최상위 폴더에서 실행해야 함 → `cd ~/projects/hla-serologic-converter` |
