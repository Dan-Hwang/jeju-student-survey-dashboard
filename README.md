# Jeju Exchange Student Survey Dashboard

제주대학교 교류학생 생활 플랫폼 수요조사 결과를 외부에 공유하기 위한 Streamlit 공개 대시보드입니다.

이 앱은 Google Form 응답이 연결된 Google Sheets를 읽어 응답 수, 주요 불편, 오픈채팅 이용 목적, 서비스 사용 의향을 집계해서 보여줍니다. Google Sheets 연결이 실패하면 저장된 CSV 파일을 기준으로 화면을 표시합니다.

## 주요 기능

- Google Form 응답 기반 공개 수요조사 대시보드
- 응답 수, 핵심 불편, 오픈채팅 탐색 항목, 서비스 사용 의향 요약
- 개별 응답 row를 노출하지 않는 집계형 화면
- Google Sheets 연결 실패 시 CSV fallback 표시
- 설문 결과 PDF/PNG 다운로드

## 실행 방법

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

로컬 실행 주소:

```text
http://127.0.0.1:8501
```

## Google Sheets 설정

로컬에서는 아래 파일이 있으면 Google Sheets 응답을 직접 읽습니다.

```text
secrets/google-service-account.json
```

이 파일은 인증키이므로 GitHub, 카카오톡, 공개 저장소에 올리지 않습니다.

Streamlit Cloud 같은 배포 환경에서는 저장소에 JSON 파일을 넣지 말고 Secrets에 아래 값을 등록합니다.

```toml
ARA_SURVEY_SPREADSHEET = "https://docs.google.com/spreadsheets/d/136GDfjr_qUIxsWfWqGOr8CZ392IAcAgVOyCH2eBXQdE/edit"
GOOGLE_SERVICE_ACCOUNT_JSON = "{서비스 계정 JSON 전체 내용}"
```

Google Sheets는 서비스 계정 JSON 안의 `client_email`에 보기 권한으로 공유되어 있어야 합니다.

## 파일 구조

```text
ara-guide/
├── app.py
├── requirements.txt
├── src/
│   └── survey_dashboard.py
├── scripts/
│   ├── make_survey_report_auto.py
│   └── run_survey_report_from_sheets.ps1
├── data/
│   └── responses/
├── output/
│   └── reports/
└── docs/
    └── survey-report-automation.md
```

## 배포 전 확인

1. `secrets/google-service-account.json`이 Git에 포함되지 않았는지 확인합니다.
2. Streamlit Secrets에 서비스 계정 JSON을 등록합니다.
3. Google Sheets가 서비스 계정 이메일에 공유되어 있는지 확인합니다.
4. 앱 첫 화면에서 수요조사 결과만 표시되는지 확인합니다.
