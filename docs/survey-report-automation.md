# 설문 리포트 자동화

Google Form 응답을 팀원 공유용 리포트로 자동 변환하는 방법이다.

## 권장 구조

Google Form 자체를 직접 읽기보다, Form 응답을 Google Sheets에 연결한 뒤 Sheets API로 읽는다.

```text
Google Form 응답
-> Google Sheets에 자동 저장
-> scripts/make_survey_report_auto.py가 Sheets API로 읽기
-> PDF/PNG 리포트 생성
```

## 1. 빠른 테스트: CSV 사용

Google Form 응답 화면에서 `응답 다운로드(.csv)`를 받은 뒤 실행한다.

```powershell
python scripts/make_survey_report_auto.py --csv data/student_survey_sample.csv
```

생성 파일:

- `output/reports/student-survey-auto-report.pdf`
- `output/reports/student-survey-auto-report.png`

## 2. 완전 자동: Google Sheets API 사용

1. Google Form의 응답을 Google Sheets에 연결한다.
2. Google Cloud에서 Sheets API를 활성화한다.
3. 서비스 계정을 만들고 JSON 키를 내려받는다.
4. 연결된 Google Sheets를 서비스 계정 이메일에 공유한다.
5. 아래처럼 실행한다.

```powershell
.\scripts\run_survey_report_from_sheets.ps1 `
  -Spreadsheet "구글시트_URL_또는_ID" `
  -Credentials "secrets\google-service-account.json"
```

응답 시트의 첫 번째 탭을 자동으로 읽는다. 다른 탭을 읽어야 할 때만 `-Range "'다른 탭 이름'!A:Z"`를 추가한다.

`credentials.json`은 인증 파일이므로 Git에 올리지 않는다.

성공하면 아래 파일이 생성된다.

- `output/reports/student-survey-live-report.pdf`
- `output/reports/student-survey-live-report.png`

## 해야 하는 Google 설정

1. Google Form 응답 탭에서 스프레드시트 아이콘을 눌러 응답 Sheet를 만든다.
2. Google Cloud Console에서 새 프로젝트를 만든다.
3. `Google Sheets API`를 활성화한다.
4. 서비스 계정을 만든다.
5. 서비스 계정 키를 JSON으로 내려받는다.
6. 파일 이름을 `google-service-account.json`으로 바꾸고 `secrets/` 폴더에 넣는다.
7. JSON 안의 `client_email` 값을 복사한다.
8. Google Sheets에서 공유 버튼을 눌러 그 이메일에 보기 권한을 준다.

## 필요한 입력

- CSV 방식: Google Form 응답 CSV 파일
- Sheets API 방식: 스프레드시트 URL 또는 ID, 서비스 계정 JSON 파일

## 현재 자동 집계하는 항목

- 응답 수
- 4주 이상 체류 응답 수
- 불편했던 점
- 같이 하고 싶은 활동
- 오픈채팅에서 많이 찾는 것
- 오픈채팅에서 불편한 점
- 서비스 사용 의향을 긍정/중립/부정으로 재분류

질문 문구가 조금 달라져도 키워드로 컬럼을 찾도록 구성했다.
