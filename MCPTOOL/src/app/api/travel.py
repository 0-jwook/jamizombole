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
        
        # 2. 쿼리에서 지역과 키워드 추출 (간단한 휴리스틱)
        region = None
        keyword = None
        
        # 지역 추출
        for area in ["부산", "서울", "제주", "인천", "대전", "대구", "광주", "울산", 
                     "경기", "강원", "충북", "충남", "경북", "경남", "전북", "전남"]:
            if area in request.query:
                region = area
                break
        
        # 키워드 추출 (일반적인 여행 키워드)
        query_lower = request.query.lower()
        keyword_candidates = {
            "바다": ["바다", "해수욕장", "해변", "해안"],
            "산": ["산", "등산", "하이킹"],
            "카페": ["카페", "커피"],
            "데이트": ["데이트", "연인"],
            "가족": ["가족", "아이"],
            "맛집": ["맛집", "음식", "레스토랑"],
            "문화": ["문화", "박물관", "미술관"],
            "쇼핑": ["쇼핑", "마켓"],
        }
        
        for key, values in keyword_candidates.items():
            if any(v in query_lower for v in values):
                keyword = key
                break
        
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

