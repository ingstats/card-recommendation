# backend/recommender.py

import pandas as pd

def recommend_cards(user_profile, card_df, top_k=5):
    """
    간단한 키워드 기반 카드 추천 함수 (예시 버전)
    """
    keywords = user_profile.get("keywords", [])
    if not keywords:
        return card_df.sample(top_k).to_dict(orient="records")

    matched_cards = card_df[card_df["Benefits"].apply(
        lambda x: any(keyword.lower() in str(x).lower() for keyword in keywords)
    )]

    if matched_cards.empty:
        return card_df.sample(top_k).to_dict(orient="records")

    return matched_cards.head(top_k).to_dict(orient="records")
