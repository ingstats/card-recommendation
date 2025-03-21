import os
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import mysql.connector

# LangChain 관련 임포트
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import Document
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 환경 변수 로드
load_dotenv()

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

class CardRecommendation(BaseModel):
    """카드 추천 결과를 위한 Pydantic 모델"""
    card_name: str = Field(description="추천 카드 이름")
    corporate_name: str = Field(description="카드사 이름")
    recommendation_reason: str = Field(description="추천 이유")
    benefits: List[Dict[str, str]] = Field(description="카드 혜택 목록")

class CardRecommendationResponse(BaseModel):
    """최종 추천 응답을 위한 Pydantic 모델"""
    user_summary: str = Field(description="사용자 소비 패턴 요약")
    recommendations: List[CardRecommendation] = Field(description="추천 카드 목록")
    summary_opinion: str = Field(description="종합 추천 의견")

class CardRecommendationRAG:
    def __init__(self, mysql_config: Dict[str, Any]):
        """
        LangChain 기반 카드 추천 RAG 시스템 초기화
        
        Args:
            mysql_config: MySQL 연결 설정 (host, user, password, database 등)
        """
        # MySQL 연결 설정
        self.mysql_config = mysql_config
        
        # LangChain 임베딩 모델 초기화
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # LangChain LLM 초기화
        self.llm = ChatOpenAI(
            temperature=0.7,
            model_name="gpt-3.5-turbo",
            max_tokens=1500
        )
        
        # 벡터 저장소 초기화
        self.vector_store = None
        self.retriever = None
        
        # 카드 데이터 로드 및 벡터 저장소 생성
        self.load_card_data()
        self.create_vector_store()
    
    def load_card_data(self):
        """MySQL에서 카드 데이터 로드"""
        try:
            # MySQL 연결
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            # 카드 정보 쿼리
            query = """
            SELECT c.card_id, c.card_name, c.corporate_name, c.benefits, c.image_url, 
                   c.card_type
            FROM cards c
            """
            cursor.execute(query)
            
            # 결과를 DataFrame으로 변환
            self.cards_df = pd.DataFrame(cursor.fetchall())
            
            # 카드고릴라 크롤링 데이터 로드 (상세 정보용)
            query_gorilla = """
            SELECT cg.card_id, cg.detailed_benefits
            FROM card_gorilla_data cg
            """
            cursor.execute(query_gorilla)
            gorilla_df = pd.DataFrame(cursor.fetchall())
            
            # 두 데이터 합치기
            if not gorilla_df.empty:
                self.cards_df = pd.merge(
                    self.cards_df, 
                    gorilla_df, 
                    on='card_id', 
                    how='left'
                )
            
            # 필요시 NaN 처리
            self.cards_df.fillna('', inplace=True)
            
            print(f"카드 데이터 로드 완료: {len(self.cards_df)}개 카드")
            
            # 연결 종료
            cursor.close()
            connection.close()
            
            # 카드 문서 생성 (LangChain Document 형식)
            self.create_card_documents()
            
        except Exception as e:
            print(f"카드 데이터 로드 중 오류 발생: {str(e)}")
            self.cards_df = pd.DataFrame()  # 빈 DataFrame 생성
    
    def create_card_documents(self):
        """카드 데이터를 LangChain Document 형식으로 변환"""
        self.card_documents = []
        self.card_ids = []
        
        for idx, card in self.cards_df.iterrows():
            # 카드 정보를 하나의 텍스트로 결합
            card_text = f"카드명: {card.get('card_name', '')}\n"
            card_text += f"카드사: {card.get('corporate_name', '')}\n"
            card_text += f"카드 타입: {card.get('card_type', '')}\n"
            card_text += f"혜택: {card.get('benefits', '')}\n"
            
            # 카드고릴라 상세 정보가 있으면 추가
            if 'detailed_benefits' in card and card['detailed_benefits']:
                card_text += f"상세 혜택: {card.get('detailed_benefits', '')}\n"
            
            # 메타데이터 구성
            metadata = {
                'card_id': card.get('card_id'),
                'card_name': card.get('card_name', ''),
                'corporate_name': card.get('corporate_name', ''),
                'card_type': card.get('card_type', ''),
                'benefits': card.get('benefits', ''),
                'detailed_benefits': card.get('detailed_benefits', '') if 'detailed_benefits' in card else '',
                'image_url': card.get('image_url', '')
            }
            
            # LangChain Document 생성
            self.card_documents.append(
                Document(
                    page_content=card_text,
                    metadata=metadata
                )
            )
            
            self.card_ids.append(card.get('card_id'))
    
    def create_vector_store(self):
        """LangChain FAISS 벡터 저장소 생성"""
        try:
            # 캐시 파일 경로
            cache_file = 'faiss_index'
            
            # 캐시된 벡터 저장소가 있는지 확인
            if os.path.exists(f"{cache_file}.faiss") and os.path.exists(f"{cache_file}.pkl"):
                try:
                    # 캐시된 벡터 저장소 로드
                    self.vector_store = FAISS.load_local(
                        folder_path=".",
                        index_name=cache_file,
                        embeddings=self.embedding_model,
                        allow_dangerous_deserialization=True  # 안전한 환경에서만 사용
                    )
                    print(f"캐시된 벡터 저장소 로드 완료")
                except Exception as e:
                    print(f"캐시된 벡터 저장소 로드 실패, 새 저장소 생성: {str(e)}")
                    # 새 벡터 저장소 생성
                    self.vector_store = FAISS.from_documents(
                        documents=self.card_documents,
                        embedding=self.embedding_model
                    )
                    
                    # 새로 생성한 벡터 저장소 캐싱
                    self.vector_store.save_local(folder_path=".", index_name=cache_file)
            else:
                # 새 벡터 저장소 생성
                self.vector_store = FAISS.from_documents(
                    documents=self.card_documents,
                    embedding=self.embedding_model
                )
                
                # 벡터 저장소 캐싱
                self.vector_store.save_local(folder_path=".", index_name=cache_file)
                print(f"카드 벡터 저장소 생성 완료")
            
            # 검색기(Retriever) 생성 - 항상 실행되도록 함
            if self.vector_store:
                self.retriever = self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 10}
                )
            
        except Exception as e:
            print(f"벡터 저장소 생성 중 오류 발생: {str(e)}")
            # 벡터 저장소 생성 실패 시 백업 처리
            if not self.vector_store and self.card_documents:
                try:
                    print("백업 벡터 저장소 생성 시도...")
                    self.vector_store = FAISS.from_documents(
                        documents=self.card_documents,
                        embedding=self.embedding_model
                    )
                    self.retriever = self.vector_store.as_retriever(
                        search_type="similarity",
                        search_kwargs={"k": 10}
                    )
                except Exception as backup_error:
                    print(f"백업 벡터 저장소 생성 실패: {str(backup_error)}")
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 프로필 정보 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict: 사용자 프로필 정보
        """
        try:
            # MySQL 연결
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            # 두 가지 접근 방식 - 새로운 트랜잭션 데이터 형식 또는 기존 형식
            # 1. 새로운 트랜잭션 데이터 형식(SEQ 기반 사용자 ID)
            if len(user_id) > 20:  # 긴 ID는 트랜잭션 데이터 형식
                query = """
                SELECT 
                    t.seq_id as user_id,
                    t.age_group as age,
                    t.gender,
                    t.member_rank,
                    t.life_stage,
                    t.region_code,
                    t.total_usage_amount,
                    t.card_sales_amount,
                    t.restaurant_amount,
                    t.clothing_amount + t.clothing_general_amount as shopping_amount,
                    t.travel_amount + t.travel_general_amount as travel_amount,
                    t.top_spending_category
                FROM user_transactions t
                WHERE t.seq_id = %s
                """
                cursor.execute(query, (user_id,))
                user_trans = cursor.fetchone()
                
                if user_trans:
                    # 인코딩된 값을 사람이 읽을 수 있는 형식으로 매핑
                    gender_str = "남성" if user_trans["gender"] == 1 else "여성"
                    
                    # 연령대 매핑
                    age_mapping = {0: 20, 1: 30, 2: 40, 3: 50, 4: 60, 5: 70}
                    age_value = age_mapping.get(user_trans["age"], 35)
                    
                    # 회원등급에 따른 소득수준
                    income_level = "상위" if user_trans["member_rank"] <= 2 else "중간" if user_trans["member_rank"] == 3 else "낮음"
                    
                    # 트랜잭션 데이터에서 소비 패턴 가져오기
                    spending_query = """
                    SELECT
                        CASE 
                            WHEN restaurant_amount > 50 THEN '외식' 
                            WHEN restaurant_amount > 20 THEN '카페' 
                            ELSE NULL 
                        END as category1,
                        CASE 
                            WHEN clothing_amount + clothing_general_amount > 50 THEN '의류쇼핑'
                            WHEN furniture_amount + appliance_amount > 50 THEN '가전/가구'
                            ELSE NULL 
                        END as category2,
                        CASE 
                            WHEN travel_amount + travel_general_amount > 30 THEN '여행'
                            WHEN auto_amount + automaint_amount > 30 THEN '자동차'
                            ELSE NULL 
                        END as category3
                    FROM user_transactions
                    WHERE seq_id = %s
                    """
                    cursor.execute(spending_query, (user_id,))
                    spending_result = cursor.fetchone()
                    
                    # None 값 필터링하고 소비 패턴 문자열 형성
                    if spending_result:
                        categories = [cat for cat in spending_result.values() if cat]
                        if not categories:
                            # 유의미한 카테고리가 없으면 기본값 사용
                            spending_pattern = "일반적인 소비 습관"
                        else:
                            # 감지된 카테고리 합치기
                            spending_pattern = ", ".join(categories) + "을 중심으로 하는 소비 습관"
                    else:
                        spending_pattern = "일반적인 소비 습관"
                    
                    # 사용자 프로필 구성
                    user_profile = {
                        "user_id": user_id,
                        "연령대": f"{age_value}대",
                        "성별": gender_str,
                        "소득 수준": income_level,
                        "직업": "직장인",  # 기본값, 후에 정제 가능
                        "소비 패턴": spending_pattern,
                        "총 지출액": user_trans["total_usage_amount"]
                    }
                    cursor.close()
                    connection.close()
                    return user_profile
            
            # 2. 기존 사용자 데이터 형식 처리
            query = """
            SELECT u.user_id, u.age, u.gender, u.income_level, u.job_category 
            FROM users u 
            WHERE u.user_id = %s
            """
            cursor.execute(query, (user_id,))
            user_basic = cursor.fetchone()
            
            if not user_basic:
                cursor.close()
                connection.close()
                return {}
            
            # 사용자 소비 패턴 조회
            query_consumption = """
            SELECT cp.category, cp.amount, cp.frequency
            FROM consumption_patterns cp
            WHERE cp.user_id = %s
            ORDER BY cp.amount DESC
            """
            cursor.execute(query_consumption, (user_id,))
            consumption_patterns = cursor.fetchall()
            
            # 프로필 정보 구성
            user_profile = {
                "user_id": user_basic.get("user_id", ""),
                "연령대": f"{user_basic.get('age', 0)}대",
                "성별": user_basic.get("gender", ""),
                "소득 수준": user_basic.get("income_level", "중간"),
                "직업": user_basic.get("job_category", "직장인"),
                "소비 패턴": self._format_consumption_patterns(consumption_patterns)
            }
            
            # 연결 종료
            cursor.close()
            connection.close()
            
            return user_profile
            
        except Exception as e:
            print(f"사용자 프로필 조회 중 오류 발생: {str(e)}")
            return {}
    
    def _format_consumption_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """소비 패턴 포맷팅"""
        if not patterns:
            return "일반적인 소비 습관"
        
        # 상위 3개 카테고리 추출
        top_categories = patterns[:3]
        
        result = ", ".join([f"{p['category']}({p['frequency']})" for p in top_categories])
        return f"{result}을 중심으로 하는 소비 습관"
    
    def extract_spending_insights(self, user_id: str) -> Dict[str, Any]:
        """
        트랜잭션 데이터에서 소비 인사이트 추출
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict: 소비 인사이트
        """
        # 트랜잭션 데이터 형식 ID만 처리
        if not len(user_id) > 20:
            return {}
        
        try:
            # MySQL 연결
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            # 카테고리별 지출 조회 쿼리
            query = """
            SELECT 
                restaurant_amount,
                clothing_amount + clothing_general_amount as clothing_total,
                travel_amount + travel_general_amount as travel_total,
                grocery_amount,
                auto_amount + automaint_amount + autosl_amount as auto_total,
                hotel_amount,
                culture_amount,
                interior_amount + furniture_amount as home_total,
                total_usage_amount
            FROM user_transactions
            WHERE seq_id = %s
            """
            cursor.execute(query, (user_id,))
            spending = cursor.fetchone()
            
            if not spending:
                cursor.close()
                connection.close()
                return {}
            
            # 각 카테고리의 총 지출 대비 비율 계산
            total = spending["total_usage_amount"] or 1  # 0으로 나누기 방지
            
            insights = {
                "외식/카페": {
                    "금액": spending["restaurant_amount"],
                    "비율": round(spending["restaurant_amount"] / total * 100, 1)
                },
                "쇼핑/의류": {
                    "금액": spending["clothing_total"],
                    "비율": round(spending["clothing_total"] / total * 100, 1)
                },
                "여행/교통": {
                    "금액": spending["travel_total"],
                    "비율": round(spending["travel_total"] / total * 100, 1)
                },
                "식료품": {
                    "금액": spending["grocery_amount"],
                    "비율": round(spending["grocery_amount"] / total * 100, 1)
                },
                "자동차": {
                    "금액": spending["auto_total"],
                    "비율": round(spending["auto_total"] / total * 100, 1)
                },
                "숙박": {
                    "금액": spending["hotel_amount"],
                    "비율": round(spending["hotel_amount"] / total * 100, 1)
                },
                "문화/여가": {
                    "금액": spending["culture_amount"],
                    "비율": round(spending["culture_amount"] / total * 100, 1)
                },
                "가정/인테리어": {
                    "금액": spending["home_total"],
                    "비율": round(spending["home_total"] / total * 100, 1)
                }
            }
            
            # 금액으로 정렬하고 상위 카테고리 가져오기
            sorted_categories = sorted(
                insights.items(),
                key=lambda x: x[1]["금액"],
                reverse=True
            )
            
            # 상위 3개 카테고리
            top_categories = sorted_categories[:3]
            
            result = {
                "총 지출": total,
                "주요 카테고리": {cat[0]: cat[1] for cat in top_categories},
                "모든 카테고리": insights
            }
            
            cursor.close()
            connection.close()
            return result
            
        except Exception as e:
            print(f"소비 인사이트 추출 중 오류 발생: {str(e)}")
            return {}
    
    def semantic_search(self, query: str, user_profile: Dict[str, Any], 
                       spending_insights: Dict[str, Any] = None, 
                       top_k: int = 10) -> List[Dict[str, Any]]:
        """
        LangChain 기반 의미론적 검색 수행
        
        Args:
            query: 검색 쿼리
            user_profile: 사용자 프로필
            spending_insights: 소비 인사이트
            top_k: 상위 k개 결과 반환
            
        Returns:
            List: 검색 결과 (카드 정보)
        """
        try:
            # 검색기가 없으면 빈 리스트 반환
            if not self.retriever:
                print("retriever가 초기화되지 않았습니다. 모델 기반 추천으로 대체합니다.")
                return []
            
            # 사용자 프로필 정보를 쿼리에 추가하여 맥락화
            contextualized_query = query
            if user_profile:
                user_context = f"사용자는 {user_profile.get('연령대', '')} {user_profile.get('성별', '')}이고, "
                user_context += f"{user_profile.get('직업', '')}이며, {user_profile.get('소비 패턴', '')}입니다. "
                contextualized_query = user_context + query
            
            # 소비인사이트가 있으면 추가
            if spending_insights and spending_insights.get("주요 카테고리"):
                top_categories = spending_insights["주요 카테고리"]
                categories_context = "주요 소비 카테고리: "
                for cat_name, cat_data in top_categories.items():
                    categories_context += f"{cat_name}({cat_data['비율']}%), "
                contextualized_query += " " + categories_context
            
            # LangChain 검색기로 관련 문서 검색
            relevant_docs = self.retriever.invoke(contextualized_query)
            
            # 결과 구성
            results = []
            for i, doc in enumerate(relevant_docs[:top_k]):
                card_id = doc.metadata.get('card_id')
                
                # 원본 카드 데이터 가져오기
                card_data = self.cards_df[self.cards_df['card_id'] == card_id]
                
                if not card_data.empty:
                    card_dict = card_data.iloc[0].to_dict()
                    
                    # 개인화된 추천 이유 생성
                    recommendation_reason = self._generate_recommendation_reason(
                        card_dict, query, user_profile, spending_insights
                    )
                    
                    results.append({
                        'card_id': card_id,
                        'similarity_score': 1.0 - (i * 0.05),  # 유사도 점수 근사화 (1.0에서 시작하여 0.05씩 감소)
                        'recommendation_reason': recommendation_reason,
                        'details': card_dict
                    })
            
            return results
            
        except Exception as e:
            print(f"의미론적 검색 중 오류 발생: {str(e)}")
            return []
    
    def _generate_recommendation_reason(self, card_details: Dict[str, Any], 
                                      query: str, 
                                      user_profile: Dict[str, Any],
                                      spending_insights: Dict[str, Any] = None) -> str:
        """
        추천 이유 생성
        
        Args:
            card_details: 카드 상세 정보
            query: 사용자 질의
            user_profile: 사용자 프로필
            spending_insights: 소비 인사이트
            
        Returns:
            str: 추천 이유
        """
        card_name = card_details.get('card_name', '이 카드')
        
        # 사용자 소비 패턴 추출
        consumption_pattern = user_profile.get('소비 패턴', '')
        categories = []
        if '중심으로' in consumption_pattern:
            categories_text = consumption_pattern.split('중심으로')[0].strip()
            categories = [c.split('(')[0].strip() for c in categories_text.split(',')]
        
        # 소비인사이트에서 카테고리 추가
        if spending_insights and spending_insights.get("주요 카테고리"):
            categories.extend(spending_insights["주요 카테고리"].keys())
        
        # 카드 혜택 정보
        benefits = card_details.get('benefits', '')
        
        # 기본 추천 이유
        reason = f"{card_name}는 '{query}'와 관련된 혜택을 제공합니다."
        
        # 사용자 소비 패턴과 관련된 혜택이 있으면 추가
        for category in categories:
            if category in benefits:
                reason += f" 특히 {category} 관련 혜택이 귀하의 소비 패턴과 일치합니다."
                break
        
        # 트랜잭션 데이터의 인사이트가 있으면 추가
        if spending_insights and spending_insights.get("주요 카테고리"):
            top_category = list(spending_insights["주요 카테고리"].keys())[0]
            percentage = spending_insights["주요 카테고리"][top_category]["비율"]
            
            if top_category in benefits and percentage > 10:
                reason += f" 귀하는 {top_category}에 총 지출의 {percentage}%를 사용하고 있어 해당 혜택이 더욱 유용할 것입니다."
        
        return reason
    
    def get_top_n_recommendations(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        딥러닝 추천 시스템 결과와 의미론적 검색을 결합한 최종 추천
        
        Args:
            user_id: 사용자 ID
            query: 사용자 질의
            limit: 최대 추천 수
            
        Returns:
            List: 추천 카드 정보 목록
        """
        try:
            # 사용자 프로필 조회
            user_profile = self.get_user_profile(user_id)
            
            # 소비인사이트 추출 (새로운 트랜잭션 데이터 형식)
            spending_insights = self.extract_spending_insights(user_id) if len(user_id) > 20 else {}
            
            # 딥러닝 모델 기반 Top-N 카드 가져오기
            model_recommended_cards = self.get_model_recommendations(user_id)
            
            # 의미론적 검색 수행
            semantic_results = self.semantic_search(query, user_profile, spending_insights, top_k=10)
            
            # 두 결과 병합 및 재정렬
            combined_results = self.merge_recommendations(model_recommended_cards, semantic_results)
            
            # 상위 N개 결과 반환
            return combined_results[:limit]
            
        except Exception as e:
            print(f"추천 생성 중 오류 발생: {str(e)}")
            return []
    
    def get_model_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        딥러닝 모델 기반 추천 카드 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            List: 추천 카드 정보
        """
        try:
            # MySQL 연결
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            # 추천 결과 쿼리 - ranking 컬럼 사용
            query = """
            SELECT r.card_id, r.score, r.ranking
            FROM recommendations r
            WHERE r.user_id = %s
            ORDER BY r.ranking ASC
            LIMIT 20
            """
            cursor.execute(query, (user_id,))
            recommendations = cursor.fetchall()
            
            # 결과 포맷팅
            results = []
            for rec in recommendations:
                card_id = rec.get('card_id')
                
                # 카드 상세 정보 조회
                card_data = self.cards_df[self.cards_df['card_id'] == card_id]
                
                if not card_data.empty:
                    card_dict = card_data.iloc[0].to_dict()
                    
                    results.append({
                        'card_id': card_id,
                        'recommendation_score': rec.get('score', 0),
                        'recommendation_rank': rec.get('ranking', 999),
                        'details': card_dict
                    })
            
            # 연결 종료
            cursor.close()
            connection.close()
            
            return results
                
        except Exception as e:
            print(f"모델 추천 조회 중 오류 발생: {str(e)}")
            return []
    
    def merge_recommendations(self, model_recs: List[Dict[str, Any]], semantic_recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        모델 추천과 의미론적 검색 결과 병합
        
        Args:
            model_recs: 모델 기반 추천 결과
            semantic_recs: 의미론적 검색 결과
            
        Returns:
            List: 병합된 추천 결과
        """
        # 카드 ID로 매핑 생성
        model_map = {rec['card_id']: rec for rec in model_recs}
        semantic_map = {rec['card_id']: rec for rec in semantic_recs}
        
        all_card_ids = set(model_map.keys()) | set(semantic_map.keys())
        
        combined_results = []
        for card_id in all_card_ids:
            model_rec = model_map.get(card_id, {})
            semantic_rec = semantic_map.get(card_id, {})
            
            # 모델 추천과 의미론적 검색 모두에 있는 경우
            if card_id in model_map and card_id in semantic_map:
                # 점수 결합 (0.6 * 모델 점수 + 0.4 * 의미 점수)
                model_score = model_rec.get('recommendation_score', 0)
                semantic_score = semantic_rec.get('similarity_score', 0)
                
                combined_score = 0.6 * model_score + 0.4 * semantic_score
                
                # 추천 이유는 의미론적 검색 결과에서 사용
                reason = semantic_rec.get('recommendation_reason', '')
                
                combined_results.append({
                    'card_id': card_id,
                    'recommendation_score': combined_score,
                    'recommendation_reason': reason,
                    'details': model_rec.get('details', semantic_rec.get('details', {}))
                })
            
            # 모델 추천에만 있는 경우
            elif card_id in model_map:
                model_rec['recommendation_score'] *= 0.6  # 가중치 적용
                combined_results.append(model_rec)
            
            # 의미론적 검색에만 있는 경우
            else:
                semantic_rec['recommendation_score'] = semantic_rec.get('similarity_score', 0) * 0.4  # 가중치 적용
                combined_results.append(semantic_rec)
        
        # 최종 점수로 정렬
        combined_results.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        
        return combined_results
    
    def parse_benefits(self, benefits_str: str) -> List[Dict[str, str]]:
        """
        카드 혜택 문자열을 구조화된 형태로 파싱
        
        Args:
            benefits_str: 혜택 정보 문자열
            
        Returns:
            List: 파싱된 혜택 정보 목록
        """
        if not benefits_str:
            return []
        
        parsed_benefits = []
        
        # 세미콜론이나 개행으로 구분된 혜택 항목 분리
        delimiters = [';', '\n']
        for delimiter in delimiters:
            if delimiter in benefits_str:
                benefit_items = benefits_str.split(delimiter)
                
                for item in benefit_items:
                    item = item.strip()
                    if not item:
                        continue
                    
                    # 카테고리와 설명 분리 (콜론이나 큰 화살표 기준)
                    if ':' in item:
                        parts = item.split(':', 1)
                        category = parts[0].strip()
                        description = parts[1].strip()
                        parsed_benefits.append({"category": category, "description": description})
                    elif '→' in item:
                        parts = item.split('→', 1)
                        category = parts[0].strip()
                        description = parts[1].strip()
                        parsed_benefits.append({"category": category, "description": description})
                    else:
                        # 카테고리만 있는 경우
                        parsed_benefits.append({"category": item, "description": ""})
                
                return parsed_benefits
        
        # 구분자가 없는 경우 전체를 하나의 혜택으로 취급
        parsed_benefits.append({"category": "혜택", "description": benefits_str})
        
        return parsed_benefits
    
    def prepare_context_for_llm(self, user_profile: Dict[str, Any], 
                              recommendations: List[Dict[str, Any]],
                              spending_insights: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        LLM에 전달할 컨텍스트 정보 준비 (LangChain 형식)
        
        Args:
            user_profile: 사용자 프로필 정보
            recommendations: 추천 카드 목록
            spending_insights: 소비 인사이트
            
        Returns:
            Dict: LLM에 전달할 컨텍스트 정보
        """
        # 사용자 프로필 정보 구성
        user_info = {}
        for key, value in user_profile.items():
            if key != 'user_id':  # user_id는 제외
                user_info[key] = value
        
        # 소비인사이트가 있으면 추가
        if spending_insights:
            user_info["주요 소비 카테고리"] = spending_insights.get("주요 카테고리", {})
            user_info["총 지출액"] = spending_insights.get("총 지출", 0)
        
        # 추천 카드 정보 구성
        rec_cards = []
        for i, rec in enumerate(recommendations, 1):
            details = rec.get('details', {})
            
            # 카드 기본 정보
            card_name = details.get('card_name', '이름 없음')
            corporate_name = details.get('corporate_name', '정보 없음')
            card_type = details.get('card_type', '')
            
            # 혜택 정보 처리
            benefits_str = details.get('benefits', '')
            parsed_benefits = self.parse_benefits(benefits_str)
            
            benefits_list = []
            for benefit in parsed_benefits:
                category = benefit.get('category', '')
                description = benefit.get('description', '')
                if description:
                    benefits_list.append(f"{category}: {description}")
                else:
                    benefits_list.append(f"{category}")
            
            # 카드 정보 구성
            card_info = {
                "번호": i,
                "카드명": card_name,
                "카드사": corporate_name,
                "추천 점수": rec.get('recommendation_score', '정보 없음'),
                "추천 이유": rec.get('recommendation_reason', '정보 없음'),
                "카드 타입": card_type,
                "주요 혜택": benefits_list,
                "상세 혜택": details.get('detailed_benefits', ''),
                "이미지 URL": details.get('image_url', '')
            }
            
            rec_cards.append(card_info)
        
        # 전체 컨텍스트 정보
        context = {
            "사용자_프로필": user_info,
            "추천_카드": rec_cards
        }
        
        return context
    
    def generate_response_with_llm(self, user_query: str, user_profile: Dict[str, Any], 
                                 recommendations: List[Dict[str, Any]],
                                 spending_insights: Dict[str, Any] = None) -> str:
        """
        LangChain LLM을 사용하여 사용자 질문에 대한 응답 생성
        
        Args:
            user_query: 사용자 질문
            user_profile: 사용자 프로필 정보
            recommendations: 추천 카드 목록
            spending_insights: 소비 인사이트
            
        Returns:
            str: LLM 응답 문자열
        """
        try:
            # 컨텍스트 준비 (LangChain 형식)
            context = self.prepare_context_for_llm(user_profile, recommendations, spending_insights)
            
            # 시스템 프롬프트 템플릿
            system_template = """
            당신은 신용카드 추천 전문가입니다. 사용자의 질문에 대해 제공된 카드 정보를 기반으로 
            정확하고 친절하게 답변해 주세요. 카드의 혜택을 명확히 설명하고, 사용자에게 가장 적합한 
            카드를 추천해 주세요. 카드 정보는 신뢰할 수 있는 데이터베이스에서 가져온 것입니다.
            
            반드시 응답에 추천하는 카드의 이름, 카드사, 그리고 각 카드의 주요 혜택을 상세하게 포함시켜야 합니다.
            혜택은 카테고리별로 구분하여 설명하고, 사용자의 소비 패턴과 관련된 혜택을 강조해 주세요.
            
            사용자의 질문을 분석하여 가장 적합한 카드를 먼저 추천하고, 그 이유를 설명해 주세요.
            각 카드의 혜택을 명확히 표시하고, 사용자가 이해하기 쉽도록 구체적인 예시를 들어 설명해 주세요.
            """
            
            # 사용자 프롬프트 템플릿
            human_template = """
            다음은 사용자의 질문입니다:
            {query}
            
            다음은 사용자 정보와 추천 카드에 대한 정보입니다:
            {context}
            
            응답 형식:
            1. 사용자의 소비 패턴 요약
            2. 추천 카드 목록 (각 카드마다):
               - 카드명: [카드 이름]
               - 카드사: [카드사 이름]
               - 추천 이유: [사용자 특성에 맞는 추천 이유]
               - 주요 혜택:
                 * [혜택 카테고리1]: [혜택 설명1]
                 * [혜택 카테고리2]: [혜택 설명2]
                 * [혜택 카테고리3]: [혜택 설명3]
            3. 종합 추천 의견
            
            위 정보를 바탕으로 사용자의 질문에 자연스럽게 답변해주세요.
            답변은 친절하고 자연스러운 대화체로 작성해주세요.
            """
            
            # 메시지 템플릿 생성 
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
            
            chat_prompt = ChatPromptTemplate.from_messages([
                system_message_prompt, 
                human_message_prompt
            ])
            
            # 파이프라인 방식 사용
            chain = chat_prompt | self.llm
            response = chain.invoke({"query": user_query, "context": context})
            
            # 응답 내용 추출
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return response_text
            
        except Exception as e:
            print(f"LLM 응답 생성 중 오류 발생: {str(e)}")
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 질문해 주세요."
            
    def process_user_query(self, user_id: str, user_query: str) -> str:
        """
        사용자 질문 처리 및 추천 응답 생성
        
        Args:
            user_id: 사용자 ID
            user_query: 사용자 질문
            
        Returns:
            str: 추천 응답 문자열
        """
        try:
            # 사용자 프로필 조회
            user_profile = self.get_user_profile(user_id)
            
            if not user_profile:
                return "사용자 정보를 찾을 수 없습니다. 올바른 사용자 ID를 입력해주세요."
            
            # 소비인사이트 추출 (새로운 트랜잭션 데이터 형식)
            spending_insights = self.extract_spending_insights(user_id) if len(user_id) > 20 else {}
            
            # 추천 카드 조회 (최대 5개)
            recommendations = self.get_top_n_recommendations(user_id, user_query, limit=5)
            
            if not recommendations:
                # 의미론적 검색 실패 시 모델 기반 추천만 사용
                if not self.retriever:
                    print("의미론적 검색 실패, 모델 기반 추천만 사용")
                    recommendations = self.get_model_recommendations(user_id)[:5]
                
                # 그래도 추천 카드가 없는 경우
                if not recommendations:
                    return "죄송합니다. 조건에 맞는 추천 카드를 찾을 수 없습니다. 다른 조건으로 다시 시도해주세요."
            
            # LangChain LLM을 사용한 응답 생성
            response = self.generate_response_with_llm(user_query, user_profile, recommendations, spending_insights)
            
            return response
            
        except Exception as e:
            print(f"사용자 질의 처리 중 오류 발생: {str(e)}")
            return "죄송합니다. 요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    def run_recommendation_service(self):
        """
        추천 서비스 실행 (간단한 CLI 인터페이스)
        """
        print("카드 추천 시스템을 시작합니다.")
        
        while True:
            user_id = input("\n사용자 ID를 입력하세요 (종료하려면 'exit' 입력): ")
            
            if user_id.lower() == 'exit':
                print("서비스를 종료합니다. 감사합니다.")
                break
            
            # 사용자 ID 확인
            profile = self.get_user_profile(user_id)
            if not profile:
                print("존재하지 않는 사용자 ID입니다. 다시 시도해주세요.")
                continue
            
            print(f"\n{profile.get('성별', '')} {profile.get('연령대', '')} 사용자님, 어떤 카드를 찾고 계신가요?")
            
            while True:
                user_query = input("\n질문을 입력하세요 (이전 메뉴로 돌아가려면 'back' 입력): ")
                
                if user_query.lower() == 'back':
                    break
                
                # 추천 응답 생성
                response = self.process_user_query(user_id, user_query)
                
                print("\n=== 추천 결과 ===")
                print(response)
                print("================")
    
    def save_recommendations_to_db(self, user_id: str, recommendations: List[Dict[str, Any]]) -> bool:
        """
        추천 결과를 데이터베이스에 저장
        
        Args:
            user_id: 사용자 ID
            recommendations: 추천 카드 목록
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # MySQL 연결
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()
            
            # 이전 추천 데이터 삭제
            delete_query = "DELETE FROM user_recommendations WHERE user_id = %s"
            cursor.execute(delete_query, (user_id,))
            
            # 추천 데이터 저장
            insert_query = """
            INSERT INTO user_recommendations 
            (user_id, card_id, recommendation_score, recommendation_reason, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
            """
            
            for rec in recommendations:
                card_id = rec.get('card_id', '')
                score = rec.get('recommendation_score', 0)
                reason = rec.get('recommendation_reason', '')
                
                cursor.execute(insert_query, (user_id, card_id, score, reason))
            
            # 변경사항 저장
            connection.commit()
            
            # 연결 종료
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"추천 결과 저장 중 오류 발생: {str(e)}")
            return False
    
    def get_card_details(self, card_id: str) -> Dict[str, Any]:
        """
        특정 카드의 상세 정보 조회
        
        Args:
            card_id: 카드 ID
            
        Returns:
            Dict: 카드 상세 정보
        """
        try:
            # 카드 데이터에서 검색
            card_data = self.cards_df[self.cards_df['card_id'] == card_id]
            
            if not card_data.empty:
                return card_data.iloc[0].to_dict()
            else:
                return {}
                
        except Exception as e:
            print(f"카드 상세 정보 조회 중 오류 발생: {str(e)}")
            return {}


# 메인 실행 코드
if __name__ == "__main__":
    # MySQL 설정
    mysql_config = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3307")),
    "user": os.getenv("MYSQL_USER", "recommendation_team"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "card_recommendation")
}

    
    # 추천 시스템 초기화
    recommendation_system = CardRecommendationRAG(mysql_config)
    
    # CLI 서비스 실행
    recommendation_system.run_recommendation_service()