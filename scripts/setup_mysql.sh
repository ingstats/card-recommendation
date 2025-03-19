#!/bin/bash
source .env

echo "==== 카드 추천 시스템 MySQL 테이블 설정 ===="

# MySQL 서버가 준비될 때까지 대기
echo -e "\n[1/2] MySQL 서버가 시작될 때까지 대기 중... (약 30초)"
for i in {1..30}; do
  echo -n "."
  sleep 1
  # 5초마다 연결 시도 (올바른 사용자와 비밀번호 사용)
  if [ $((i % 5)) -eq 0 ]; then
    if docker exec mysql-card-rec mysqladmin -u${MYSQL_USER} -p${MYSQL_PASSWORD} ping --silent > /dev/null 2>&1; then
      echo -e "\nMySQL 서버가 준비되었습니다!"
      break
    fi
  fi
done

# 테이블 스키마 생성
echo -e "\n[2/2] 데이터베이스 테이블 스키마 생성 중..."
# SQL 스크립트 파일 생성
cat > create_tables.sql << 'EOF'
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
EOF

# SQL 스크립트 실행 (환경 변수 사용)
docker exec -i mysql-card-rec mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} < create_tables.sql

echo -e "\n==== 테이블 설정 완료! ===="
echo "데이터베이스 테이블 스키마가 생성되었습니다."
