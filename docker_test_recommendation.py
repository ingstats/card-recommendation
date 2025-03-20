#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
트랜잭션 데이터셋을 활용한 카드 추천 시스템 테스트 스크립트.
이 스크립트는 SEQ 기반 사용자 ID를 사용하는 시스템의 작동 방식을 보여줍니다.
"""

from card_recommendation import CardRecommendationRAG
import os
from dotenv import load_dotenv
import traceback
import pandas as pd

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

    print("트랜잭션 데이터를 활용한 LangChain 기반 카드 추천 시스템 테스트 시작...")
    
    try:
        # 추천 시스템 초기화
        rec_system = CardRecommendationRAG(mysql_config)
        
        # 트랜잭션 데이터에서 사용자 ID 샘플 가져오기 (최대 5개)
        try:
            # 데이터베이스에서 사용자 ID 조회 시도
            connection = mysql_config.copy()
            import mysql.connector
            conn = mysql.connector.connect(**connection)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT seq_id FROM user_transactions LIMIT 5")
            user_ids = [row['seq_id'] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        except Exception as e:
            # 데이터베이스 조회 실패 시 파일에서 직접 읽기
            print(f"데이터베이스 조회 실패, 파일에서 직접 읽기: {e}")
            try:
                df = pd.read_csv("paste.txt", delimiter='\t')
                user_ids = df['SEQ'].tolist()[:5]
            except Exception as e2:
                print(f"트랜잭션 데이터 파일 읽기 오류: {e2}")
                user_ids = ["0003UZ715F1AVTCFVTLJ", "000FQ6EU9C0VJG9ECRUV"]  # 기본 예시 ID
        
        # 테스트용 사용자 ID (첫 번째 사용)
        test_user_id = user_ids[0] if user_ids else "0003UZ715F1AVTCFVTLJ"
        
        # 트랜잭션 데이터에서 추출한 사용자 ID 샘플 출력
        print("\n트랜잭션 데이터에서 가져온 사용자 ID 샘플:")
        for i, user_id in enumerate(user_ids[:5], 1):
            print(f"{i}. {user_id}")
        
        # 테스트 질의문
        test_queries = [
            "식당과 카페에서 사용할 때 혜택이 좋은 카드 추천해주세요",
            "쇼핑할 때 유용한 카드 알려주세요",
            "여행과 주유 혜택이 좋은 카드 있나요?"
        ]
        
        # 사용자 프로필 조회하여 표시
        user_profile = rec_system.get_user_profile(test_user_id)
        spending_insights = rec_system.extract_spending_insights(test_user_id)
        
        print(f"\n사용자 프로필 (ID: {test_user_id}):")
        for key, value in user_profile.items():
            if key != 'user_id':
                print(f"- {key}: {value}")
        
        if spending_insights:
            print("\n소비 인사이트:")
            print(f"- 총 지출액: {spending_insights.get('총 지출', 0)}")
            print("- 주요 소비 카테고리:")
            for cat, data in spending_insights.get('주요 카테고리', {}).items():
                print(f"  * {cat}: {data['금액']} ({data['비율']}%)")
        
        # 첫 번째 질의로 테스트
        selected_query = test_queries[0]
        print(f"\n테스트 질의: {selected_query}")
        
        try:
            # 카드 추천 요청 및 응답 생성
            response = rec_system.process_user_query(test_user_id, selected_query)
            
            print("\n=== 추천 결과 ===")
            print(response)
            print("================")
            
            # 다른 질의 시도 여부 물어보기
            print("\n다른 질의도 시도해보시겠습니까? (y/n)")
            choice = input().lower()
            
            if choice == 'y':
                print("\n사용 가능한 질의:")
                for i, query in enumerate(test_queries, 1):
                    print(f"{i}. {query}")
                
                print("\n질의 번호를 선택하거나 직접 입력하세요:")
                user_input = input()
                
                try:
                    # 사용자 입력이 숫자인 경우 해당 질의 사용
                    query_idx = int(user_input) - 1
                    if 0 <= query_idx < len(test_queries):
                        user_query = test_queries[query_idx]
                    else:
                        user_query = user_input
                except ValueError:
                    # 사용자 입력이 숫자가 아닌 경우 직접 질의로 사용
                    user_query = user_input
                
                # 선택한 질의로 추천 요청
                response = rec_system.process_user_query(test_user_id, user_query)
                
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