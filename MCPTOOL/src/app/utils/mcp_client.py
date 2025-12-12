"""MCP Tool을 FastAPI에서 직접 호출하기 위한 클라이언트"""
from app.mcp.tourism_tool import search_tourism_keyword, format_tourism_item
from typing import Optional, List, Dict, Any


async def call_tourism_search(
    region: Optional[str] = None,
    keyword: Optional[str] = None,
    area_code: Optional[str] = None,
    num_of_rows: int = 10
) -> Dict[str, Any]:
    """
    MCP Tool의 tourism_search를 직접 호출
    
    FastAPI에서는 MCP Server를 거치지 않고 직접 함수를 호출합니다.
    """
    result = await search_tourism_keyword(
        region=region,
        keyword=keyword,
        area_code=area_code,
        num_of_rows=num_of_rows
    )
    
    items = [format_tourism_item(item) for item in result.get("items", [])]
    
    return {
        "total_count": result.get("total_count", 0),
        "items": items
    }

