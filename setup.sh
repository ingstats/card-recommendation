#!/bin/bash
echo "==== 카드 추천 시스템 Docker 환경 설정 ===="

# 1. Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
  echo "Docker가 실행되고 있지 않습니다. Docker Desktop을 실행해주세요."
  exit 1
fi

# 2. 필요한 Python 패키지 설치
echo -e "\n[1/5] 필요한 Python 패키지 설치 중..."
pip install -r requirements.txt

# 3. Docker Compose로 MySQL 컨테이너 실행
echo -e "\n[2/5] Docker Compose로 MySQL 컨테이너 실행 중..."
docker-compose down -v 2>/dev/null || true
docker-compose up -d

# 4. MySQL 테이블 생성
echo -e "\n[3/5] MySQL 테이블 생성 중..."
chmod +x scripts/setup_mysql.sh
./scripts/setup_mysql.sh

# 5. 카드 데이터 로드
echo -e "\n[4/5] 카드 데이터 로드 중..."
python scripts/card_data_tosql.py

# 6. 테스트 실행 준비 완료
echo -e "\n[5/5] 설정 완료! 테스트 실행 준비 완료"
echo "docker_test_recommendation.py를 실행하여 카드 추천 시스템을 테스트할 수 있습니다."
echo "실행 명령어: python docker_test_recommendation.py"
