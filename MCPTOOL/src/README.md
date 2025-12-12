# TravelGenie - AI 여행 코스 추천 서비스

공공데이터를 활용한 AI 기반 맞춤형 여행 코스 추천 서비스입니다.

## 주요 기능

- 🌍 **여행지 검색**: 공공데이터포털 관광정보 API를 통한 여행지 검색
- 🤖 **AI 코스 추천**: LangChain + Google Gemini를 활용한 맞춤형 여행 코스 생성
- 🔍 **RAG 기반 검색**: 벡터DB(Chroma)를 활용한 여행지 정보 검색 및 요약
- 🎯 **스마트 필터링**: 테마, 시간, 실내/실외 등 다양한 필터 조건 지원
- ⚡ **MCP Tool 통합**: MCP Server를 통한 표준화된 API 연동

## 기술 스택

- **Backend**: FastAPI
- **MCP**: MCP Server + Tool
- **LLM**: Google Gemini API + LangChain
- **RAG**: ChromaDB + Sentence Transformers
- **Data Source**: 공공데이터포털 한국관광공사 관광정보 API

## 설치 방법

### 1. 가상환경 활성화

```bash
# 프로젝트 루트에서
cd mcp
source bin/activate  # 또는 bin\activate (Windows)
```

### 2. 의존성 설치

```bash
cd src
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

필수 환경 변수:
- `GOOGLE_API_KEY`: Google Gemini API 키
- `TOURISM_API_KEY`: 공공데이터포털 관광정보 API 키

## API 키 발급

### 공공데이터포털 관광정보 API
1. [공공데이터포털](https://www.data.go.kr/) 접속
2. "한국관광공사_국문 관광정보 서비스" 검색
3. 활용신청 후 인증키 발급

### Google Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 버튼 클릭하여 API 키 생성
3. 또는 [Google Cloud Console](https://console.cloud.google.com/)에서 API 키 발급

## 실행 방법

### FastAPI 서버 실행

```bash
cd mcp/src
python -m app.main
```

또는:

```bash
cd mcp/src
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버 실행 후 [http://localhost:8000/docs](http://localhost:8000/docs)에서 API 문서 확인 가능합니다.

### MCP Server 실행

```bash
cd mcp/src
python -m app.mcp.server
```

## API 엔드포인트

### 1. 여행지 검색

```bash
POST /travel/search
Content-Type: application/json

{
  "region": "부산",
  "keyword": "바다",
  "num_of_rows": 10
}
```

### 2. 여행 코스 추천

```bash
POST /travel/recommend
Content-Type: application/json

{
  "query": "부산에서 3시간 바다 코스 추천해줘"
}
```

응답 예시:

```json
{
  "course": [
    {
      "name": "해운대 해수욕장",
      "description": "부산의 대표적인 해수욕장으로 해안 산책로와 카페가 잘 갖춰져 있습니다.",
      "time": "1시간"
    },
    {
      "name": "용궁사",
      "description": "바다를 바라보는 절로 조용한 분위기에서 힐링할 수 있습니다.",
      "time": "30분"
    }
  ]
}
```

## 프로젝트 구조

```
mcp/src/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 메인 서버
│   ├── api/
│   │   ├── __init__.py
│   │   └── travel.py          # 여행 관련 API 엔드포인트
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # MCP Server
│   │   └── tourism_tool.py    # 관광정보 API Tool
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── chain.py           # LangChain 코스 생성 체인
│   │   └── rag.py             # RAG 시스템
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py          # 설정 관리
│   │   ├── area_code.py       # 지역 코드 유틸리티
│   │   └── filter.py          # 필터링 기능
│   └── db/                    # 데이터베이스 저장소
│       └── chroma_db/         # ChromaDB 벡터DB
├── requirements.txt
├── .env.example
└── README.md
```

## 테스트 예시

### 1. 부산 바다 코스 추천

```bash
curl -X POST "http://localhost:8000/travel/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "부산 바다 코스 추천해줘"}'
```

### 2. 서울 실내 위주 데이트 코스

```bash
curl -X POST "http://localhost:8000/travel/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "서울 실내 위주 데이트 코스"}'
```

### 3. 가족이랑 갈만한 제주도 반나절 여행지

```bash
curl -X POST "http://localhost:8000/travel/recommend" \
  -H "Content-Type: application/json" \
  -d '{"query": "가족이랑 갈만한 제주도 반나절 여행지"}'
```

## 주요 기능 설명

### 1. 여행지 검색 (MCP Tool)
- 공공데이터포털 관광정보 API 연동
- 지역명, 키워드 기반 검색
- 지역 코드 자동 매핑

### 2. 필터링
- 테마 필터 (데이트, 가족, 힐링, 문화 등)
- 실내/실외 구분
- 시간 기반 필터링

### 3. RAG 시스템
- 여행지 정보를 ChromaDB 벡터DB에 저장
- 사용자 쿼리와 관련된 문서 검색
- LLM에 컨텍스트로 제공하여 정확도 향상

### 4. AI 코스 생성
- LangChain 프롬프트 템플릿 기반
- 사용자 요구사항 분석
- 이동 시간 및 체류 시간 고려
- JSON 형식으로 구조화된 출력

## 성능 최적화

- API 응답 시간 2초 이하 목표
- 벡터DB 캐싱
- 비동기 처리 (FastAPI async/await)

## 문제 해결

### 공공데이터 API 오류
- API 키 확인
- 서비스 URL 확인 (`app/utils/config.py`)
- 네트워크 연결 확인

### Google Gemini API 오류
- API 키 확인
- 할당량 확인
- 모델 이름 확인 (gemini-pro 또는 gemini-1.5-pro)
- Google Cloud 프로젝트 설정 확인

### ChromaDB 오류
- `db/chroma_db` 폴더 권한 확인
- 디스크 공간 확인

## 라이선스

이 프로젝트는 교육 및 학습 목적으로 제작되었습니다.

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

