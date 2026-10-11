# hla-sero 가이드 (Linux Mint)

분자형 HLA 타이핑을 최신 IPD-IMGT/HLA 데이터 기준 혈청형으로 변환하는 프로그램.
붙여넣기만 하면 됩니다.

---

## 1. 설치 (한 번만)

```bash
cd ~/projects/hla-serologic-converter
./install.sh
```

하는 일:
1. `pipx` 설치 (없으면 — 비밀번호 물어봄)
2. `hla-sero` 명령 설치
3. IMGT/HLA 최신 릴리스 다운로드 + md5 체크섬 검증
4. Mint 메뉴에 **HLA Serology Converter** 추가

✅ 마지막에 `Done.` 이 나오면 완료. `hla-sero: command not found`가 뜨면 터미널을 닫고 새로 여세요.

> 다른 컴퓨터에 설치할 때는:
> `git clone https://github.com/bluebut11-EO/hla-serologic-converter.git && cd hla-serologic-converter && ./install.sh`

---

## 2. 사용법

### 창으로 쓰기 (추천)

메뉴 → **HLA Serology Converter**, 또는 터미널에서 `hla-sero gui`

1. 타이핑을 붙여넣기 — 엑셀에서 복사한 표, 보고서 한 줄, 목록 등 형식 무관
2. **Convert** (또는 `Ctrl + Enter`)
3. **By sample** 탭: 샘플별 항원 목록 / **Allele detail** 탭: allele별 근거
4. **Copy antigens** — 샘플별 항원 문자열 복사
   **Copy table for Excel** — 전체 표를 엑셀에 바로 붙여넣기
   **Download CSV** — 파일 저장
5. 끝나면 **Quit**

### 터미널로 쓰기

```bash
hla-sero convert                         # 붙여넣고 Enter → Ctrl+D
hla-sero convert typing.txt              # 파일 변환, 화면에 표
hla-sero convert typing.txt -o out.csv   # CSV로 저장
hla-sero demo | hla-sero convert         # 합성 예제로 연습
```

### 교차 확인 (현재 쓰는 혈청형과 비교)

allele 뒤에 현재 혈청형을 함께 붙여넣으면 줄마다 `match` / `broad-match` / `mismatch`가 표시됩니다.
엑셀 열(`Sample | Allele | 혈청형`) 그대로 복사해도 되고, `A*02:01 A2  B*15:03 B72`처럼 한 줄로 써도 됩니다.
자세한 내용과 검증용 양식: `docs/LAB_WINDOWS_KO.md`, `docs/cross_check_template.csv`

### 결과 상태 읽는 법

| 상태 | 의미 | 할 일 |
|---|---|---|
| `mapped` | 혈청학적으로 확인된 대응 (WMDA unambiguous/possible) | — |
| `assumed` | 확인된 혈청형 없음, allele 이름에서 추정 | **확인 필요** |
| `ambiguous` | 포함된 allele들이 서로 다른 항원 (예: `B*15`, `B*15:01/15:03`) | **확인 필요** — 후보 전부 표시됨 |
| `null` | 발현되지 않는 allele (N) | — |
| `no-equivalent` | WMDA에 혈청형 없음 (`?`), 또는 MICA 등 | — |
| `not-found` | 이 릴리스에 없는 이름 (오타·개명·삭제) | 이름 확인 |
| `unsupported` | NMDP MAC 코드 (`A*02:AB`) | allele로 풀어서 입력 |

2-field·G/P·XX 입력은 null/questionable(N/Q) allele을 자동 제외하고 개수를 표시합니다.
모든 결과에 사용한 IMGT/HLA 릴리스 번호가 찍힙니다.

---

## 3. 데이터 업데이트

IMGT/HLA는 1년에 4번(1·4·7·10월) 새 릴리스를 냅니다.

| 명령 | 동작 |
|---|---|
| `hla-sero status` | 현재 사용 중인 릴리스, 설정 확인 |
| `hla-sero update` | 지금 바로 새 릴리스 확인 |
| `hla-sero config --auto-update auto` | 기본값: 주 1회 확인 → 새 릴리스면 자동 전환 |
| `hla-sero config --auto-update notify` | 새 릴리스가 있다고 알리기만 함 |
| `hla-sero config --auto-update off` | 확인 안 함 |
| `hla-sero config --pin 3.65.0` | 이 릴리스로 고정 (검증한 버전 유지) |
| `hla-sero config --unpin` | 다시 최신 따라가기 |

- 릴리스마다 별도 폴더에 보관되고 덮어쓰지 않습니다 (`~/.local/share/hla-sero/releases/`).
- 인터넷이 끊겨도 저장된 릴리스로 계속 동작합니다.
- **임상 업무에 쓰려면**: 새 릴리스로 바뀌기 전에 검증하고 싶다면 `notify` + `--pin` 조합을 권합니다.

### 랩 정책 예외 (선택)

OPTN/UNOS 동등표 등 WMDA와 다르게 써야 하는 경우 `~/.config/hla-sero/overrides.csv`:

```
allele,equivalent,associated,broad,note
A*02:03,A203,,A2,UNOS listing
```

---

## 4. 코드를 고칠 때 (개발 루틴)

```bash
cd ~/projects/hla-serologic-converter
./setup.sh                                  # 개발 환경 + 테스트
# ... 코드 수정 ...
.venv/bin/python -m pytest -q               # 테스트
HLA_SERO_LIVE=1 .venv/bin/python -m pytest tests/test_live.py   # 실제 최신 릴리스로 검증
./install.sh                                # 설치된 앱에 반영
git add . && git commit -m "..." && git push
```

| 파일 | 역할 |
|---|---|
| `src/hla_sero/wmda.py` | WMDA 파일 읽기 |
| `src/hla_sero/engine.py` | 변환 규칙 (mapped/assumed/ambiguous 판정) |
| `src/hla_sero/imgt.py` | 다운로드·체크섬·업데이트 정책 |
| `src/hla_sero/cli.py` | `hla-sero` 명령 |
| `src/hla_sero/gui.py`, `web/index.html` | 붙여넣기 창 |
| `tests/` | 오프라인 테스트 + 실데이터 테스트 |

---

## 자주 막히는 곳

| 증상 | 해결 |
|---|---|
| `hla-sero: command not found` | 터미널 새로 열기. 그래도 안 되면 `pipx ensurepath` 후 다시 |
| 창에 `Data problem: cannot reach GitHub` | 첫 실행엔 인터넷 필요. 연결 후 **Check for update** |
| 메뉴에 아이콘이 안 보임 | `hla-sero install-launcher` 후 로그아웃/로그인 |
| 코드를 고쳤는데 앱에 반영 안 됨 | `./install.sh` 다시 실행 |
| `Permission denied (publickey)` (git push) | GitHub SSH 키 등록 확인 |
