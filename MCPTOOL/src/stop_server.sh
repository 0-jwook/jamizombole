#!/bin/bash
# TravelGenie 서버 종료 스크립트

echo "🛑 서버를 종료합니다..."

# 포트 8000을 사용하는 프로세스 찾기 및 종료
PID=$(lsof -ti:8000 2>/dev/null)

if [ -z "$PID" ]; then
    echo "❌ 실행 중인 서버가 없습니다."
    exit 0
fi

echo "📌 프로세스 ID: $PID"
kill $PID 2>/dev/null

# 프로세스가 종료될 때까지 대기
sleep 2

# 여전히 실행 중인지 확인
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "⚠️  강제 종료 시도 중..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

if lsof -ti:8000 >/dev/null 2>&1; then
    echo "❌ 서버 종료 실패"
    exit 1
else
    echo "✅ 서버가 성공적으로 종료되었습니다."
fi

