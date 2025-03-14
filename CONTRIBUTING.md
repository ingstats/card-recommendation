# 💳 Card Recommendation System - Git 협업 가이드

> 본 문서는 `https://github.com/ingstats/card-recommendation` 프로젝트의 팀원 협업을 원활하게 진행하기 위한 Git 사용 규칙, 브랜치 전략, 커밋 메시지, PR 규칙, 코드리뷰 방식 등을 정리한 문서입니다.

---

## ✅ 1. Git 브랜치 전략 (Branching Strategy)

| 브랜치 | 목적 |
|--------|--------------------------------------------------|
| `main` | **운영 배포 브랜치** - 항상 안정적인 상태 유지 |
| `dev` | **기능 통합 브랜치** - 모든 기능은 dev에 병합 후 main으로 |
| `feature/*` | 새로운 기능 개발 시 사용하는 브랜치 |
| `hotfix/*` | 운영 중 긴급 수정사항 처리용 브랜치 |
| `test/*` | 성능평가, 벤치마크 실험 등을 위한 테스트 브랜치 |

### 📌 브랜치 예시
- `feature/rag-engine`: RAG 설명 생성기 개발
- `feature/gpt-summary`: GPT 요약 템플릿 개선
- `feature/streamlit-ui`: Streamlit UI 구축
- `hotfix/api-error`: API 긴급 수정
- `test/model-evaluation`: 모델 벤치마킹 테스트

---

## ✅ 2. 브랜치 생성 및 Push 방식

```bash
# 새 브랜치 생성
git checkout -b feature/rag-engine

# 작업 후 커밋
git add .
git commit -m "feat: RAG 설명 생성기 구현"

# 원격 저장소로 Push
git push -u origin feature/rag-engine
```

---

## ✅ 3. 커밋 메시지 규칙

| 태그 | 의미 |
|------|-----------------------------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 (README, 주석 등) |
| `style` | 코드 포맷팅, 세미콜론 등 비기능 변경 |
| `refactor` | 코드 리팩토링 (기능변화 없음) |
| `test` | 테스트 코드 추가 |
| `chore` | 빌드 설정, 패키지 업데이트 등 기타 |

### 📌 커밋 메시지 예시
```
feat: GPT 요약 템플릿 추가
fix: 추천 모델 오류 수정
refactor: card_loader 함수 분리
docs: README 실행방법 추가
```

---

## ✅ 4. Pull Request (PR) 규칙

- **PR 대상**: 항상 `dev` 브랜치 기준
- **제목**: `[feat] Streamlit UI 구성`, `[fix] API 에러 처리`
- **본문 내용 포함 항목**:
  - 변경 내용 요약
  - 영향 범위
  - 테스트 방식 또는 확인 방법

### 📌 PR 생성 예시
```
제목: [feat] Streamlit 사용자 인터페이스 구축

- Streamlit을 이용해 사용자 UI를 구성
- Flask API와 통신하여 카드 추천 결과 표시
- benefits 출력 형식 수정
```

---

## ✅ 5. 코드 리뷰 가이드

- 최소 **1인 이상의 승인** 후 dev 브랜치 병합
- 리뷰자는 **기능 이해도와 가독성** 중심으로 확인
- 리뷰 시 GitHub 코멘트 기능 적극 활용

### 📌 리뷰 항목 체크리스트
- [ ] 코드가 기능에 맞게 작성되었는가?
- [ ] 하드코딩 없이 모듈화 되어 있는가?
- [ ] 예외처리 및 로그처리가 적절한가?
- [ ] 테스트 코드가 포함되어 있는가?

---

## ✅ 6. 팀원 협업 워크플로우

```
1. feature/ 브랜치 생성 후 작업
2. dev 브랜치로 Pull Request 생성
3. 코드 리뷰 → 승인 → dev 병합
4. 주기적으로 main 브랜치로 릴리즈 병합
```

---

## ✅ 7. Git 사용시 주의사항

- 절대 `main`에서 직접 작업하지 마세요.
- 작업 전 항상 `pull`로 최신 상태 유지하세요.
- 커밋은 **작고 명확하게**, 의미있는 단위로 나누세요.
- 코드 커밋 전 **로컬 테스트** 필수입니다.

---

## ✅ 8. 권장 툴/환경

- Git + GitHub Desktop 또는 CLI
- Visual Studio Code
- Python 3.10+
- 가상환경(venv 또는 conda) 사용 권장

---

## ✅ 9. 예시 브랜치 생성 스크립트 (선택사항)

```bash
git checkout -b feature/streamlit-ui
git push -u origin feature/streamlit-ui

git checkout -b feature/rag-engine
git push -u origin feature/rag-engine

git checkout -b feature/gpt-summary
git push -u origin feature/gpt-summary
```

---

## 📬 문의

- 프로젝트 오너: `@ingstats`
- 이메일: ingstats@example.com