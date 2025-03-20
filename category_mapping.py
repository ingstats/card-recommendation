import os
import pymysql
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 함수
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
            cursor.execute(query, data)  # 파라미터가 있는 쿼리 실행
        else:
            cursor.execute(query)  # 일반 쿼리 실행
        connection.commit()  # 변경사항 커밋
        print("쿼리 성공적으로 실행됨")
    except Exception as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()  # 커서 닫기

# 일괄 쿼리 실행 함수
def execute_many_query(connection, query, data_list):
    cursor = connection.cursor()
    try:
        cursor.executemany(query, data_list)  # 여러 레코드 한번에 실행
        connection.commit()  # 변경사항 커밋
        print(f"일괄 쿼리 성공적으로 실행됨 ({len(data_list)}개 레코드)")
    except Exception as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()  # 커서 닫기

# 인코딩된 카테고리 값들에 대한 매핑 정의
def create_category_mappings():
    # TOP_SPENDING_CATEGORY_encoded 매핑
    spending_category_mapping = {
        1: "식품/마트",
        2: "쇼핑",
        3: "자동차",
        4: "주유",
        5: "공과금",
        6: "통신비",
        7: "의료/건강",
        8: "여행/교통",
        9: "문화/오락", 
        10: "교육",
        11: "카페/식당",
        12: "유흥/오락",
        13: "보험",
        14: "금융",
        15: "기타",
        16: "가전/가구",
        17: "뷰티/미용"
    }
    
    # 연령대 매핑 (AGE_encoded)
    age_mapping = {
        0: "20대",
        1: "30대",
        2: "40대",
        3: "50대",
        4: "60대",
        5: "70대 이상"
    }
    
    # 성별 매핑 (SEX_CD_encoded)
    gender_mapping = {
        0: "여성",
        1: "남성"
    }
    
    # 회원등급 매핑 (MBR_RK_encoded)
    member_rank_mapping = {
        0: "최우수",
        1: "우수",
        2: "상위",
        3: "중간",
        4: "일반"
    }
    
    # 생애주기 매핑 (LIFE_STAGE_encoded)
    life_stage_mapping = {
        8: "자영업",
        9: "학생",
        10: "직장인",
        11: "주부",
        12: "은퇴자"
    }
    
    # 지역 매핑 (HOUS_SIDO_NM_encoded)
    region_mapping = {
        1: "서울",
        2: "경기",
        3: "인천",
        4: "강원",
        5: "충북",
        6: "충남",
        7: "대전",
        8: "경북",
        9: "경남",
        10: "대구",
        11: "울산",
        12: "부산",
        13: "전북",
        14: "전남",
        15: "광주",
        16: "제주"
    }
    
    # 모든 매핑을 하나의 딕셔너리로 통합
    all_mappings = {
        "소비카테고리": spending_category_mapping,
        "연령대": age_mapping,
        "성별": gender_mapping,
        "회원등급": member_rank_mapping,
        "생애주기": life_stage_mapping,
        "지역": region_mapping
    }
    
    return all_mappings

# 매핑 정보를 데이터베이스에 저장
def save_category_mappings(connection, mappings):
    # 기존 매핑 삭제
    delete_query = "DELETE FROM category_mappings"
    execute_query(connection, delete_query)
    
    # 새 매핑 추가
    insert_query = """
    INSERT INTO category_mappings (category_id, category_name, category_type)
    VALUES (%s, %s, %s)
    """
    
    mapping_data = []
    
    # 각 매핑 유형별로 처리
    for mapping_type, mapping_values in mappings.items():
        for code, name in mapping_values.items():
            # 매핑 유형에 따라 카테고리 ID 프리픽스 추가 (겹치지 않게)
            if mapping_type == "소비카테고리":
                category_id = code  # 소비 카테고리는 원래 코드 사용
            elif mapping_type == "연령대":
                category_id = 100 + code  # 100대 코드 사용
            elif mapping_type == "성별":
                category_id = 200 + code  # 200대 코드 사용
            elif mapping_type == "회원등급":
                category_id = 300 + code  # 300대 코드 사용
            elif mapping_type == "생애주기":
                category_id = 400 + code  # 400대 코드 사용
            elif mapping_type == "지역":
                category_id = 500 + code  # 500대 코드 사용
            else:
                category_id = 900 + code  # 기타는 900대 코드 사용
            
            mapping_data.append((category_id, name, mapping_type))
    
    # 매핑 데이터 일괄 삽입
    execute_many_query(connection, insert_query, mapping_data)
    print(f"카테고리 매핑 저장 완료: {len(mapping_data)}개 항목")

# 트랜잭션 데이터의 카테고리 코드 검증
def validate_category_codes(connection):
    try:
        # TOP_SPENDING_CATEGORY_encoded 값 확인
        query = """
        SELECT DISTINCT top_spending_category 
        FROM user_transactions 
        ORDER BY top_spending_category
        """
        
        cursor = connection.cursor()
        cursor.execute(query)
        categories = cursor.fetchall()
        cursor.close()
        
        print("\n트랜잭션 데이터에서 발견된 카테고리 코드:")
        for cat in categories:
            print(f"- 카테고리 코드: {cat[0]}")
        
        # 연령대 값 확인
        query = """
        SELECT DISTINCT age_group 
        FROM user_transactions 
        ORDER BY age_group
        """
        
        cursor = connection.cursor()
        cursor.execute(query)
        ages = cursor.fetchall()
        cursor.close()
        
        print("\n트랜잭션 데이터에서 발견된 연령대 코드:")
        for age in ages:
            print(f"- 연령대 코드: {age[0]}")
        
    except Exception as e:
        print(f"카테고리 코드 검증 중 오류 발생: {str(e)}")

# 메인 함수
def main():
    # DB 연결
    connection = create_db_connection()
    
    if connection:
        try:
            # 카테고리 코드 검증 (옵션)
            validate_category_codes(connection)
            
            # 매핑 정의 가져오기
            mappings = create_category_mappings()
            
            # 매핑 정보 저장
            save_category_mappings(connection, mappings)
            
            print("카테고리 매핑 생성 및 저장 완료!")
            
        except Exception as e:
            print(f"매핑 처리 중 오류 발생: {str(e)}")
        finally:
            # 연결 종료
            connection.close()
            print("MySQL 연결 종료")

if __name__ == "__main__":
    main()