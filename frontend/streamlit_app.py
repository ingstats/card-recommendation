import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="카드 추천 챗봇", layout="wide")

st.title("💳 ChatGPT 기반 카드 추천 시스템")
st.markdown("사용자의 소비 패턴에 맞춰 최적의 카드를 추천해드립니다.")

with st.form("user_input_form"):
    age = st.number_input("나이", min_value=10, max_value=100, value=30)
    income_level = st.selectbox("소득 수준", ["낮음", "중간", "높음"])
    recent_spending = st.multiselect(
        "최근 소비 패턴 키워드",
        ["커피", "편의점", "택시", "온라인쇼핑", "주유", "영화", "통신", "여행"]
    )
    context = st.text_input("추천 문맥(자유입력)", value="커피, 편의점 중심 소비 패턴")

    submitted = st.form_submit_button("카드 추천받기")

if submitted:
    user_profile = {
        "age": age,
        "income_level": income_level,
        "recent_spending": recent_spending
    }

    with st.spinner("카드 추천 중..."):
        response = requests.post("http://localhost:8000/recommend_card", json={
            "user_profile": user_profile,
            "context": context
        })

    if response.status_code == 200:
        result = response.json()
        st.subheader("📋 요약 결과")
        st.write(result["summary"])

        st.subheader("📌 카드 추천 상세")
        for card in result["recommendations"]:
            st.markdown(f"### {card['card_name']} ({card['corporate']})")
            st.image(card["image_url"], width=200)
            st.markdown(f"**혜택 요약:** {card['benefits']}")
            st.markdown(f"**추천 이유 (RAG):** {card['rag_explanation']}")
            st.markdown("---")
    else:
        st.error("추천 서버 오류 발생")
