# docker_test_recommendation.py
from card_recommendation import CardRecommendationRAG
import os
from dotenv import load_dotenv
import traceback

# 환경 변수 로드
load_dotenv()

def main():
    # MySQL 설정
    mysql_config = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3307")),
        "user": os.getenv("MYSQL_USER", "recommendation_team"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "card_recommendation")
    }

    print("LangChain 기반 CardRecommendationRAG 시스템 테스트 시작...")
    
    try:
        # 추천 시스템 초기화
        rec_system = CardRecommendationRAG(mysql_config)
        
        # 테스트할 사용자 ID와 질문
        test_user_id = "user1"  # 테이블에 실제로 존재하는 사용자 ID
        test_query = "카페와 쇼핑할 때 혜택이 좋은 카드 추천해주세요"
        
        # 사용자 프로필 정보 확인
        user_profile = rec_system.get_user_profile(test_user_id)
        print(f"\n사용자 프로필: {user_profile}")
        
        # retriever가 없는 경우 추가 디버깅 정보 출력
        if not hasattr(rec_system, 'retriever') or rec_system.retriever is None:
            print("\n주의: retriever가 초기화되지 않았습니다. Vector Store 상태 확인:")
            print(f"Vector Store 존재 여부: {hasattr(rec_system, 'vector_store') and rec_system.vector_store is not None}")
            print(f"카드 문서 개수: {len(rec_system.card_documents) if hasattr(rec_system, 'card_documents') else 0}")
        
        # 추천 결과 생성
        print(f"\n질문: {test_query}")
        print("\n추천 결과 생성 중...")
        
        try:
            response = rec_system.process_user_query(test_user_id, test_query)
            
            print("\n=== 추천 결과 ===")
            print(response)
            print("================")
        except Exception as e:
            print(f"\n추천 결과 생성 중 오류 발생: {str(e)}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"\n시스템 초기화 중 오류 발생: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()