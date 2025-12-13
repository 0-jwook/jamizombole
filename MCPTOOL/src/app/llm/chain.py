"""LangChain 기반 여행 코스 생성 체인"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.utils.config import settings
import json
import google.generativeai as genai


# ==========================
# Pydantic 모델
# ==========================
class CourseItem(BaseModel):
    name: str = Field(description="장소명")
    description: str = Field(description="간단한 설명")
    address: str = Field(description="주소")
    type: str = Field(description="장소 유형 (예: 관광지, 식당, 카페)")
    time: str = Field(description="예상 소요 시간 (예: 1시간, 30분)")


class TravelCourse(BaseModel):
    course: List[CourseItem] = Field(description="여행 코스 아이템 리스트")
    summary: str = Field(description="전체 코스에 대한 간단한 설명")


# ==========================
# 코스 생성기
# ==========================
class CourseGenerator:
    def __init__(self):
        # Google Gemini 클라이언트 초기화
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.temperature = settings.temperature

        # 프롬프트 템플릿
        self.prompt_template = """
당신은 전문 여행 코스 추천 AI입니다.
제공된 여행지 정보를 기반으로 최적의 여행 코스를 생성하세요.

규칙:
1. 사용자의 쿼리(지역/시간/테마)를 정확히 분석
2. 제공된 여행지 정보를 활용
3. 이동 시간, 체류 시간 현실적으로 반영
4. 코스는 최소 2개, 최대 6개
5. 전체 코스의 총 소요시간은 5시간 내외로 구성
6. 반드시 course와 summary 필드를 모두 포함해야 함
7. JSON만 출력 (추가 설명 금지)

출력 형식:
{{
  "course": [
    {{
      "name": "장소명",
      "description": "간단한 설명",
      "address": "주소",
      "type": "장소 유형",
      "time": "1시간"
    }}
  ],
  "summary": "이 코스는 OO의 주요 명소를 5시간 동안 둘러보는 코스입니다."
}}

사용자 요청:
{query}

여행지 정보:
{context}

JSON만 반환하세요.
"""

    # ==========================
    # 여행 코스 생성
    # ==========================
    async def generate_course(
        self,
        query: str,
        context: str,
        tourism_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        try:
            # 프롬프트 생성
            prompt = self.prompt_template.format(
                query=query,
                context=context
            )

            # Gemini 호출
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                )
            )
            content = response.text

            # None 방지
            if not content:
                raise ValueError("모델 응답이 비어 있습니다.")

            content = str(content).strip()

            # 코드블럭 제거
            if "```" in content:
                part = content.split("```")
                if len(part) > 1:
                    content = part[1].replace("json", "").strip()

            # JSON 파싱
            data = json.loads(content)

            # 리스트가 직접 반환된 경우 처리
            if isinstance(data, list):
                data = {"course": data, "summary": "여행 코스가 생성되었습니다."}

            # summary 필드가 없는 경우 기본값 추가
            if "summary" not in data:
                course_count = len(data.get("course", []))
                data["summary"] = f"총 {course_count}개의 장소를 둘러보는 여행 코스입니다."

            # Pydantic 검증
            validated = TravelCourse(**data)
            return validated.model_dump()

        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"오류 발생: {error_msg}")
            print(traceback.format_exc())
            return {
                "course": [
                    {
                        "name": "오류",
                        "description": f"코스 생성에 실패했습니다: {error_msg}",
                        "time": "0분"
                    }
                ]
            }

    # ==========================
    # 여행지 정보 포맷팅
    # ==========================
    def format_tourism_items_for_context(self, items: List[Dict[str, Any]]) -> str:
        formatted = []

        for idx, item in enumerate(items[:10], 1):
            title = item.get("title", "이름 없음") or ""
            addr = item.get("addr1") or item.get("addr2") or ""
            tel = item.get("tel", "") or ""
            ctype = item.get("contenttypeid", "") or ""

            formatted.append(
                f"{idx}. {title}\n"
                f"   주소: {addr}\n"
                f"   전화: {tel}\n"
                f"   유형: {ctype}"
            )

        return "\n\n".join(formatted)


# ==========================
# 싱글톤 생성기
# ==========================
_course_generator: Optional[CourseGenerator] = None


def get_course_generator() -> CourseGenerator:
    global _course_generator
    if _course_generator is None:
        _course_generator = CourseGenerator()
    return _course_generator
