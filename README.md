```markdown
# 💳 카드 추천 시스템 (RAG + GPT 요약 + Streamlit UI)

이 프로젝트는 각 사용자마다 최적의 신용카드를 추천하고, RAG 기반 설명 생성과 GPT 요약을 통해 자연스러운 카드 추천 응답을 생성하는 AI 기반 시스템입니다.

---

## 📦 주요 기능

- ✅ 카드 소비 패턴 기반 딥러닝 추천 모델 연동 가능
- ✅ RAG (FAISS + SentenceTransformer) 기반 카드 설명 검색
- ✅ GPT 프롬프트 템플릿 기반 자연어 요약 응답 생성
- ✅ Streamlit UI로 손쉽게 테스트 가능

---

## 📁 디렉토리 구조

```text
card-recommendation/
├── backend/
│   ├── api_server.py              # 추천 + RAG + GPT 요약 API 서버
│   ├── build_faiss_index.py      # FAISS 인덱스 구축 스크립트
│   ├── card_data_loader.py       # 카드 CSV 로드 유틸리티
│   ├── gpt_summary_generator.py  # GPT 요약 템플릿 생성기
│   ├── rag_retriever.py          # FAISS 기반 카드 설명 검색기
│   ├── recommender.py            # 카드 추천 로직 (딥러닝 or 규칙 기반)
│   └── data/
│       └── card_data.csv         # 카드 정보 CSV
│
├── frontend/
│   └── streamlit_app.py          # 💻 Streamlit 사용자 인터페이스
│
├── gpt_function_calling/
│   └── assistant_client.py       # GPT API 연동 Function Calling
│
├── index/
│   ├── card_embeddings.pkl       # 카드 설명 임베딩 저장
│   └── faiss_index.bin           # FAISS 인덱스 파일
│
├── requirements.txt              # 필수 패키지 목록
├── CONTRIBUTING.md               # Git 협업 가이드
└── README.md                     # 프로젝트 설명 문서
```

---

## ⚙️ 설치 및 실행 방법

### 1. 설치
```bash
git clone https://github.com/ingstats/card-recommendation.git
cd card-recommendation
pip install -r requirements.txt
```

### 2. FAISS 인덱스 생성 (최초 1회만 실행)
```bash
python backend/build_faiss_index.py
```

### 3. API 서버 실행
```bash
python backend/api_server.py
```

### 4. Streamlit UI 실행
```bash
streamlit run frontend/streamlit_app.py
```

---

## 📊 Streamlit UI 입력 예시

- 나이: 30세  
- 소득수준: 중간  
- 소비 키워드: 편의점, 커피, 택시  
- 문맥 설명: "편의점과 커피를 자주 사용하는 사용자입니다."

---

## 📜 사용 기술/모델

- Sentence-BERT: `paraphrase-multilingual-MiniLM-L12-v2`
- FAISS 인덱싱 (유사 카드 설명 검색)
- OpenAI GPT-4 API (Function Calling + 자연어 요약)
- Streamlit 프론트엔드

---

## ✅ 시스템 아키텍처 흐름 요약

```text
사용자 (Streamlit UI)
     ↓
Flask API 서버
     ├─ 추천 모델 → 카드 추천
     ├─ RAG Retriever → 카드 설명 검색
     └─ GPT → 자연어 요약 응답
     ↓
Streamlit에 추천 카드 + 요약 결과 표시
```

---

## 📄 requirements.txt

```text
flask
streamlit
openai
requests
pandas
faiss-cpu
sentence-transformers
```

---

## ✍️ 라이선스

MIT License

---

## 📬 문의

- 개발자: @ingstats
```