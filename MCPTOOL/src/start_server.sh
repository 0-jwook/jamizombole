#!/bin/bash
# TravelGenie 서버 실행 스크립트

# 현재 스크립트 위치 기준으로 경로 설정
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# mcp 디렉토리로 이동
cd "$PROJECT_ROOT/mcp" || exit 1

# 가상환경 활성화
if [ -f "bin/activate" ]; then
    source bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다. bin/activate 파일이 없습니다."
    exit 1
fi

# src 디렉토리로 이동
cd src || exit 1

# 서버 실행
echo "🚀 TravelGenie 서버를 시작합니다..."
echo "📍 접속 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo ""
echo "서버를 종료하려면 Ctrl+C를 누르세요."
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

