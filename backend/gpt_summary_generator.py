import openai

openai.api_key = "YOUR_OPENAI_API_KEY"

def summarize_recommendations(user_text, recommendation_cards):
    cards_formatted = ""
    for card in recommendation_cards:
        cards_formatted += f"""
✅ {card['card_name']} ({card['corporate']})
- 주요 혜택: {card['benefits']}
- 추천 이유: {card['rag_explanation']}
- 카드 이미지: {card['image_url']}\n"""

    prompt = f"""[카드 추천 응답 요약 템플릿]

사용자 소비 문맥: "{user_text}"

추천 카드 목록:
{cards_formatted}

위 카드 목록을 바탕으로, 사용자가 이해하기 쉽게 자연어로 설명을 구성하세요. 각 카드에 대해 친절한 말투로 소개하고, 선택 이유를 부각하세요.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "너는 카드 추천 컨설턴트야."},
                  {"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]
