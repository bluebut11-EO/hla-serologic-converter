# 실험실 Windows PC에서 쓰기 — hla-sero.exe

설치가 필요 없는 단독 실행 파일입니다. Python도, 관리자 권한도 필요 없습니다.
**현재 용도: 기존 결과의 교차 확인(참고용).** 이 도구의 결과로 검사 결과를 바꾸지 않습니다.

---

## 1. 내려받기

1. GitHub 레포 → 오른쪽 **Releases** → 최신 버전 (예: `v0.3.0`)
2. `hla-sero.exe` 와 `SHA256SUMS.txt` 둘 다 받기
3. **파일이 진짜인지 확인** — PowerShell에서:
   ```powershell
   Get-FileHash .\hla-sero.exe -Algorithm SHA256
   ```
   출력된 값이 `SHA256SUMS.txt` 안의 값과 같아야 합니다.
4. `문서\hla-sero\` 처럼 고정된 폴더로 옮기기
5. (선택) 우클릭 → **시작 화면에 고정** 또는 **바탕 화면에 바로 가기 만들기**

## 2. 실행

`hla-sero.exe` 더블클릭 → 검은 창(콘솔)이 뜨고, 잠시 뒤 브라우저에 변환 화면이 열립니다.

- **검은 창은 열어둔 채로** 사용하세요. 이 창이 변환 프로그램 본체입니다.
- 끝낼 때: 화면 오른쪽 위 **Quit**, 또는 검은 창 닫기.
- 첫 실행 때 GitHub에서 IMGT/HLA 데이터(약 2MB)를 받습니다.

> **"Windows의 PC 보호" 파란 창이 뜨면**: 서명되지 않은 프로그램이라 뜨는 경고입니다.
> IT에서 허용한 경우에만 **추가 정보 → 실행**. 백신이나 AppLocker가 막으면 IT에 아래 4번 정보를 전달하세요.

## 3. 교차 확인 하는 법

### 엑셀에서 바로

| Sample | Allele | 현재 혈청형 |
|---|---|---|
| SYN0001 | A*02:01 | A2 |
| SYN0001 | B*15:03 | B72 |

세 열을 선택해 복사(`Ctrl+C`) → 변환 화면에 붙여넣기 → **Convert** → **Cross-check** 탭.
한 줄에 여러 쌍을 써도 됩니다: `S1  A*02:01 A2  A*24:02 A24  B*15:03 B72`

### 결과 읽기

| Check | 의미 | 할 일 |
|---|---|---|
| `match` | 현재 혈청형 = 계산 결과 (associated 이름 `A203`도 인정) | — |
| `broad-match` | broad로 적혀 있음 (A24인데 A9) | split 수준으로 적어야 하는지 확인 |
| `mismatch` | 다름 (빨간 줄) | **검토** — 아래 기록 |
| (빈칸) | 현재 혈청형을 안 적음 | — |

`match`인데 상태가 `ambiguous`/`assumed`면 Note에 "review"가 붙습니다 — 계산 쪽이 확정적이지 않다는 뜻입니다.

### mismatch가 나오면

1. **Allele detail** 탭에서 근거(basis, HATS, note) 확인
2. 랩 기준(OPTN/UNOS 동등표 등)과 WMDA가 원래 다른 allele인지, 실제 오류인지 판단
3. 원래 다른 경우 → `%APPDATA%\hla-sero\overrides.csv`에 기록 (형식은 README 참고)
4. **Download CSV**로 결과 저장 — 파일 첫 줄에 IMGT/HLA 릴리스, 프로그램 버전, 생성 시각이 찍힙니다

## 4. IT에 전달할 정보

| 항목 | 내용 |
|---|---|
| 무엇 | HLA 분자형 → 혈청형 변환 참고 도구, 오픈소스 (github.com/bluebut11-EO/hla-serologic-converter) |
| 설치 | 없음. 단독 실행 파일, 관리자 권한 불필요 |
| 네트워크 | `raw.githubusercontent.com`에 HTTPS로 IMGT/HLA 공개 데이터 다운로드만 (주 1회 이하) |
| 환자 데이터 | 외부 전송 없음. 이 PC의 `127.0.0.1`(자기 자신)에서만 동작 |
| 저장 위치 | `%LOCALAPPDATA%\hla-sero` (데이터), `%APPDATA%\hla-sero` (설정) |
| 빌드 | GitHub Actions에서 공개적으로 빌드, 매 릴리스 SHA256 제공 |

## 5. 권장 설정 (교차 확인 기간)

화면 오른쪽 위:
- **Updates: notify** — 새 IMGT/HLA 릴리스가 나와도 자동으로 바꾸지 않고 알리기만
- **Pin this release** 체크 — 확인 작업 동안 같은 릴리스 유지

새 릴리스(1·4·7·10월)로 옮길 때는 검증 세트를 다시 돌려 비교한 뒤 Pin을 바꿉니다.
새 릴리스가 나오면 GitHub가 변경 목록과 함께 이메일로 알려줍니다 → `docs/EMAIL_ALERTS_KO.md`

## 6. 검증 세트 만들기

`docs/cross_check_template.csv`를 엑셀로 열어 **현재 혈청형** 열을 랩 기준으로 채우세요.
까다로운 allele(B*15, B*40, C*03, DRB1*14, null 등)을 미리 넣어두었습니다.
전부 붙여넣고 Cross-check 결과를 CSV로 저장 → 이것이 검증 기록의 출발점입니다.

## 문제 해결

| 증상 | 해결 |
|---|---|
| 브라우저가 안 열림 | 검은 창에 나온 `http://127.0.0.1:....` 주소를 브라우저에 직접 입력 |
| `cannot reach GitHub` | 첫 실행엔 인터넷 필요. 병원 프록시 문제면 IT에 `raw.githubusercontent.com` 허용 요청 |
| 실행이 차단됨 | IT에 4번 표 + SHA256 전달 |
| 결과가 이상함 | Allele detail 탭 화면을 캡처해서 확인 |
