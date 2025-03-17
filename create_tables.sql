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
-- 카드고릴라 데이터 테이블 (conditions TEXT 필드 제외)
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
