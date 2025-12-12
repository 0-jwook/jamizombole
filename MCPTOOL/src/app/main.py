"""FastAPI 메인 애플리케이션"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import travel
from app.utils.config import settings
import uvicorn






# FastAPI 앱 생성
app = FastAPI(
    title="TravelGenie API",
    description="AI 여행 코스 추천 서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(travel.router)

# @app.on_event("startup")
# async def debug_settings():
#     print("===== DEBUG SETTINGS =====")
#     print("OPENAI KEY:", settings.openai_api_key)
#     print("ENV PATH:", settings.model_config["env_file"])
#     print("==========================")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "TravelGenie API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/travel/search",
            "recommend": "/travel/recommend",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )

