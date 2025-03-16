import streamlit as st
import requests

# 페이지 설정
st.set_page_config(page_title="카드 추천 챗봇", layout="wide")

# 타이틀
st.title("💬 카드 추천 챗봇")
st.markdown("**당신의 소비 패턴에 맞는 카드를 추천해드릴게요!**")

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 사용자 입력 form
with st.form("chat_input_form", clear_on_submit=True):
    user_input = st.text_input("👤 사용자 질문을 입력하세요", "")
    submitted = st.form_submit_button("💬 전송")

# 사용자 입력 처리
if submitted and user_input:
    # 사용자 입력 저장
    st.session_state.chat_history.append(("user", user_input))

    # 예시 기본 파라미터
    age = 30
    income_level = "중간"
    recent_spending = []
    context = user_input

    try:
        # API 호출
        with st.spinner("🤖 추천 중..."):
            response = requests.post("http://localhost:5000/recommend", json={
                "age": age,
                "income": income_level,
                "keywords": recent_spending,
                "context": context
            })

        if response.status_code == 200:
            result = response.json()
            recommendations = result.get("recommendations", [])
            summary_text = result.get("summary", "")

            if not recommendations:
                st.session_state.chat_history.append(("bot", "😥 추천 결과가 없습니다. 다른 키워드를 시도해보세요."))
            else:
                # 요약 메시지 우선 출력
                summary_msg = f"🎯 {summary_text if summary_text else f'총 {len(recommendations)}개의 카드를 추천드립니다!'}"
                st.session_state.chat_history.append(("bot", summary_msg))

                # 카드별 상세 응답
                for card in recommendations:
                    if isinstance(card, dict):
                        card_name = card.get("Card Name", "카드명 없음")
                        corporate = card.get("Corporate Name", "카드사 정보 없음")
                        benefits = card.get("Benefits", "혜택 정보 없음")
                        summary = card.get("summary", "추천 이유 없음")
                        image_url = card.get("image_url", None)

                        # 혜택 줄바꿈 처리
                        formatted_benefits = "\n".join([f"- {b.strip()}" for b in benefits.split(';') if b.strip()])

                        # 요약 fallback 처리
                        if summary.lower().startswith("요약 정보를 불러오지 못했습니다") or "index out of range" in summary.lower():
                            summary = "이 카드는 고객님의 소비 성향에 가장 잘 맞는 혜택을 제공합니다."

                        # 카드 정보 출력 블록
                        with st.container():
                            st.markdown(f"### 💳 {card_name} ({corporate})")
                            cols = st.columns([1, 3])
                            with cols[0]:
                                if image_url:
                                    st.image(image_url, width=180)
                            with cols[1]:
                                st.markdown("**📌 혜택 요약:**")
                                st.markdown(formatted_benefits)
                                st.markdown("**📌 추천 이유:**")
                                st.markdown(summary)
                                st.markdown("---")
                    else:
                        st.session_state.chat_history.append(("bot", "❌ 추천 카드 형식 오류 (dict가 아닙니다)"))

        else:
            st.session_state.chat_history.append(("bot", f"❌ 추천 서버 오류 (status code: {response.status_code})"))

    except requests.exceptions.ConnectionError:
        st.session_state.chat_history.append(("bot", "❌ 서버 연결 실패: API 서버를 먼저 실행해주세요."))

# 이전 채팅 내역 출력
st.markdown("---")
for sender, msg in st.session_state.chat_history:
    if sender == "user":
        st.markdown(f"🧑‍💼 **사용자:** {msg}")
    else:
        st.markdown(f"🤖 **추천봇:** {msg}")
