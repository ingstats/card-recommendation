-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
  user_id VARCHAR(50) PRIMARY KEY,
  age INT,
  gender VARCHAR(10),
  income_level VARCHAR(20),
  job_category VARCHAR(50)
);
-- 소비 패턴 테이블
CREATE TABLE IF NOT EXISTS consumption_patterns (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(50),
  category VARCHAR(50),
  amount DECIMAL(10,2),
  frequency VARCHAR(20),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
);
-- 카드 테이블
CREATE TABLE IF NOT EXISTS cards (
  card_id VARCHAR(50) PRIMARY KEY,
  card_name VARCHAR(100),
  corporate_name VARCHAR(50),
  benefits TEXT,
  image_url VARCHAR(255),
  card_type VARCHAR(50) DEFAULT '신용카드'
);
-- 카드고릴라 데이터 테이블
CREATE TABLE IF NOT EXISTS card_gorilla_data (
  card_id VARCHAR(50) PRIMARY KEY,
  detailed_benefits TEXT,
  FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
-- 추천 테이블
CREATE TABLE IF NOT EXISTS recommendations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(50),
  card_id VARCHAR(50),
  score FLOAT,
  ranking INT,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
-- 사용자 추천 결과 저장 테이블
CREATE TABLE IF NOT EXISTS user_recommendations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id VARCHAR(50),
  card_id VARCHAR(50),
  recommendation_score FLOAT,
  recommendation_reason TEXT,
  created_at DATETIME,
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
-- 신규: 사용자 트랜잭션 데이터 테이블
CREATE TABLE IF NOT EXISTS user_transactions (
  seq_id VARCHAR(50) PRIMARY KEY,
  base_year_quarter VARCHAR(10),
  att_date VARCHAR(20),
  age_group INT,
  gender INT,
  member_rank INT,
  region_code INT,
  life_stage INT,
  digital_channel_registered BOOLEAN,
  digital_channel_used BOOLEAN,
  total_usage_amount DECIMAL(10,2),
  card_sales_amount DECIMAL(10,2),
  conf_usage_amount DECIMAL(10,2),
  interior_amount DECIMAL(10,2),
  insuhos_amount DECIMAL(10,2),
  offedu_amount DECIMAL(10,2),
  travel_amount DECIMAL(10,2),
  business_amount DECIMAL(10,2),
  service_amount DECIMAL(10,2),
  distribution_amount DECIMAL(10,2),
  health_amount DECIMAL(10,2),
  clothing_amount DECIMAL(10,2),
  auto_amount DECIMAL(10,2),
  furniture_amount DECIMAL(10,2),
  appliance_amount DECIMAL(10,2),
  healthfood_amount DECIMAL(10,2),
  building_amount DECIMAL(10,2),
  architecture_amount DECIMAL(10,2),
  optic_amount DECIMAL(10,2),
  agriculture_amount DECIMAL(10,2),
  leisure_s_amount DECIMAL(10,2),
  leisure_p_amount DECIMAL(10,2),
  culture_amount DECIMAL(10,2),
  sanit_amount DECIMAL(10,2),
  insurance_amount DECIMAL(10,2),
  office_amount DECIMAL(10,2),
  book_amount DECIMAL(10,2),
  repair_amount DECIMAL(10,2),
  hotel_amount DECIMAL(10,2),
  goods_amount DECIMAL(10,2),
  travel_general_amount DECIMAL(10,2),
  fuel_amount DECIMAL(10,2),
  service_general_amount DECIMAL(10,2),
  distbnp_amount DECIMAL(10,2),
  distbp_amount DECIMAL(10,2),
  grocery_amount DECIMAL(10,2),
  hospital_amount DECIMAL(10,2),
  clothing_general_amount DECIMAL(10,2),
  restaurant_amount DECIMAL(10,2),
  automaint_amount DECIMAL(10,2),
  autosl_amount DECIMAL(10,2),
  kitchenware_amount DECIMAL(10,2),
  fabric_amount DECIMAL(10,2),
  academy_amount DECIMAL(10,2),
  membership_amount DECIMAL(10,2),
  month_diff INT,
  top_spending_category INT
);
-- 신규: 카테고리 매핑 테이블
CREATE TABLE IF NOT EXISTS category_mappings (
  category_id INT PRIMARY KEY,
  category_name VARCHAR(100),
  category_type VARCHAR(50)
);
