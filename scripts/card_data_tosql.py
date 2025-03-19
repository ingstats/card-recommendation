import pandas as pd
import numpy as np
import pymysql
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# MySQL 연결 설정
def create_db_connection():
    connection = None
    try:
        connection = pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "recommendation_team"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "card_recommendation")
        )

        print("MySQL 데이터베이스 연결 성공")
    except Exception as err:
        print(f"Error: '{err}'")
    return connection

# 쿼리 실행 함수
def execute_query(connection, query, data=None):
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        print("쿼리 성공적으로 실행")
    except Exception as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()

# 조회 쿼리 실행 함수
def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as err:
        print(f"Error: '{err}'")
        return None
    finally:
        cursor.close()

# 엑셀 파일 읽기
def read_excel_data(file_path):
    try:
        df = pd.read_excel(file_path)
        print(f"엑셀 파일에서 {len(df)} 행 읽기 성공")
        return df
    except Exception as e:
        print(f"엑셀 파일 읽기 오류: {str(e)}")
        return None

# 혜택 파싱 함수 (conditions 반환 제거)
def parse_benefits(benefits_text):
    if not benefits_text or pd.isna(benefits_text):
        return ""
    
    # 세미콜론(;)으로 분리된 혜택 항목들
    benefit_items = str(benefits_text).split(';')
    
    detailed_benefits = ""
    
    for item in benefit_items:
        item = item.strip()
        if not item:
            continue
        
        # 유의사항은 무시하고 혜택만 추가
        if "유의사항" not in item:
            detailed_benefits += item + "; "
    
    return detailed_benefits

# 카드 데이터 삽입
def insert_card_data(connection, df):
    try:
        # cards 테이블 삽입 쿼리
        insert_card_query = """
        INSERT INTO cards (card_id, card_name, corporate_name, benefits, image_url, card_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # card_gorilla_data 테이블 삽입 쿼리 (conditions 필드 제외)
        insert_gorilla_query = """
        INSERT INTO card_gorilla_data (card_id, detailed_benefits)
        VALUES (%s, %s)
        """
        
        # 각 행 처리
        for index, row in df.iterrows():
            card_name = row.get('Card Name', '') 
            if pd.isna(card_name):
                card_name = f"Unknown Card {index}"
                
            corporate_name = row.get('Corporate Name', '')
            if pd.isna(corporate_name):
                corporate_name = "기타"
                
            # 고유 ID 생성
            card_id = f"CARD{str(index+1).zfill(3)}"
            
            # 혜택 정보
            benefits = row.get('Benefits', '')
            if pd.isna(benefits):
                benefits = ''
                
            # 이미지 URL
            image_url = row.get('Image URLs', '')
            if pd.isna(image_url):
                image_url = ''
            
            # 카드 타입
            card_type = row.get('Card Type', '신용카드')
            if pd.isna(card_type):
                card_type = '신용카드'
                
            # 상세 혜택 파싱 (conditions 반환 값 제거)
            detailed_benefits = parse_benefits(benefits)
            
            # cards 테이블 데이터 삽입
            card_data = (card_id, card_name, corporate_name, benefits, image_url, card_type)
            execute_query(connection, insert_card_query, card_data)
            
            # card_gorilla_data 테이블 데이터 삽입 (conditions 필드 제외)
            gorilla_data = (card_id, detailed_benefits)
            execute_query(connection, insert_gorilla_query, gorilla_data)
            
        print("카드 데이터 삽입 완료")
                
    except Exception as e:
        print(f"카드 데이터 삽입 오류: {str(e)}")

# 테스트 사용자 추가
def insert_test_users(connection):
    try:
        # 사용자 테이블 삽입 쿼리
        insert_user_query = """
        INSERT INTO users (user_id, age, gender, income_level, job_category)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        # 소비 패턴 테이블 삽입 쿼리
        insert_consumption_query = """
        INSERT INTO consumption_patterns (user_id, category, amount, frequency)
        VALUES (%s, %s, %s, %s)
        """
        
        # 테스트 사용자 데이터
        test_users = [
            ("user1", 30, "여성", "중간", "직장인"),
            ("user2", 40, "남성", "상위", "자영업"),
            ("user3", 25, "여성", "낮음", "학생"),
            ("user4", 35, "남성", "중간", "직장인")
        ]
        
        # 테스트 소비 패턴 데이터
        test_consumption_patterns = [
            # 사용자 1 (여성, 30대)
            ("user1", "카페", 80000, "주 3회"),
            ("user1", "외식", 200000, "주 2회"),
            ("user1", "쇼핑", 300000, "월 2회"),
            
            # 사용자 2 (남성, 40대)
            ("user2", "주유", 200000, "주 2회"),
            ("user2", "통신비", 150000, "월 1회"),
            ("user2", "마트", 400000, "주 1회"),
            
            # 사용자 3 (여성, 20대)
            ("user3", "온라인쇼핑", 150000, "월 3회"),
            ("user3", "카페", 60000, "주 4회"),
            ("user3", "영화", 50000, "월 2회"),
            
            # 사용자 4 (남성, 30대)
            ("user4", "외식", 300000, "주 3회"),
            ("user4", "대중교통", 100000, "주 5회"),
            ("user4", "편의점", 80000, "주 3회")
        ]
        
        # 사용자 데이터 삽입
        for user in test_users:
            execute_query(connection, insert_user_query, user)
            
        # 소비 패턴 데이터 삽입
        for pattern in test_consumption_patterns:
            execute_query(connection, insert_consumption_query, pattern)
            
        print("테스트 사용자 및 소비 패턴 데이터 삽입 완료")
                
    except Exception as e:
        print(f"테스트 사용자 데이터 삽입 오류: {str(e)}")

# 테스트 추천 데이터 생성
def insert_test_recommendations(connection):
    try:
        # 카드 ID 조회
        query = "SELECT card_id FROM cards LIMIT 20"
        results = read_query(connection, query)
        
        if not results:
            print("카드 데이터가 없습니다.")
            return
            
        card_ids = [result[0] for result in results]
        
        # 추천 테이블 삽입 쿼리
        insert_rec_query = """
        INSERT INTO recommendations (user_id, card_id, score, ranking)
        VALUES (%s, %s, %s, %s)
        """
        
        # 테스트 사용자 ID
        user_ids = ["user1", "user2", "user3", "user4"]
        
        # 각 사용자별 5개의 카드 추천 생성
        for user_id in user_ids:
            # 무작위 카드 5개 선택
            selected_cards = np.random.choice(len(card_ids), min(5, len(card_ids)), replace=False)
            
            for rank, idx in enumerate(selected_cards, 1):
                card_id = card_ids[idx]
                # 점수는 0.7~0.95 사이 무작위 값
                score = round(np.random.uniform(0.7, 0.95), 2)
                
                # 추천 데이터 삽입
                rec_data = (user_id, card_id, score, rank)
                execute_query(connection, insert_rec_query, rec_data)
                
        print("테스트 추천 데이터 삽입 완료")
                
    except Exception as e:
        print(f"테스트 추천 데이터 삽입 오류: {str(e)}")

# 메인 함수
def main():
    # 엑셀 파일 경로
    excel_file = "data/card_data_updated.xlsx"
    
    # DB 연결
    connection = create_db_connection()
    
    if connection:
        # 엑셀 데이터 읽기
        df = read_excel_data(excel_file)
        
        if df is not None:
            # 카드 데이터 삽입
            insert_card_data(connection, df)
            
            # 테스트 사용자 데이터 삽입
            insert_test_users(connection)
            
            # 테스트 추천 데이터 생성
            insert_test_recommendations(connection)
            
        # 연결 종료
        connection.close()
        print("MySQL 연결 종료")

if __name__ == "__main__":
    main()
