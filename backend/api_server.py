from flask import Flask, request, jsonify
from recommender import get_recommendations
from card_data_loader import load_card_data
from rag_retriever import get_card_rag_explanations
from gpt_summary_generator import summarize_recommendations

app = Flask(__name__)
card_df = load_card_data()

@app.route("/recommend_card", methods=["POST"])
def recommend_card():
    user_profile = request.json.get("user_profile", {})
    context = request.json.get("context", "")

    recommendations = get_recommendations(user_profile)
    rag_results = get_card_rag_explanations(context, top_k=3)

    enriched = []
    for rec in recommendations:
        match = card_df[card_df["Card Name"] == rec["card_name"]].iloc[0]
        explanation = f"{rec['card_name']}는 {context}에 적합하며, 주요 혜택은 {match['Benefits']}"
        enriched.append({
            "card_name": rec["card_name"],
            "corporate": match["Corporate Name"],
            "benefits": match["Benefits"],
            "image_url": match["Image URLs"],
            "score": rec["score"],
            "rag_explanation": explanation
        })

    summary = summarize_recommendations(context, enriched)

    return jsonify({
        "recommendations": enriched,
        "summary": summary
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
