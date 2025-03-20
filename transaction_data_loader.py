import pandas as pd
import numpy as np
import pymysql
import os
from dotenv import load_dotenv
import csv

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
        print("쿼리 성공적으로 실행됨")
    except Exception as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()

# 일괄 쿼리 실행 함수 (대량 데이터 처리용)
def execute_many_query(connection, query, data_list):
    cursor = connection.cursor()
    try:
        cursor.executemany(query, data_list)
        connection.commit()
        print(f"일괄 쿼리 성공적으로 실행됨 ({len(data_list)} 레코드)")
    except Exception as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()

# 파일 구분자 자동 감지
def detect_delimiter(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            
            # 가능한 구분자 목록
            delimiters = [',', '\t', ';', '|']
            
            # 각 구분자별로 첫 줄 분할 시도
            max_count = 0
            best_delimiter = ','  # 기본값
            
            for delimiter in delimiters:
                count = first_line.count(delimiter)
                if count > max_count:
                    max_count = count
                    best_delimiter = delimiter
            
            # 좀더 명확한 감지를 위해 csv.Sniffer 사용
            try:
                with open(file_path, 'r', encoding='utf-8') as sniffer_f:
                    sample = sniffer_f.read(4096)
                    dialect = csv.Sniffer().sniff(sample)
                    return dialect.delimiter
            except:
                pass  # Sniffer가 실패하면 이전 방법으로 돌아감
                
            print(f"파일 구분자를 '{best_delimiter}'로 감지했습니다.")
            return best_delimiter
    except Exception as e:
        print(f"구분자 감지 중 오류 발생: {str(e)}")
        return ','  # 기본 쉼표 구분자 사용

# CSV에서 트랜잭션 데이터 읽기
def read_transaction_data(file_path):
    try:
        # 파일 구분자 자동 감지
        delimiter = detect_delimiter(file_path)
        
        # 파일 확인을 위해 첫 몇 행만 읽기
        df_sample = pd.read_csv(file_path, delimiter=delimiter, nrows=5)
        print(f"파일 구분자 '{delimiter}'로 읽기 성공")
        print("샘플 컬럼 목록:", df_sample.columns.tolist())
        
        # 전체 파일 읽기
        print(f"전체 파일 읽기 중... (큰 파일의 경우 시간이 걸릴 수 있습니다)")
        df = pd.read_csv(file_path, delimiter=delimiter)
        print(f"트랜잭션 데이터 파일에서 {len(df)}개 행 읽기 완료")
        
        # SEQ 컬럼 확인
        if 'SEQ' in df.columns:
            print("'SEQ' 컬럼을 찾았습니다!")
            null_count = df['SEQ'].isnull().sum()
            print(f"'SEQ' 컬럼의 null 값 개수: {null_count}")
            
            # null 값이 있는 경우 제거
            if null_count > 0:
                df = df.dropna(subset=['SEQ'])
                print(f"{null_count}개의 null SEQ 값을 가진 행을 제거했습니다.")
                print(f"정제 후 남은 행 수: {len(df)}")
            
            # SEQ 값 샘플 확인
            print("SEQ 값 샘플:", df['SEQ'].head(3).tolist())
        else:
            print("'SEQ' 컬럼을 찾을 수 없습니다!")
            print("현재 컬럼 목록:", df.columns.tolist())
            
            # 대소문자 구분없이 'seq' 또는 유사한 이름 찾기
            for col in df.columns:
                if col.upper() == 'SEQ':
                    print(f"'{col}'을(를) 'SEQ'로 변경합니다.")
                    df = df.rename(columns={col: 'SEQ'})
                    break
            
            # 그래도 없으면 첫 번째 컬럼을 임시로 SEQ로 간주
            if 'SEQ' not in df.columns and len(df.columns) > 0:
                first_col = df.columns[0]
                print(f"경고: SEQ 컬럼을 찾을 수 없어 첫 번째 컬럼 '{first_col}'을 임시로 SEQ로 사용합니다.")
                df = df.rename(columns={first_col: 'SEQ'})
        
        return df
    except Exception as e:
        print(f"트랜잭션 데이터 파일 읽기 오류: {str(e)}")
        return None

# 트랜잭션 데이터 DB에 삽입
def insert_transaction_data(connection, df, batch_size=1000):
    try:
        # SEQ 컬럼 존재 확인
        if 'SEQ' not in df.columns:
            print("오류: 데이터프레임에 'SEQ' 컬럼이 없습니다. 삽입을 진행할 수 없습니다.")
            return
        
        # SEQ 컬럼에 null 값이 없는지 확인
        df_clean = df.dropna(subset=['SEQ'])
        rows_dropped = len(df) - len(df_clean)
        if rows_dropped > 0:
            print(f"null SEQ 값이 있는 {rows_dropped}개 행을 제거했습니다.")
            df = df_clean
        
        # SEQ 컬럼의 고유값 확인 (중복 체크)
        unique_seq_count = df['SEQ'].nunique()
        print(f"고유 SEQ 값 개수: {unique_seq_count} (총 {len(df)}개 행)")
        
        # 데이터 유형 확인 및 필요시 변환
        print("SEQ 컬럼 데이터 타입:", df['SEQ'].dtype)
        if df['SEQ'].dtype == 'float64':
            print("경고: SEQ 컬럼이 숫자 형식입니다. 문자열로 변환합니다.")
            df['SEQ'] = df['SEQ'].astype(str)
        
        # 모든 컬럼이 포함된 삽입 쿼리 생성
        insert_query = """
        INSERT INTO user_transactions (
            seq_id, base_year_quarter, att_date, age_group, gender, member_rank, 
            region_code, life_stage, digital_channel_registered, digital_channel_used,
            total_usage_amount, card_sales_amount, conf_usage_amount, interior_amount,
            insuhos_amount, offedu_amount, travel_amount, business_amount, service_amount,
            distribution_amount, health_amount, clothing_amount, auto_amount, furniture_amount,
            appliance_amount, healthfood_amount, building_amount, architecture_amount,
            optic_amount, agriculture_amount, leisure_s_amount, leisure_p_amount,
            culture_amount, sanit_amount, insurance_amount, office_amount, book_amount,
            repair_amount, hotel_amount, goods_amount, travel_general_amount, fuel_amount,
            service_general_amount, distbnp_amount, distbp_amount, grocery_amount,
            hospital_amount, clothing_general_amount, restaurant_amount, automaint_amount,
            autosl_amount, kitchenware_amount, fabric_amount, academy_amount, membership_amount,
            month_diff, top_spending_category
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # CSV 컬럼명과 DB 컬럼명 매핑 생성 (데이터 매핑용)
        column_mapping = {
            'SEQ': 'seq_id',  # 사용자 시퀀스 ID
            'BAS_YH': 'base_year_quarter',  # 기준 년도/분기
            'ATT_YM': 'att_date',  # 가입 년월
            'AGE_encoded': 'age_group',  # 연령대 코드
            'SEX_CD_encoded': 'gender',  # 성별 코드
            'MBR_RK_encoded': 'member_rank',  # 회원등급 코드
            'HOUS_SIDO_NM_encoded': 'region_code',  # 지역 코드
            'LIFE_STAGE_encoded': 'life_stage',  # 생애주기 코드
            'DIGT_CHNL_REG_YN_encoded': 'digital_channel_registered',  # 디지털 채널 등록 여부
            'DIGT_CHNL_USE_YN_encoded': 'digital_channel_used',  # 디지털 채널 사용 여부
            'TOT_USE_AM_mean': 'total_usage_amount',  # 총 사용 금액
            'CRDSL_USE_AM_mean': 'card_sales_amount',  # 카드 결제 금액
            'CNF_USE_AM_mean': 'conf_usage_amount',  # 확정 사용 금액
            'INTERIOR_AM_mean': 'interior_amount',  # 인테리어 금액
            'INSUHOS_AM_mean': 'insuhos_amount',  # 병원/보험 금액
            'OFFEDU_AM_mean': 'offedu_amount',  # 교육 금액
            'TRVLEC_AM_mean': 'travel_amount',  # 여행 금액
            'FSBZ_AM_mean': 'business_amount',  # 비즈니스 금액
            'SVCARC_AM_mean': 'service_amount',  # 서비스 금액
            'DIST_AM_mean': 'distribution_amount',  # 유통 금액
            'PLSANIT_AM_mean': 'health_amount',  # 건강 금액
            'CLOTHGDS_AM_mean': 'clothing_amount',  # 의류 금액
            'AUTO_AM_mean': 'auto_amount',  # 자동차 금액
            'FUNITR_AM_mean': 'furniture_amount',  # 가구 금액
            'APPLNC_AM_mean': 'appliance_amount',  # 가전 금액
            'HLTHFS_AM_mean': 'healthfood_amount',  # 건강식품 금액
            'BLDMNG_AM_mean': 'building_amount',  # 건물관리 금액
            'ARCHIT_AM_mean': 'architecture_amount',  # 건축 금액
            'OPTIC_AM_mean': 'optic_amount',  # 안경 금액
            'AGRICTR_AM_mean': 'agriculture_amount',  # 농업 금액
            'LEISURE_S_AM_mean': 'leisure_s_amount',  # 레저(스포츠) 금액
            'LEISURE_P_AM_mean': 'leisure_p_amount',  # 레저(놀이) 금액
            'CULTURE_AM_mean': 'culture_amount',  # 문화 금액
            'SANIT_AM_mean': 'sanit_amount',  # 위생 금액
            'INSU_AM_mean': 'insurance_amount',  # 보험 금액
            'OFFCOM_AM_mean': 'office_amount',  # 사무 금액
            'BOOK_AM_mean': 'book_amount',  # 도서 금액
            'RPR_AM_mean': 'repair_amount',  # 수리 금액
            'HOTEL_AM_mean': 'hotel_amount',  # 호텔 금액
            'GOODS_AM_mean': 'goods_amount',  # 상품 금액
            'TRVL_AM_mean': 'travel_general_amount',  # 여행(일반) 금액
            'FUEL_AM_mean': 'fuel_amount',  # 연료 금액
            'SVC_AM_mean': 'service_general_amount',  # 서비스(일반) 금액
            'DISTBNP_AM_mean': 'distbnp_amount',  # 유통 BNP 금액
            'DISTBP_AM_mean': 'distbp_amount',  # 유통 BP 금액
            'GROCERY_AM_mean': 'grocery_amount',  # 식료품 금액
            'HOS_AM_mean': 'hospital_amount',  # 병원 금액
            'CLOTH_AM_mean': 'clothing_general_amount',  # 의류(일반) 금액
            'RESTRNT_AM_mean': 'restaurant_amount',  # 식당 금액
            'AUTOMNT_AM_mean': 'automaint_amount',  # 자동차 정비 금액
            'AUTOSL_AM_mean': 'autosl_amount',  # 자동차 판매 금액
            'KITWR_AM_mean': 'kitchenware_amount',  # 주방용품 금액
            'FABRIC_AM_mean': 'fabric_amount',  # 직물/섬유 금액
            'ACDM_AM_mean': 'academy_amount',  # 학원 금액
            'MBRSHOP_AM_mean': 'membership_amount',  # 멤버십 금액
            'MONTH_DIFF': 'month_diff',  # 월 차이
            'TOP_SPENDING_CATEGORY_encoded': 'top_spending_category'  # 최고 지출 카테고리 코드
        }
        
        # 데이터프레임 컬럼과 매핑 검증
        print("\n컬럼 매핑 검증:")
        missing_columns = []
        for source_col in column_mapping.keys():
            if source_col not in df.columns:
                missing_columns.append(source_col)
                print(f"- 없음: {source_col} -> {column_mapping[source_col]}")
        
        if missing_columns:
            print(f"\n주의: {len(missing_columns)}개 컬럼이 데이터에 없습니다.")
            
            # 컬럼 이름의 대소문자 차이 확인 및 수정
            lower_columns = {col.lower(): col for col in df.columns}
            for missing_col in missing_columns.copy():
                if missing_col.lower() in lower_columns:
                    actual_col = lower_columns[missing_col.lower()]
                    print(f"대소문자 차이 발견: '{missing_col}' -> '{actual_col}', 수정 중...")
                    df = df.rename(columns={actual_col: missing_col})
                    missing_columns.remove(missing_col)
            
            # 그래도 없는 컬럼은 빈 값으로 추가
            for col in missing_columns:
                print(f"없는 컬럼 '{col}'을 빈 값으로 추가합니다.")
                df[col] = None
        
        # 모든 행 전처리
        all_data = []
        valid_rows = 0
        error_rows = 0
        
        # 진행률 표시 설정
        total_rows = len(df)
        progress_step = max(1, total_rows // 20)  # 5% 단위로 진행률 표시
        
        print(f"\n{total_rows}개 행 처리 시작...")
        
        for idx, row in df.iterrows():
            try:
                # 진행률 표시
                if idx % progress_step == 0:
                    print(f"처리 중: {idx}/{total_rows} 행 ({idx/total_rows*100:.1f}%)")
                
                # SEQ 값이 null이 아닌지 확인
                if pd.isna(row['SEQ']):
                    continue
                
                # 적절한 오류 처리와 함께 데이터 튜플 생성
                data_values = []
                for col in column_mapping.keys():
                    # 열이 데이터프레임에 존재하는지 확인
                    if col in row:
                        # NaN 값을 적절히 처리
                        value = row[col]
                        if pd.isna(value):
                            value = None
                        data_values.append(value)
                    else:
                        # 열이 존재하지 않으면 None 사용
                        data_values.append(None)
                
                # seq_id(첫 번째 값)가 None이 아닌 경우에만 튜플 추가
                if data_values[0] is not None:
                    all_data.append(tuple(data_values))
                    valid_rows += 1
                
            except Exception as row_error:
                error_rows += 1
                if error_rows <= 5:  # 처음 5개 오류만 출력
                    print(f"행 {idx} 처리 중 오류 발생: {str(row_error)}")
                elif error_rows == 6:
                    print("추가 오류는 생략됩니다...")
                continue
        
        print(f"\n데이터 처리 완료: {valid_rows}개 유효 행, {error_rows}개 오류 행")
        
        if not all_data:
            print("삽입할 유효한 데이터가 없습니다.")
            return
        
        # 배치 단위로 데이터 삽입
        print(f"\n데이터 삽입 시작 (배치 크기: {batch_size})...")
        
        # 총 배치 수 계산
        total_batches = (len(all_data) + batch_size - 1) // batch_size
        
        for i in range(0, len(all_data), batch_size):
            batch = all_data[i:i+batch_size]
            batch_num = i // batch_size + 1
            print(f"배치 {batch_num}/{total_batches} 삽입 중 ({len(batch)}개 행)...")
            execute_many_query(connection, insert_query, batch)
        
        print(f"트랜잭션 데이터 삽입 완료: {len(all_data)}개 레코드")
                
    except Exception as e:
        print(f"트랜잭션 데이터 삽입 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 트랜잭션 데이터에서 사용자 프로필 생성
def create_user_profiles_from_transactions(connection):
    try:
        # 트랜잭션에서 고유 사용자 추출
        query = """
        SELECT DISTINCT 
            seq_id as user_id,
            age_group as age,
            gender,
            CASE 
                WHEN member_rank <= 2 THEN '상위'
                WHEN member_rank = 3 THEN '중간'
                ELSE '낮음'
            END as income_level,
            CASE
                WHEN life_stage = 10 THEN '직장인'
                WHEN life_stage = 9 THEN '학생'
                WHEN life_stage = 8 THEN '자영업'
                ELSE '기타'
            END as job_category
        FROM user_transactions
        """
        
        cursor = connection.cursor()
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        
        if not users:
            print("user_transactions 테이블에서 데이터를 찾을 수 없습니다.")
            return
            
        print(f"트랜잭션에서 {len(users)}명의 사용자 프로필을 추출했습니다.")
        
        # 사용자를 users 테이블에 삽입
        insert_user_query = """
        INSERT INTO users (user_id, age, gender, income_level, job_category)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            age = VALUES(age),
            gender = VALUES(gender),
            income_level = VALUES(income_level),
            job_category = VALUES(job_category)
        """
        
        # 배치 처리 설정
        batch_size = 1000
        total_users = len(users)
        batches = (total_users + batch_size - 1) // batch_size
        
        for batch_idx in range(batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_users)
            batch_users = users[start_idx:end_idx]
            
            # 처리할 사용자 데이터 배열
            user_data_batch = []
            
            for user in batch_users:
                # 성별 숫자를 텍스트로 변환
                user_data = list(user)
                user_data[2] = "남성" if user[2] == 1 else "여성"
                
                # 연령대 코드를 실제 나이로 변환
                age_mapping = {0: 20, 1: 30, 2: 40, 3: 50, 4: 60, 5: 70}
                user_data[1] = age_mapping.get(user[1], 35)  # 기본값 35
                
                user_data_batch.append(tuple(user_data))
            
            # 배치 삽입
            cursor = connection.cursor()
            try:
                cursor.executemany(insert_user_query, user_data_batch)
                connection.commit()
                print(f"사용자 프로필 배치 삽입: {len(user_data_batch)}명 ({batch_idx+1}/{batches})")
            except Exception as e:
                print(f"사용자 프로필 배치 삽입 오류: {str(e)}")
            finally:
                cursor.close()
        
        print(f"사용자 프로필 생성/업데이트 완료: {total_users}명")
        
        # 소비 패턴 생성
        create_consumption_patterns(connection)
        
    except Exception as e:
        print(f"사용자 프로필 생성 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 트랜잭션 데이터에서 소비 패턴 생성
def create_consumption_patterns(connection):
    try:
        # 카테고리 매핑 (소비 카테고리 코드 → 이름)
        category_mapping = {
            1: "식품/마트", 2: "쇼핑", 3: "자동차", 4: "주유", 5: "공과금",
            6: "통신비", 7: "의료/건강", 8: "여행/교통", 9: "문화/오락", 
            10: "교육", 11: "카페/식당", 12: "유흥/오락", 13: "보험", 
            14: "금융", 15: "기타", 16: "가전/가구", 17: "뷰티/미용"
        }
        
        # 기존 소비 패턴 데이터 삭제 (갱신 전)
        clear_query = "DELETE FROM consumption_patterns"
        execute_query(connection, clear_query)
        
        # 최고 지출 카테고리를 기반으로 소비 패턴 생성
        query = """
        SELECT 
            seq_id as user_id,
            top_spending_category,
            total_usage_amount,
            CASE 
                WHEN total_usage_amount > 1000 THEN '매우 자주'
                WHEN total_usage_amount > 500 THEN '자주'
                WHEN total_usage_amount > 100 THEN '가끔'
                ELSE '드물게'
            END as frequency
        FROM user_transactions
        """
        
        cursor = connection.cursor()
        cursor.execute(query)
        patterns = cursor.fetchall()
        cursor.close()
        
        if not patterns:
            print("소비 패턴을 생성할 트랜잭션 데이터가 없습니다.")
            return
            
        print(f"{len(patterns)}개의 소비 패턴 레코드를 생성합니다.")
        
        # 소비 패턴 삽입
        insert_pattern_query = """
        INSERT INTO consumption_patterns (user_id, category, amount, frequency)
        VALUES (%s, %s, %s, %s)
        """
        
        # 배치 처리 설정
        batch_size = 1000
        total_patterns = len(patterns)
        batches = (total_patterns + batch_size - 1) // batch_size
        
        for batch_idx in range(batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_patterns)
            batch_patterns = patterns[start_idx:end_idx]
            
            # 처리할 패턴 데이터 배열
            pattern_data_batch = []
            
            for pattern in batch_patterns:
                user_id, category_id, amount, frequency = pattern
                
                # NULL 값 확인 및 처리
                if user_id is None or category_id is None:
                    continue
                    
                category_name = category_mapping.get(category_id, "기타")
                pattern_data_batch.append((user_id, category_name, amount, frequency))
            
            # 배치 삽입
            if pattern_data_batch:
                cursor = connection.cursor()
                try:
                    cursor.executemany(insert_pattern_query, pattern_data_batch)
                    connection.commit()
                    print(f"소비 패턴 배치 삽입: {len(pattern_data_batch)}개 ({batch_idx+1}/{batches})")
                except Exception as e:
                    print(f"소비 패턴 배치 삽입 오류: {str(e)}")
                finally:
                    cursor.close()
        
        print(f"소비 패턴 생성 완료: {len(patterns)}개 패턴")
        
        # 특정 카테고리에 높은 지출이 있는 경우 추가 패턴 생성 (샘플링 방식으로 변경)
        print("추가 소비 패턴 생성 중...")
        sample_users_query = """
        SELECT seq_id FROM user_transactions 
        WHERE restaurant_amount > 30 OR clothing_amount + clothing_general_amount > 20 
        OR travel_amount + travel_general_amount > 15
        LIMIT 1000
        """
        
        cursor = connection.cursor()
        cursor.execute(sample_users_query)
        sample_users = cursor.fetchall()
        cursor.close()
        
        for user_data in sample_users:
            user_id = user_data[0]
            create_additional_patterns(connection, user_id)
        
    except Exception as e:
        print(f"소비 패턴 생성 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 특정 카테고리 고지출 기반 추가 소비 패턴 생성
def create_additional_patterns(connection, user_id):
    try:
        # 해당 사용자의 특정 카테고리 고지출 분석 쿼리
        query = """
        SELECT 
            seq_id as user_id,
            '카페/식당' as category,
            restaurant_amount as amount,
            'weekly' as frequency
        FROM user_transactions
        WHERE seq_id = %s AND restaurant_amount > 30
        UNION
        SELECT 
            seq_id,
            '쇼핑' as category,
            clothing_amount + clothing_general_amount as amount,
            'monthly' as frequency
        FROM user_transactions
        WHERE seq_id = %s AND (clothing_amount + clothing_general_amount) > 20
        UNION
        SELECT 
            seq_id,
            '교통/여행' as category,
            travel_amount + travel_general_amount as amount,
            'monthly' as frequency
        FROM user_transactions
        WHERE seq_id = %s AND (travel_amount + travel_general_amount) > 15
        """
        
        cursor = connection.cursor()
        cursor.execute(query, (user_id, user_id, user_id))
        patterns = cursor.fetchall()
        cursor.close()
        
        # 추가 패턴이 있으면 삽입
        if patterns:
            insert_pattern_query = """
            INSERT INTO consumption_patterns (user_id, category, amount, frequency)
            VALUES (%s, %s, %s, %s)
            """
            
            for pattern in patterns:
                execute_query(connection, insert_pattern_query, pattern)
        
    except Exception as e:
        print(f"사용자 {user_id}의 추가 패턴 생성 중 오류 발생: {str(e)}")

# 소비 패턴 기반 샘플 추천 생성
def generate_recommendations(connection):
    try:
        # 기존 추천 데이터 삭제
        clear_query = "DELETE FROM recommendations"
        execute_query(connection, clear_query)
        
        # 모든 사용자 가져오기
        user_query = "SELECT user_id FROM users LIMIT 1000"  # 시스템 부하 감소를 위해 1000명만 처리
        cursor = connection.cursor()
        cursor.execute(user_query)
        users = cursor.fetchall()
        
        # 모든 카드 가져오기
        card_query = "SELECT card_id FROM cards"
        cursor.execute(card_query)
        cards = cursor.fetchall()
        cursor.close()
        
        if not cards:
            print("데이터베이스에 카드가 없습니다. 먼저 카드 데이터를 로드해주세요.")
            return
        
        if not users:
            print("데이터베이스에 사용자가 없습니다.")
            return
        
        print(f"{len(users)}명의 사용자에 대한 추천을 생성합니다.")
        
        card_ids = [card[0] for card in cards]
        
        # 배치 처리 설정
        batch_size = 100
        total_users = len(users)
        batches = (total_users + batch_size - 1) // batch_size
        
        # 추천 데이터 삽입 쿼리
        insert_rec_query = """
        INSERT INTO recommendations (user_id, card_id, score, ranking)
        VALUES (%s, %s, %s, %s)
        """
        
        for batch_idx in range(batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, total_users)
            batch_users = users[start_idx:end_idx]
            
            # 추천 데이터 배열
            recommendation_batch = []
            
            for user_data in batch_users:
                user_id = user_data[0]
                
                # 각 사용자에게 3-5개 무작위 카드 선택
                num_recommendations = min(len(card_ids), np.random.randint(3, 6))
                selected_card_indices = np.random.choice(len(card_ids), num_recommendations, replace=False)
                
                for rank, idx in enumerate(selected_card_indices, 1):
                    card_id = card_ids[idx]
                    # 0.7-0.95 사이의 점수 생성 (순위가 높을수록 점수도 높음)
                    score = round(0.7 + 0.25 * (num_recommendations - rank) / num_recommendations, 2)
                    
                    recommendation_batch.append((user_id, card_id, score, rank))
            
            # 배치 삽입
            cursor = connection.cursor()
            try:
                cursor.executemany(insert_rec_query, recommendation_batch)
                connection.commit()
                print(f"추천 배치 삽입: {len(recommendation_batch)}개 ({batch_idx+1}/{batches})")
            except Exception as e:
                print(f"추천 배치 삽입 오류: {str(e)}")
            finally:
                cursor.close()
                
        print(f"추천 데이터 생성 완료: {len(users)}명의 사용자")
                
    except Exception as e:
        print(f"추천 생성 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 메인 함수
def main():
    import argparse
    
    # 명령줄 인수 파서 설정
    parser = argparse.ArgumentParser(description='트랜잭션 데이터 로더')
    parser.add_argument('file_path', nargs='?', default='data/transaction_data.csv', 
                        help='트랜잭션 데이터 파일 경로 (기본값: data/transaction_data.csv)')
    parser.add_argument('--batch-size', type=int, default=1000, 
                        help='DB 삽입 배치 크기 (기본값: 1000)')
    parser.add_argument('--skip-users', action='store_true',
                        help='사용자 프로필 생성 단계 건너뛰기')
    parser.add_argument('--skip-patterns', action='store_true',
                        help='소비 패턴 생성 단계 건너뛰기')
    parser.add_argument('--skip-recommendations', action='store_true',
                        help='추천 생성 단계 건너뛰기')
    
    args = parser.parse_args()
    
    # 트랜잭션 데이터 파일 경로
    transaction_file = args.file_path
    
    # 파일이 없으면 paste.txt 사용 (업로드된 데이터)
    if not os.path.exists(transaction_file):
        transaction_file = "paste.txt"
        print(f"{transaction_file}을 트랜잭션 데이터 소스로 사용합니다")
    
    # DB 연결
    connection = create_db_connection()
    
    if connection:
        try:
            # 트랜잭션 데이터 읽기
            df = read_transaction_data(transaction_file)
            
            if df is not None:
                # 트랜잭션 데이터 삽입
                insert_transaction_data(connection, df, batch_size=args.batch_size)
                
                # 사용자 프로필 생성
                if not args.skip_users:
                    create_user_profiles_from_transactions(connection)
                else:
                    print("사용자 프로필 생성 단계 건너뛰기")
                
                # 소비 패턴 및 추천 생성
                if not args.skip_patterns:
                    if not args.skip_recommendations:
                        generate_recommendations(connection)
                    else:
                        print("추천 생성 단계 건너뛰기")
                else:
                    print("소비 패턴 생성 단계 건너뛰기")
                
            # 연결 종료
            connection.close()
            print("MySQL 연결 종료")
            
        except Exception as e:
            print(f"처리 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생해도 연결 종료
            try:
                connection.close()
                print("MySQL 연결 종료")
            except:
                pass

if __name__ == "__main__":
    main()