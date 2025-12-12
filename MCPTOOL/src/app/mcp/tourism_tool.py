"""공공데이터포털 관광정보 API 연동 MCP Tool"""
import httpx
from typing import List, Dict, Optional, Any
from urllib.parse import quote
from app.utils.config import settings
from app.utils.area_code import get_area_code, normalize_region


async def search_tourism_keyword(
    region: Optional[str] = None,
    keyword: Optional[str] = None,
    area_code: Optional[str] = None,
    num_of_rows: int = 10,
    page_no: int = 1
) -> Dict[str, Any]:
    """
    한국관광공사 관광정보 키워드 검색
    
    주의: 공공데이터 API가 500 에러를 반환하는 경우, API 키 확인이 필요합니다.
    - 공공데이터포털에서 API 키가 활성화되어 있는지 확인
    - API 키가 올바른 서비스에 연결되어 있는지 확인
    """
    """
    한국관광공사 관광정보 키워드 검색
    
    Args:
        region: 지역명 (예: "부산", "서울")
        keyword: 검색 키워드
        area_code: 지역 코드 (region이 없을 경우)
        num_of_rows: 반환 개수
        page_no: 페이지 번호
    
    Returns:
        API 응답 결과 딕셔너리
    """
    # 지역 코드 처리
    if region and not area_code:
        normalized_region = normalize_region(region)
        area_code = get_area_code(normalized_region) if normalized_region else None
    
    # API 파라미터 설정
    # serviceKey는 URL 인코딩이 필요할 수 있음 (공공데이터 API 요구사항)
    service_key = settings.tourism_api_key
    # 이미 인코딩되어 있지 않다면 인코딩 시도
    if '%' not in service_key:
        service_key = quote(service_key, safe='')
    
    params = {
        "serviceKey": service_key,
        "numOfRows": num_of_rows,
        "pageNo": page_no,
        "MobileOS": "ETC",
        "MobileApp": "TravelGenie",
        "_type": "json",
    }
    
    # keyword는 필수일 수 있음 (searchKeyword1 API 특성)
    if keyword:
        params["keyword"] = keyword
    else:
        # keyword가 없으면 기본값 사용
        params["keyword"] = "관광"
    
    if area_code:
        params["areaCode"] = area_code
    
    # API 요청
    try:
        # 요청 URL 생성 (디버깅용)
        import logging
        logger = logging.getLogger(__name__)
        
        # 요청 정보 로깅 (serviceKey는 마스킹)
        debug_params = params.copy()
        if "serviceKey" in debug_params:
            debug_params["serviceKey"] = f"{debug_params['serviceKey'][:10]}...{debug_params['serviceKey'][-10:]}"
        logger.debug(f"공공데이터 API 요청: {settings.tourism_api_url}, 파라미터: {debug_params}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.tourism_api_url, params=params)
            
            # 응답 본문 확인
            response_text = response.text
            
            # XML 응답인 경우 처리 (공공데이터 API는 때때로 XML로 에러 반환)
            if response_text.strip().startswith('<?xml') or response_text.strip().startswith('<'):
                # XML 파싱 시도
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(response_text)
                    error_msg = ""
                    for elem in root.iter():
                        if elem.tag in ['resultMsg', 'resultCode', 'message']:
                            error_msg += f"{elem.tag}: {elem.text} "
                    if error_msg:
                        raise Exception(f"API XML 에러 응답: {error_msg.strip()}")
                except ET.ParseError:
                    pass
            
            try:
                data = response.json()
            except Exception as json_error:
                # JSON 파싱 실패 시 텍스트 응답 확인
                text_response = response_text[:500]  # 처음 500자만
                raise Exception(f"API 응답 파싱 실패 (Status: {response.status_code}): {text_response}")
            
            # 에러 응답 확인
            if response.status_code != 200:
                error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "")
                error_code = data.get("response", {}).get("header", {}).get("resultCode", "")
                raise Exception(f"API 오류 (Code: {error_code}, Status: {response.status_code}): {error_msg}")
            
            # 응답 구조 파싱
            if "response" in data:
                header = data["response"].get("header", {})
                result_code = header.get("resultCode", "")
                
                # API 에러 코드 확인
                if result_code != "0000":
                    result_msg = header.get("resultMsg", "알 수 없는 오류")
                    raise Exception(f"API 오류 (Code: {result_code}): {result_msg}")
                
                body = data["response"].get("body", {})
                items = body.get("items", {})
                
                # items가 None이거나 비어있을 수 있음
                if not items:
                    return {
                        "total_count": 0,
                        "page_no": page_no,
                        "num_of_rows": num_of_rows,
                        "items": []
                    }
                
                item_list = items.get("item", [])
                
                # 단일 아이템인 경우 리스트로 변환
                if isinstance(item_list, dict):
                    item_list = [item_list]
                
                return {
                    "total_count": body.get("totalCount", 0),
                    "page_no": page_no,
                    "num_of_rows": num_of_rows,
                    "items": item_list if item_list else []
                }
            else:
                return {
                    "total_count": 0,
                    "page_no": page_no,
                    "num_of_rows": num_of_rows,
                    "items": []
                }
    
    except httpx.HTTPStatusError as e:
        error_detail = ""
        response_text = e.response.text.strip()
        
        # "Unexpected errors"는 보통 API 키 문제나 서버 문제
        if response_text == "Unexpected errors" or "Unexpected errors" in response_text:
            error_detail = " (공공데이터 API 서버 오류: 'Unexpected errors' - API 키 확인 필요 또는 서버 일시적 문제)"
        else:
            try:
                # JSON 응답 시도
                error_data = e.response.json()
                error_msg = error_data.get("response", {}).get("header", {}).get("resultMsg", "")
                error_code = error_data.get("response", {}).get("header", {}).get("resultCode", "")
                if error_msg or error_code:
                    error_detail = f" (Code: {error_code}, Msg: {error_msg})"
                else:
                    error_detail = f" (응답: {str(error_data)[:200]})"
            except:
                # 텍스트 응답
                error_detail = f" (응답: {response_text[:300]})"
        
        # 요청 URL 정보 (디버깅용, serviceKey는 제외)
        request_url = str(e.request.url)
        if "serviceKey" in request_url:
            # serviceKey 부분을 마스킹
            import re
            request_url = re.sub(r'serviceKey=[^&]+', 'serviceKey=***', request_url)
        
        error_message = f"API 요청 실패: HTTP {e.response.status_code}{error_detail}"
        if "Unexpected errors" in error_detail:
            error_message += "\n💡 해결 방법:\n"
            error_message += "1. 공공데이터포털(data.go.kr)에서 API 키가 활성화되어 있는지 확인\n"
            error_message += "2. API 키가 '한국관광공사_국문 관광정보 서비스'에 연결되어 있는지 확인\n"
            error_message += "3. API 서비스 신청 상태를 확인 (승인 대기 중일 수 있음)\n"
            error_message += "4. 잠시 후 다시 시도 (서버 일시적 문제일 수 있음)"
        
        raise Exception(error_message)
    except httpx.HTTPError as e:
        raise Exception(f"API 요청 실패: {str(e)}")
    except Exception as e:
        # 원본 에러 메시지 유지
        raise Exception(f"데이터 처리 실패: {str(e)}")


def format_tourism_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """여행지 아이템 포맷팅"""
    return {
        "contentid": item.get("contentid"),
        "contenttypeid": item.get("contenttypeid"),
        "title": item.get("title", ""),
        "addr1": item.get("addr1", ""),
        "addr2": item.get("addr2", ""),
        "mapx": item.get("mapx", ""),
        "mapy": item.get("mapy", ""),
        "tel": item.get("tel", ""),
        "firstimage": item.get("firstimage", ""),
        "firstimage2": item.get("firstimage2", ""),
    }

