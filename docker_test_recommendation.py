# test_recommendation.py
from card_recommendation import CardRecommendationRAG
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def main():
    # MySQL 설정
    mysql_config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "user": os.getenv("MYSQL_USER", "recommendation_team"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "card_recommendation")
    }
    
    print("CardRecommendationRAG 시스템 테스트 시작...")
    # 추천 시스템 초기화
    rec_system = CardRecommendationRAG(mysql_config)
    
    # 테스트할 사용자 ID와 질문
    test_user_id = "user1"  # 테이블에 실제로 존재하는 사용자 ID
    test_query = "카페와 쇼핑할 때 혜택이 좋은 카드 추천해주세요"
    
    # 사용자 프로필 정보 확인
    user_profile = rec_system.get_user_profile(test_user_id)
    print(f"\n사용자 프로필: {user_profile}")
    
    # 추천 결과 생성
    print(f"\n질문: {test_query}")
    print("\n추천 결과 생성 중...")
    response = rec_system.process_user_query(test_user_id, test_query)
    
    print("\n=== 추천 결과 ===")
    print(response)
    print("================")

if __name__ == "__main__":
    main()
