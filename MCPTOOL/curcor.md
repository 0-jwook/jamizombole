프로젝트명: TravelGenie - AI 여행 코스 추천 서비스

목표:
- 사용자 입력(지역/키워드/테마/시간/예산 등)에 따라 공공데이터 기반 여행지 정보를 조회하고,
  LLM이 사용자 조건에 맞는 맞춤형 여행 코스를 생성하는 서비스 구현.

필수 기술 스택:
- FastAPI (메인 백엔드 서버)
- MCP Server + MCP Tool (공공데이터 API 연동용)
- LangChain (Prompt, Chains, Retrieval)
- LLM (OpenAI API or 무료 모델)
- RAG 구조 (여행지 텍스트 데이터 벡터DB 저장)
- 공공데이터포털 관광정보 API(KorService1)

선택 기술:
- React 프론트엔드
- Docker

핵심 기능 요구사항:

1) 여행지 검색 기능 (MCP Tool)
   - MCP Tool 이름: "tourism_search"
   - 입력: 지역(areaCode), 키워드(keyword)
   - 데이터 소스: 한국관광공사_국문 관광정보 API (searchKeyword1)
   - 출력: 여행지 리스트(item 배열)

2) 여행지 필터링 기능
   - 필터 기준: 테마, 이동 거리, 타입(실내/실외), 난이도, 체류 시간
   - FastAPI 내부 함수로 구현

3) AI 여행 코스 생성 기능 (LangChain + LLM)
   - 사용자의 자연어 쿼리 입력을 기반으로 여행지 후보 리스트를 조합해 여행 코스 생성
   - Prompt Template 기반
   - 출력 형식(JSON):
     {
        "course": [
          {"name": "장소명", "description": "간단설명", "time": "예상소요시간"}
        ]
     }

4) RAG 기반 여행지 설명 요약
   - 여행지 상세 내용(text) → VectorDB(Chroma 등)에 저장
   - 코스 생성 시 관련 문서 검색 후 LLM에 전달

5) FastAPI API 엔드포인트
   - POST /travel/search  
       입력: { "region": "부산", "keyword": "바다" }
       출력: MCP tool 결과 리스트

   - POST /travel/recommend  
       입력: { "query": "부산에서 3시간 바다 코스 추천" }
       내부 동작:  
          a) MCP tool로 여행지 검색  
          b) 필터링  
          c) LangChain + RAG 기반 LLM 코스 생성  
       출력: 여행 코스 JSON

6) 폴더 구조(권장)
backend/
  app/
    main.py
    api/travel.py
    mcp/server.py
    mcp/tourism_tool.py
    llm/chain.py
    llm/rag.py
    db/tourism_cache.json
  Dockerfile
  requirements.txt

7) LLM Prompt 요구사항
   - 사용자 쿼리 요약
   - MCP에서 받은 여행지 리스트를 기반으로 코스 추천
   - 여행 시간 고려
   - 장소 설명은 RAG 검색 기반 요약
   - JSON만 반환하도록 지시

8) 성공 조건
   - 공공데이터 API 정상 요청/파싱
   - FastAPI → MCP → LLM 흐름 작동
   - 여행 코스 JSON 생성 성공률 90% 이상
   - 예외 상황(검색결과 없음 등) 처리 포함

9) 테스트 요구사항
   - “부산 바다 코스 추천해줘”
   - “서울 실내 위주 데이트 코스”
   - “가족이랑 갈만한 제주도 반나절 여행지”

10) 비기능 요구사항
   - API 응답 속도 2초 이하
   - JSON output 보장
   - LLM hallucination 최소화를 위한 RAG 사용

