# 💳 카드 추천 시스템 (Docker + RAG + OpenAI)

이 프로젝트는 Docker 환경에서 실행되는 개인화된 신용카드 추천 시스템입니다. RAG(Retrieval-Augmented Generation) 기술과 OpenAI GPT를 활용하여 사용자의 소비 패턴에 맞는 카드를 추천하고 자연스러운 설명을 제공합니다.

## 🚀 주요 기능

- ✅ Docker 기반 MySQL 환경으로 간편한 설정
- ✅ 소비 패턴 기반 개인화된 카드 추천 알고리즘
- ✅ SentenceTransformer 기반 의미론적 카드 검색
- ✅ OpenAI GPT를 활용한 자연어 설명 생성
- ✅ 확장 가능한 모듈식 아키텍처

## 🔧 시스템 구성 요소

### 데이터베이스
- MySQL 8.0 Docker 컨테이너
- 카드 정보, 사용자 프로필, 소비 패턴, 추천 결과 저장

### 백엔드
- Python 기반 RAG 엔진
- 의미론적 검색을 위한 SentenceTransformer
- OpenAI GPT 통합 API

## 📋 설치 및 실행 방법

### 필수 요구사항
- Docker Desktop
- Python 3.7 이상
- pip (Python 패키지 관리자)

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/card-recommendation-system.git
cd card-recommendation-system
```

### 2. 환경 설정
```bash
# 환경 변수 파일 생성
cp .env.example .env
# .env 파일을 열어 데이터베이스 및 API 키 정보 입력
```

### 3. 가상환경 설정 (권장)
```bash
python -m venv card_env
source card_env/bin/activate  # Mac/Linux
# 또는
card_env\Scripts\activate  # Windows
```

### 4. 패키지 설치
```bash
pip install -r requirements.txt
```

### 5. Docker 환경 실행
```bash
# Docker Desktop 실행 확인
docker-compose up -d
```

### 6. 데이터베이스 설정 및 데이터 로드
```bash
# Mac/Linux
chmod +x scripts/setup_mysql.sh
./scripts/setup_mysql.sh

# Windows
bash scripts/setup_mysql.sh

# 카드 데이터 로드
python scripts/card_data_tosql.py
```

### 7. 테스트 실행
```bash
python docker_test_recommendation.py
```

## 📊 시스템 동작 예시

**입력 예시:**
- 사용자 ID: user1
- 질문: "카페와 쇼핑할 때 혜택이 좋은 카드 추천해주세요"

**출력 예시:**
```
=== 추천 결과 ===
사용자님의 소비 패턴을 고려하여 카드를 추천해 드립니다.

### 1. 추천 카드:
- 카드명: 청춘대로 톡톡카드
- 카드사: KB국민카드
- 추천 이유: 귀하의 주요 소비 습관 중 카페 방문이 많고, 이 카드는 카페와 디저트 혜택이 강점입니다.
- 주요 혜택:
  * 카페/디저트: 스타벅스 50% 청구할인
  * 패스트푸드: 버거/패스트푸드 업종 20% 청구할인
  ...
```

## 🔄 프로젝트 구조

```
card-recommendation-system/
├── docker-compose.yml         # Docker MySQL 컨테이너 설정
├── card_recommendation.py     # 핵심 추천 시스템 로직
├── docker_test_recommendation.py # 테스트 실행 스크립트
├── scripts/
│   ├── setup_mysql.sh         # MySQL 테이블 스키마 설정
│   └── card_data_tosql.py     # 카드 데이터 로드 스크립트
└── data/
    └── card_data_updated.xlsx # 카드 정보 엑셀 파일
```

## 🤝 기여 방법

1. 이 저장소를 포크합니다.
2. 새 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치를 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.

## 📜 라이센스

이 프로젝트는 MIT 라이센스에 따라 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📬 문의

- 개발자: @ingstats
