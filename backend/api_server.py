from flask import Flask, request, jsonify
from recommender import recommend_cards
from card_data_loader import load_card_data
from rag_retriever import retrieve_similar_card_descriptions
from gpt_summary_generator import generate_summary_with_model

app = Flask(__name__)
card_df = load_card_data()

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json

    user_profile = {
        "age": data.get("age"),
        "income": data.get("income"),
        "keywords": data.get("keywords", []),
    }
    context = data.get("context", "")

    # 카드 추천
    recommended_cards = recommend_cards(user_profile, card_df)

    # 추천 카드별 설명 생성
    recommendation_list = []
    for card in recommended_cards:
        rag_text = retrieve_similar_card_descriptions(card["Card Name"], card_df)
        summary = generate_summary_with_model(card["Card Name"], rag_text)

        recommendation_list.append({
            "Card Name": card["Card Name"],
            "Corporate Name": card["Corporate Name"],
            "Benefits": card["Benefits"],
            "image_url": card.get("Image URLs", ""),
            "summary": summary
        })

    # 전체 요약 텍스트
    overall_summary = f"{len(recommendation_list)}개의 카드를 추천해드렸습니다."

    return jsonify({
        "summary": overall_summary,
        "recommendations": recommendation_list
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
