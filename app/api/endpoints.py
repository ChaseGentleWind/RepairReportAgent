from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import time

from app.models.schemas_v2 import RepairIntentResponseV2 as RepairIntentResponse
from app.services.image_utils import (
    process_and_encode_image,
    validate_image_file,
    get_image_info
)
from app.agents.repair_agent import get_agent
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/api/v1", tags=["repair-analysis"])


@router.post(
    "/analyze-repair",
    response_model=dict,
    summary="分析报修图片",
    description="上传报修图片，AI 自动识别物件、故障描述和问题分类",
    responses={
        200: {
            "description": "分析成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "suggested_option": "车库倒车杆被撞弯变形，需要派人维修或更换。",
                        "reply": "车库倒车杆被撞弯变形，需要派人维修或更换。",
                        "dispatch_info": {
                            "专业工种": "装修技工",
                            "工单类型": "WH公共工单",
                            "响应时限": "30分钟到场",
                            "参考规程": "QHKC-WI-MT-01 §5.4"
                        },
                        "rag_used": True,
                        "metadata": {
                            "processing_time": 2.8,
                            "image_size": "800x600"
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求错误（图片格式不支持、图片无效等）",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "INVALID_IMAGE_FORMAT",
                            "message": "不支持的文件格式: text/plain"
                        }
                    }
                }
            }
        },
        500: {
            "description": "服务器错误（LLM 调用失败等）",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "LLM_ANALYSIS_FAILED",
                            "message": "图片分析失败: API timeout"
                        }
                    }
                }
            }
        }
    }
)
async def analyze_repair(
    file: UploadFile = File(..., description="报修图片文件（支持 JPEG, PNG, WebP 等格式）")
) -> JSONResponse:
    """
    分析报修图片接口

    **流程：**
    1. 验证图片格式
    2. 压缩并编码图片为 Base64
    3. 调用 LLM 进行视觉推理
    4. 返回结构化的报修意图

    **支持的图片格式：**
    - JPEG / JPG
    - PNG
    - WebP
    - GIF
    - BMP
    - TIFF

    **返回字段说明：**
    - `success`: 请求是否成功
    - `reply`: 面向用户的一句话报修描述，直接用于前端展示和工单系统
    - `metadata`: 元数据信息
      - `processing_time`: 处理耗时（秒）
      - `image_size`: 图片尺寸

    **注意事项：**
    - 图片会自动压缩（长边最大 1024px）
    - 置信度为 Low 时建议人工确认
    - 无效图片会被自动驳回
    - AI 仅通过图片推理，不依赖任何文字描述
    """
    start_time = time.time()
    image_info = None

    try:
        logger.info(f"收到报修图片分析请求: {file.filename}")

        # 1. 验证图片格式
        try:
            validate_image_file(file)
            logger.info(f"图片格式验证通过: {file.content_type}")
        except HTTPException as e:
            logger.warning(f"图片格式验证失败: {e.detail}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "INVALID_IMAGE_FORMAT",
                        "message": e.detail
                    }
                }
            )

        # 2. 获取图片信息（用于日志和元数据）
        try:
            image_info = await get_image_info(file)
            logger.info(f"图片信息: {image_info['width']}x{image_info['height']}, "
                       f"大小: {image_info['size']} bytes")
        except Exception as e:
            logger.warning(f"获取图片信息失败: {e}")
            # 不影响主流程，继续执行

        # 3. 处理并编码图片
        try:
            base64_image = await process_and_encode_image(
                file,
                max_size=settings.MAX_IMAGE_SIZE
            )
            logger.info(f"图片处理完成，Base64 长度: {len(base64_image)}")
        except HTTPException as e:
            logger.error(f"图片处理失败: {e.detail}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "IMAGE_PROCESSING_FAILED",
                        "message": e.detail
                    }
                }
            )
        except Exception as e:
            logger.error(f"图片处理异常: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "IMAGE_PROCESSING_ERROR",
                        "message": f"图片处理失败: {str(e)}"
                    }
                }
            )

        # 4. 调用 LangChain Agent 分析图片
        try:
            agent = get_agent()
            result = await agent.analyze(base64_image)
            logger.info(f"LangChain Agent 分析完成: {result.get('object_name', 'N/A')}, "
                       f"置信度: {result.get('confidence', 'N/A')}")
        except Exception as e:
            logger.error(f"LLM 分析失败: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "LLM_ANALYSIS_FAILED",
                        "message": f"图片分析失败: {str(e)}"
                    }
                }
            )

        # 5. 计算处理时间
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"请求处理完成，耗时: {processing_time}s")

        # 6. 构造响应（observation 字段丢弃，不透传给前端）
        suggested = result.get("reply")
        response_data = {
            "success": True,
            "suggested_option": suggested,
            "reply": suggested,  # 向后兼容
            "dispatch_info": result.get("dispatch_info"),
            "rag_used": result.get("rag_used", False),
            "metadata": {
                "processing_time": processing_time,
                "image_size": f"{image_info['width']}x{image_info['height']}" if image_info else "unknown",
            }
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )

    except Exception as e:
        # 捕获所有未预期的异常
        logger.error(f"未预期的错误: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "服务器内部错误，请稍后重试"
                }
            }
        )


@router.get(
    "/health",
    summary="健康检查",
    description="检查 API 服务是否正常运行",
    tags=["health"]
)
async def health_check():
    """
    健康检查接口

    返回服务状态和配置信息
    """
    return {
        "status": "healthy",
        "service": "Repair Report Agent API",
        "version": "1.0.0",
        "model": settings.MODEL_NAME,
        "max_image_size": settings.MAX_IMAGE_SIZE
    }


@router.get(
    "/models",
    summary="获取支持的模型列表",
    description="返回当前配置的模型信息",
    tags=["info"]
)
async def get_models():
    """
    获取模型信息接口

    返回当前使用的模型和支持的模型列表
    """
    return {
        "current_model": settings.MODEL_NAME,
        "supported_models": [
            {
                "name": "qwen3.5-omni-flash",
                "description": "通义千问 3.5 全模态闪电版（极速响应）",
                "recommended": True
            },
            {
                "name": "qwen-vl-max",
                "description": "通义千问视觉理解旗舰版（高精度）",
                "recommended": False
            },
            {
                "name": "qwen-vl-plus",
                "description": "通义千问视觉理解增强版（平衡性能）",
                "recommended": False
            }
        ]
    }
