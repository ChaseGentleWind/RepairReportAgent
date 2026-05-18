from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import router as api_router

app = FastAPI(
    title="Repair Report Agent API",
    description="多模态 AI Agent 后端服务 - 报修图片智能识别与意图分析",
    version="1.0.0",
    debug=settings.DEBUG
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)


@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "status": "ok",
        "message": "Repair Report Agent API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze_repair": "/api/v1/analyze-repair",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "model": settings.MODEL_NAME,
        "api_configured": bool(settings.DASHSCOPE_API_KEY and
                              settings.DASHSCOPE_API_KEY != "your_dashscope_api_key_here")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
