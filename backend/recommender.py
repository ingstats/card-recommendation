import random

def get_recommendations(user_profile, top_k=3):
    dummy_cards = [
        {"card_name": "삼성카드 taptap O", "score": 0.92},
        {"card_name": "스타벅스캐시백카드", "score": 0.90},
        {"card_name": "현대카드 M", "score": 0.88},
    ]
    return dummy_cards[:top_k]