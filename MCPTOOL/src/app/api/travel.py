"""여행 관련 API 엔드포인트"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.mcp.tourism_tool import search_tourism_keyword, format_tourism_item
from app.utils.filter import filter_tourism_items, extract_filters_from_query
from app.llm.rag import get_rag
from app.llm.chain import get_course_generator
from fastapi.responses import ORJSONResponse

import asyncio


router = APIRouter(prefix="/travel", tags=["travel"])


class SearchRequest(BaseModel):
    """여행지 검색 요청"""
    region: Optional[str] = Field(None, description="지역명 (예: 부산, 서울)")
    keyword: Optional[str] = Field(None, description="검색 키워드")
    num_of_rows: int = Field(10, description="반환 개수")


class SearchResponse(BaseModel):
    """여행지 검색 응답"""
    total_count: int
    items: List[Dict[str, Any]]


class RecommendRequest(BaseModel):
    """여행 코스 추천 요청"""
    query: str = Field(..., description="자연어 쿼리 (예: '부산에서 3시간 바다 코스 추천')")


class RecommendResponse(BaseModel):
    """여행 코스 추천 응답"""
    course: List[Dict[str, Any]]
    summary: str = Field(description="전체 코스에 대한 간단한 설명")


@router.post("/search", response_model=SearchResponse)
async def search_tourism(request: SearchRequest):
    """
    여행지 검색 API
    
    MCP Tool을 사용하여 공공데이터포털에서 여행지 정보를 검색합니다.
    """
    try:
        # MCP Tool 호출
        result = await search_tourism_keyword(
            region=request.region,
            keyword=request.keyword,
            num_of_rows=request.num_of_rows
        )
        
        # 아이템 포맷팅
        items = [format_tourism_item(item) for item in result.get("items", [])]
        
        return SearchResponse(
            total_count=result.get("total_count", 0),
            items=items
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_course(request: RecommendRequest):
    """
    AI 여행 코스 추천 API
    
    사용자의 자연어 쿼리를 기반으로:
    1. MCP Tool로 여행지 검색
    2. 필터링
    3. RAG 기반 컨텍스트 생성
    4. LangChain + LLM으로 코스 생성
    """
    try:
        # 1. 쿼리에서 필터 조건 추출
        filters = extract_filters_from_query(request.query)
        
        #2. 쿼리에서 지역과 키워드 추출 (간단한 휴리스틱)
        region = None
        keyword = None
        
        # 지역 추출 (세부 지역 우선 매칭)
        areas = {
            # 서울 세부
            "강남": "서울", "강북": "서울", "홍대": "서울", "이태원": "서울", "명동": "서울",
            "종로": "서울", "잠실": "서울", "여의도": "서울", "신촌": "서울", "건대": "서울",
            # 부산 세부
            "해운대": "부산", "광안리": "부산", "남포동": "부산", "서면": "부산", "태종대": "부산",
            "기장": "부산", "영도": "부산", "다대포": "부산", "송도": "부산", "용호동": "부산",
            # 제주 세부
            "제주시": "제주", "서귀포": "제주", "애월": "제주", "성산": "제주", "중문": "제주",
            "우도": "제주", "한림": "제주", "표선": "제주",
            # 경기 세부
            "수원": "경기", "성남": "경기", "고양": "경기", "용인": "경기", "부천": "경기",
            "안산": "경기", "남양주": "경기", "안양": "경기", "평택": "경기", "시흥": "경기",
            "파주": "경기", "의정부": "경기", "김포": "경기", "광명": "경기", "광주": "경기",
            "군포": "경기", "하남": "경기", "오산": "경기", "양주": "경기", "이천": "경기",
            "구리": "경기", "안성": "경기", "포천": "경기", "의왕": "경기", "양평": "경기",
            "가평": "경기", "여주": "경기", "연천": "경기",
            # 강원 세부
            "춘천": "강원", "원주": "강원", "강릉": "강원", "동해": "강원", "속초": "강원",
            "삼척": "강원", "태백": "강원", "평창": "강원", "정선": "강원", "양양": "강원",
            "고성": "강원", "인제": "강원", "홍천": "강원", "횡성": "강원", "영월": "강원",
            # 경남 세부
            "창원": "경남", "김해": "경남", "진주": "경남", "양산": "경남", "거제": "경남",
            "통영": "경남", "사천": "경남", "밀양": "경남", "함안": "경남", "거창": "경남",
            "남해": "경남", "하동": "경남", "산청": "경남", "함양": "경남", "고성": "경남",
            # 경북 세부
            "포항": "경북", "경주": "경북", "구미": "경북", "안동": "경북", "영주": "경북",
            "영천": "경북", "상주": "경북", "문경": "경북", "김천": "경북", "경산": "경북",
            "울진": "경북", "울릉도": "경북", "청송": "경북", "영양": "경북",
            # 전남 세부
            "여수": "전남", "순천": "전남", "목포": "전남", "나주": "전남", "광양": "전남",
            "담양": "전남", "곡성": "전남", "구례": "전남", "보성": "전남", "고흥": "전남",
            "완도": "전남", "진도": "전남", "신안": "전남", "강진": "전남", "해남": "전남",
            # 전북 세부
            "전주": "전북", "익산": "전북", "군산": "전북", "정읍": "전북", "남원": "전북",
            "김제": "전북", "완주": "전북", "고창": "전북", "부안": "전북", "무주": "전북",
            # 충남 세부
            "천안": "충남", "아산": "충남", "서산": "충남", "논산": "충남", "계룡": "충남",
            "당진": "충남", "공주": "충남", "보령": "충남", "금산": "충남", "태안": "충남",
            # 충북 세부
            "청주": "충북", "충주": "충북", "제천": "충북", "단양": "충북", "음성": "충북",
            "진천": "충북", "괴산": "충북", "증평": "충북",
        }

        # 광역시
        main_cities = ["서울", "부산", "제주", "인천", "대전", "대구", "광주", "울산",
                      "경기", "강원", "충북", "충남", "경북", "경남", "전북", "전남"]

        # 세부 지역 우선 검색
        for sub_area, main_area in areas.items():
            if sub_area in request.query:
                region = main_area
                keyword = sub_area if sub_area != main_area else keyword
                break

        # 세부 지역이 없으면 광역 지역 검색
        if not region:
            for area in main_cities:
                if area in request.query:
                    region = area
                    break
        
        # 키워드 추출 (일반적인 여행 키워드)
        query_lower = request.query.lower()
        keyword_candidates = {
            # 자연/풍경
            "바다": ["바다", "해수욕장", "해변", "해안", "비치", "오션뷰", "일몰", "낚시"],
            "산": ["산", "등산", "하이킹", "트레킹", "계곡", "폭포", "숲", "자연"],
            "공원": ["공원", "정원", "수목원", "식물원", "공원"],
            "호수": ["호수", "저수지", "강", "물"],
            # 액티비티
            "체험": ["체험", "액티비티", "놀이", "테마파크", "워터파크"],
            "캠핑": ["캠핑", "글램핑", "차박", "오토캠핑"],
            "스포츠": ["스포츠", "골프", "수영", "서핑", "스키", "보드"],
            "자전거": ["자전거", "사이클", "자전거길"],
            # 문화/예술
            "문화": ["문화", "박물관", "미술관", "갤러리", "전시", "공연"],
            "역사": ["역사", "유적", "사적", "전통", "한옥", "고택", "사찰", "절"],
            "예술": ["예술", "공연", "음악", "연극", "영화"],
            # 음식/카페
            "맛집": ["맛집", "음식", "레스토랑", "식당", "요리", "미식"],
            "카페": ["카페", "커피", "디저트", "베이커리", "브런치"],
            "술": ["술", "바", "와인", "맥주", "포차", "전통주"],
            # 쇼핑/도심
            "쇼핑": ["쇼핑", "마켓", "시장", "아울렛", "백화점", "거리"],
            "야경": ["야경", "야시장", "밤", "나이트", "루프탑"],
            "도심": ["도심", "시내", "번화가", "중심가"],
            # 목적별
            "데이트": ["데이트", "연인", "커플", "로맨틱"],
            "가족": ["가족", "아이", "어린이", "키즈"],
            "힐링": ["힐링", "휴양", "쉼", "휴식", "조용한"],
            "사진": ["사진", "포토존", "인스타", "갬성", "감성"],
            "드라이브": ["드라이브", "드라이빙", "자동차"],
            # 계절/시간
            "봄": ["봄", "벚꽃", "꽃"],
            "여름": ["여름", "피서", "시원한"],
            "가을": ["가을", "단풍", "억새"],
            "겨울": ["겨울", "눈", "스키"],
            # 숙박/여행 스타일
            "펜션": ["펜션", "리조트", "호텔", "숙박"],
            "당일": ["당일", "일일", "하루"],
            "1박2일": ["1박", "숙박", "여행"],
        }

        # 키워드 우선순위 매칭 (구체적인 것 우선)
        matched_keyword = None
        for key, values in keyword_candidates.items():
            if any(v in query_lower for v in values):
                matched_keyword = key
                # 더 긴 매칭을 찾기 위해 계속 검색
                if len(values[0]) > 3:  # 구체적인 키워드 우선
                    keyword = matched_keyword
                    break

        if not matched_keyword:
            matched_keyword = keyword
        else:
            keyword = matched_keyword
        
        # 키워드가 없으면 기본값 사용
        if not keyword:
            keyword = "관광"
        
        # 3. MCP Tool로 여행지 검색
        items = []
        
        try:
            # 지역과 키워드로 검색 시도
            if region:
                search_result = await search_tourism_keyword(
                    region=region,
                    keyword=keyword,
                    num_of_rows=20
                )
                items = search_result.get("items", [])
                
                # 결과가 없으면 키워드 없이 재시도 (지역만으로)
                if not items:
                    try:
                        search_result = await search_tourism_keyword(
                            region=region,
                            keyword="관광",
                            num_of_rows=20
                        )
                        items = search_result.get("items", [])
                    except:
                        pass
            
            if not items:
                raise HTTPException(
                    status_code=404,
                    detail=f"'{region or '선택한 지역'}'에서 '{keyword}' 관련 여행지 검색 결과가 없습니다. 다른 지역이나 키워드로 시도해주세요."
                )
                
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e)
            # 에러 로깅 (디버깅용)
            import logging
            logging.error(f"여행지 검색 오류: {error_msg}")
            
            # 더 친화적인 에러 메시지 제공
            if "500" in error_msg or "Internal Server Error" in error_msg:
                raise HTTPException(
                    status_code=503,
                    detail=f"공공데이터 API 서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요. (상세: {error_msg[:200]})"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"여행지 검색 중 오류가 발생했습니다: {error_msg}"
                )
        
        # 4. 필터링 적용
        filtered_items = filter_tourism_items(
            items,
            theme=filters.get("theme"),
            indoor_outdoor=filters.get("indoor_outdoor"),
            max_time=filters.get("max_time")
        )
        
        # 필터링 결과가 없으면 원본 사용
        if not filtered_items:
            filtered_items = items[:10]
        else:
            filtered_items = filtered_items[:10]
        
        # 5. RAG 시스템에 문서 추가
        rag = get_rag()
        rag.add_tourism_documents(filtered_items)
        
        # 6. RAG로 컨텍스트 생성
        context = rag.get_context_for_course(filtered_items, request.query)
        
        # 여행지 정보도 컨텍스트에 포함
        course_generator = get_course_generator()
        items_context = course_generator.format_tourism_items_for_context(filtered_items)
        full_context = f"{context}\n\n{items_context}"
        
        # 7. LangChain + LLM으로 코스 생성
        course_result = await course_generator.generate_course(
            query=request.query,
            context=full_context,
            tourism_items=filtered_items
        )

        return RecommendResponse(**course_result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"코스 추천 중 오류 발생: {str(e)}")

