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
from app.services.llm_agent import analyze_repair_image
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
                        "data": {
                            "is_valid_image": True,
                            "object_name": "空调出风口盖板",
                            "issue_description": "盖板脱落",
                            "reasoning": "图片显示白色塑料盖板与主体分离，地上可见脱落的盖板",
                            "category": "物理损坏",
                            "confidence": "High",
                            "location": None,
                            "urgency": "Medium"
                        },
                        "metadata": {
                            "processing_time": 2.35,
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
    - `is_valid_image`: 图片是否有效（清晰且包含设施）
    - `object_name`: 识别的物件名称（尽可能具体）
    - `issue_description`: 故障或需求描述
    - `reasoning`: AI 推理原因（说明从图片中看到了什么）
    - `category`: 问题分类（物理损坏/功能故障/异常状态/安装加固需求/未知）
    - `confidence`: 置信度（High/Medium/Low）
    - `location`: 位置信息（仅提取图片中能看到的，如门牌号）
    - `urgency`: 紧急程度（High/Medium/Low）

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

        # 4. 调用 LLM 分析图片
        try:
            result = await analyze_repair_image(base64_image)
            logger.info(f"LLM 分析完成: {result.get('object_name', 'N/A')}, "
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

        # 6. 构造响应
        response_data = {
            "success": True,
            "data": result,
            "metadata": {
                "processing_time": processing_time,
                "image_size": f"{image_info['width']}x{image_info['height']}" if image_info else "unknown"
            }
        }

        # 7. 添加低置信度警告
        if result.get("confidence") == "Low":
            response_data["warning"] = {
                "code": "LOW_CONFIDENCE",
                "message": "AI 置信度较低，建议人工确认分析结果"
            }
            logger.warning(f"低置信度结果: {result.get('object_name')}")

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
