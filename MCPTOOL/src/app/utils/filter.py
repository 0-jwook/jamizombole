"""여행지 필터링 기능"""
from typing import List, Dict, Any, Optional


def filter_tourism_items(
    items: List[Dict[str, Any]],
    theme: Optional[str] = None,
    indoor_outdoor: Optional[str] = None,
    difficulty: Optional[str] = None,
    min_time: Optional[int] = None,
    max_time: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    여행지 아이템 필터링
    
    Args:
        items: 여행지 아이템 리스트
        theme: 테마 (예: "데이트", "가족", "힐링" 등)
        indoor_outdoor: 실내/실외 구분 ("indoor", "outdoor")
        difficulty: 난이도 ("easy", "medium", "hard")
        min_time: 최소 체류 시간 (분)
        max_time: 최대 체류 시간 (분)
    
    Returns:
        필터링된 여행지 아이템 리스트
    """
    filtered = items.copy()
    
    # 테마 필터링 (제목 또는 설명에 키워드 포함 여부)
    if theme:
        theme_keywords = {
            "데이트": ["카페", "레스토랑", "공원", "전시", "영화"],
            "가족": ["공원", "박물관", "체험", "놀이", "아이"],
            "힐링": ["산", "바다", "공원", "카페", "스파"],
            "문화": ["박물관", "미술관", "전시", "공연", "역사"],
            "야경": ["타워", "전망", "다리", "산"],
        }
        
        keywords = theme_keywords.get(theme, [theme])
        
        def matches_theme(item):
            title = item.get("title", "").lower()
            for keyword in keywords:
                if keyword.lower() in title:
                    return True
            return False
        
        filtered = [item for item in filtered if matches_theme(item)]
    
    # 실내/실외 필터링 (간단한 휴리스틱)
    if indoor_outdoor:
        indoor_keywords = ["실내", "미술관", "박물관", "카페", "레스토랑", "쇼핑", "영화"]
        outdoor_keywords = ["산", "바다", "공원", "해변", "등산", "산책"]
        
        def is_indoor_or_outdoor(item, is_indoor: bool):
            title = item.get("title", "").lower()
            addr = (item.get("addr1", "") + item.get("addr2", "")).lower()
            text = title + " " + addr
            
            keywords = indoor_keywords if is_indoor else outdoor_keywords
            for keyword in keywords:
                if keyword in text:
                    return True
            return False
        
        is_indoor = indoor_outdoor.lower() == "indoor"
        filtered = [item for item in filtered if is_indoor_or_outdoor(item, is_indoor)]
    
    return filtered


def extract_filters_from_query(query: str) -> Dict[str, Any]:
    """
    자연어 쿼리에서 필터 조건 추출
    
    Args:
        query: 사용자 쿼리
    
    Returns:
        필터 조건 딕셔너리
    """
    query_lower = query.lower()
    filters = {}
    
    # 테마 추출
    if "데이트" in query_lower or "연인" in query_lower:
        filters["theme"] = "데이트"
    elif "가족" in query_lower or "아이" in query_lower or "아이들" in query_lower:
        filters["theme"] = "가족"
    elif "힐링" in query_lower:
        filters["theme"] = "힐링"
    elif "문화" in query_lower:
        filters["theme"] = "문화"
    
    # 실내/실외 추출
    if "실내" in query_lower:
        filters["indoor_outdoor"] = "indoor"
    elif "야외" in query_lower or "실외" in query_lower or "바깥" in query_lower:
        filters["indoor_outdoor"] = "outdoor"
    
    # 시간 추출 (예: "3시간", "반나절", "하루" 등)
    if "반나절" in query_lower or "반 날" in query_lower:
        filters["max_time"] = 240  # 4시간
    elif "하루" in query_lower or "일일" in query_lower:
        filters["max_time"] = 480  # 8시간
    elif "2시간" in query_lower:
        filters["max_time"] = 120
    elif "3시간" in query_lower:
        filters["max_time"] = 180
    elif "4시간" in query_lower:
        filters["max_time"] = 240
    
    return filters

