아래는 `codebuddy-agent` 저장소에 맞게 작성된 `README.md`입니다.

---

```markdown
# 🤖 CodeBuddy Agent

> AI 기반 GitHub Pull Request 자동 리뷰 시스템

CodeBuddy Agent는 AI를 활용하여 GitHub Pull Request를 자동으로 분석하고,
버그·보안 취약점·코드 스타일 위반을 탐지하며, 리팩토링 제안과 단위 테스트까지
자동 생성해주는 개발자 생산성 도구입니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 **자동 코드 리뷰** | PR이 열리면 Python · JavaScript · Java 코드를 자동 분석 |
| 🔴 **버그 & 보안 탐지** | 심각도(높음/중간/낮음)와 함께 버그 및 보안 취약점 보고 |
| 📊 **복잡도 분석** | 순환 복잡도(Cyclomatic Complexity) 측정으로 리팩토링 우선순위 제시 |
| 🛠️ **리팩토링 제안** | 가독성·성능·유지보수성 관점의 구체적인 코드 개선안 제공 |
| 🧪 **단위 테스트 생성** | pytest 기반 테스트 코드 자동 생성 (정상·경계·예외 케이스 포함) |
| 💬 **PR 자동 댓글** | 분석 결과를 GitHub PR 댓글로 자동 등록 |
| 🔔 **Slack 알림** | 리뷰 완료 시 팀 Slack 채널에 즉시 알림 전송 |

---

## 🚀 설치 방법

### 요구 사항

- Python 3.10 이상
- GitHub Personal Access Token (repo 권한)
- Slack Webhook URL (알림 사용 시)

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/codebuddy-agent.git
cd codebuddy-agent
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 아래 값을 입력하세요:

```dotenv
GITHUB_TOKEN=ghp_your_personal_access_token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
OPENAI_API_KEY=sk-your_openai_api_key   # AI 분석 사용 시
```

### 4. 실행

```bash
python main.py
```

---

## 📖 사용 예시

### PR 자동 리뷰 요청

```python
from codebuddy import CodeBuddyAgent

agent = CodeBuddyAgent()

# GitHub PR 분석 및 댓글 자동 등록
agent.review_pr(
    owner="your-org",
    repo="your-repo",
    pr_number=42
)
```

### 복잡도 분석

```python
with open("my_module.py", "r") as f:
    code = f.read()

result = agent.<REDACTED>(code)
print(result)
# 출력 예시:
# process_order      → 복잡도: 12 (⚠️ 리팩토링 권장)
# calculate_discount → 복잡도: 3  (✅ 양호)
```

### 단위 테스트 생성

```python
result = agent.<REDACTED>(
    code=code,
    function_name="calculate_discount"
)
print(result)
# → pytest 테스트 코드 자동 출력
```

### Slack 알림 전송

```python
agent.<REDACTED>(
    message="✅ PR #42 코드 리뷰 완료! 3개의 이슈가 발견되었습니다.",
    status="success"
)
```

---

## 📋 리뷰 출력 형식

```
🔴 높은 심각도
[Line 34] 문제: SQL 쿼리에 사용자 입력값이 직접 삽입되어 SQL Injection 위험
수정 제안:
  cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

🟡 중간 심각도
[Line 78] 문제: 함수 복잡도 12 초과 — 단일 책임 원칙 위반
수정 제안: 로직을 validate_input(), process_data()로 분리

🟢 낮은 심각도
[Line 12] 문제: 변수명 'x'는 의미를 알기 어려움
수정 제안: 'total_price'와 같이 명확한 이름 사용
```

---

## 🗂️ 프로젝트 구조

```
codebuddy-agent/
├── main.py                 # 진입점
├── codebuddy/
│   ├── agent.py            # 핵심 에이전트 로직
│   ├── tools/
│   │   ├── github.py       # PR 조회 & 댓글 등록
│   │   ├── complexity.py   # 복잡도 분석
│   │   ├── test_gen.py     # 테스트 코드 생성
│   │   ├── refactor.py     # 리팩토링 제안
│   │   └── slack.py        # Slack 알림
│   └── prompts/            # AI 프롬프트 템플릿
├── tests/                  # 자체 테스트 코드
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🤝 기여 방법

1. 이 저장소를 Fork합니다.
2. 새 브랜치를 생성합니다: `git checkout -b feat/amazing-feature`
3. 변경 사항을 커밋합니다: `git commit -m "feat: Add amazing feature"`
4. 브랜치에 Push합니다: `git push origin feat/amazing-feature`
5. Pull Request를 열어주세요.

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

```
MIT License

Copyright (c) 2025 CodeBuddy Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
```

---

<p align="center">
  Made with ❤️ by the CodeBuddy Team
</p>
```

---

### 📌 커스터마이징 체크리스트

README를 저장소에 적용하기 전에 아래 항목을 실제 값으로 교체하세요:

- [ ] `your-org` → 실제 GitHub 조직/유저명
- [ ] `your-repo` → 실제 저장소명
- [ ] `OPENAI_API_KEY` 항목 → 사용하는 AI 공급자에 맞게 수정
- [ ] 프로젝트 구조 → 실제 디렉터리 구조 반영
- [ ] 라이선스 연도 및 저작권자 수정