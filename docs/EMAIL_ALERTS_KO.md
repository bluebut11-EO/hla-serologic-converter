# IMGT/HLA 새 릴리스 이메일 알림

GitHub가 **매주 월요일 오전**에 공식 IMGT/HLA 저장소를 확인합니다.

| 상황 | 일어나는 일 | 이메일 |
|---|---|---|
| 새 릴리스 발견 | Issue 1개 생성: 이전 릴리스 대비 **혈청형이 바뀐 allele 목록** | ✅ |
| 새 릴리스에서 hla-sero 검사 실패 | ⚠️ 경고 Issue + 실패한 실행 | ✅ (2통) |
| 변화 없음 | 아무 일 없음 | — |

같은 릴리스로 Issue가 두 번 생기지 않습니다. IMGT/HLA는 1·4·7·10월에 릴리스하므로 1년에 4통 정도 옵니다.

---

## 1. 켜기 (한 번만)

이 기능이 들어간 PR을 **main에 병합**하면 자동으로 켜집니다. 예약 실행은 main 브랜치에서만 돌아갑니다.

## 2. 지금 바로 시험해보기

1. GitHub 레포 → **Actions** 탭
2. 왼쪽 목록에서 **IMGT/HLA watch** 선택
3. 오른쪽 **Run workflow** → **Run workflow**
4. 2~3분 뒤 ✅ 초록색이 되면 **Issues** 탭 확인 → `IMGT/HLA 3.65.0 released: ...` Issue가 생겨 있어야 합니다
5. 이메일함 확인 (`notifications@github.com`에서 발송)

> 첫 실행에서는 현재 최신 릴리스가 "새 릴리스"로 보고됩니다. 이후로는 정말 새 릴리스가 나왔을 때만 Issue가 생깁니다.

## 3. 이메일이 안 오면: GitHub 알림 설정

**github.com/settings/notifications** (메뉴 이름은 GitHub 화면에 따라 조금 다를 수 있습니다)

| 항목 | 설정 |
|---|---|
| Default notifications email | 받을 이메일 주소 확인 |
| **Watching** | **Email** 체크 → 새 Issue 알림 |
| **Actions** (System 아래) | **Email** 체크 + **Only notify for failed workflows** → 실패 알림 |

그리고 레포 페이지 오른쪽 위 **Watch** 버튼이 "Watching"(또는 All Activity) 상태인지 확인하세요. 직접 만든 레포는 보통 자동으로 Watching입니다.

Gmail이라면 **프로모션/소셜** 탭이나 스팸함도 확인하세요. 필터를 만들어두면 편합니다:
보낸사람 `notifications@github.com` + 제목 `IMGT/HLA` → 라벨 "IMGT 알림", 별표.

## 4. 알림이 왔을 때 할 일

1. Issue 열기 → **Changed** 표 확인
   - 예: `DQB1*02:273 | DQ2 (mapped) | DQ2 (assumed)` — 혈청형은 같아도 **근거가 약해짐**
   - 예: `B*xx:xx | B62 (mapped) | B63 (mapped)` — **혈청형 자체가 바뀜**, 반드시 검토
2. ✅ passed인지 확인 (❌면 실험실 PC를 새 릴리스로 옮기지 말 것)
3. 검증 세트(`docs/cross_check_template.csv`)를 새 릴리스로 돌려 CSV 저장
   ```bash
   hla-sero diff 3.65.0 3.66.0           # 내 컴퓨터에서 같은 비교 보기
   ```
4. 문제없으면 실험실 PC에서 **Pin this release**를 새 릴리스로 변경
5. Issue에 "검토 완료 + 날짜" 댓글 → **Close issue** (이게 변경 관리 기록이 됩니다)

## 5. 알아둘 것

- **60일 규칙:** GitHub는 공개 레포에서 60일간 활동이 없으면 예약 실행을 끕니다. 매주 실행 때 스스로 다시 켜도록 해두었지만, 혹시 꺼지면 Actions 탭 → IMGT/HLA watch → **Enable workflow**를 누르면 됩니다.
- GitHub가 바쁠 때는 예약 실행이 몇 분~몇 시간 늦어질 수 있습니다.
- 이 알림은 GitHub에서만 돌아갑니다. 실험실 PC 쪽 데이터 전환은 여전히 화면의 Updates/Pin 설정을 따릅니다.
