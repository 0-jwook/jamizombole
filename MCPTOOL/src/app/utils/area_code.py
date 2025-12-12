"""지역 코드 매핑 유틸리티"""
from typing import Dict, Optional


# 한국관광공사 지역 코드
AREA_CODES: Dict[str, str] = {
    "서울": "1",
    "인천": "2",
    "대전": "3",
    "대구": "4",
    "광주": "5",
    "부산": "6",
    "울산": "7",
    "세종": "8",
    "경기": "31",
    "강원": "32",
    "충북": "33",
    "충남": "34",
    "경북": "35",
    "경남": "36",
    "전북": "37",
    "전남": "38",
    "제주": "39",
}


def get_area_code(region: str) -> Optional[str]:
    """지역명으로부터 지역 코드 반환"""
    return AREA_CODES.get(region)


def normalize_region(region: str) -> Optional[str]:
    """지역명 정규화 (예: '서울시' -> '서울')"""
    region = region.strip()
    
    # '시', '도', '특별시', '광역시' 제거
    region = region.replace("특별시", "").replace("광역시", "").replace("시", "").replace("도", "").strip()
    
    # 매핑 확인
    if region in AREA_CODES:
        return region
    
    # 부분 매칭 시도
    for key in AREA_CODES.keys():
        if key in region or region in key:
            return key
    
    return None

