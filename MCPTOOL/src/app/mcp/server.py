"""MCP Server 구현"""
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from app.mcp.tourism_tool import search_tourism_keyword, format_tourism_item
import asyncio
import json


# MCP 서버 인스턴스 생성
app = Server("travelgenie-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        Tool(
            name="tourism_search",
            description="한국관광공사 관광정보 API를 사용하여 여행지를 검색합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "지역명 (예: 부산, 서울, 제주도 등)"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "검색 키워드 (예: 바다, 데이트, 카페 등)"
                    },
                    "area_code": {
                        "type": "string",
                        "description": "지역 코드 (선택사항, region 대신 사용 가능)"
                    },
                    "num_of_rows": {
                        "type": "integer",
                        "description": "반환할 결과 개수 (기본값: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 호출 처리"""
    if name == "tourism_search":
        try:
            result = await search_tourism_keyword(
                region=arguments.get("region"),
                keyword=arguments.get("keyword"),
                area_code=arguments.get("area_code"),
                num_of_rows=arguments.get("num_of_rows", 10)
            )
            
            # 결과 포맷팅
            items = [format_tourism_item(item) for item in result.get("items", [])]
            
            return [
                TextContent(
                    type="text",
                    text=f"검색 결과: 총 {result.get('total_count', 0)}개\n"
                         f"{json.dumps(items, ensure_ascii=False, indent=2)}"
                )
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"오류 발생: {str(e)}"
                )
            ]
    else:
        return [
            TextContent(
                type="text",
                text=f"알 수 없는 도구: {name}"
            )
        ]


async def run_mcp_server():
    """MCP 서버 실행"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(run_mcp_server())

