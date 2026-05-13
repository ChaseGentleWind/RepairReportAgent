"""简化版数据模型 - 只保留核心维修信息"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class RepairIntentResponseV2(BaseModel):
    """
    报修意图分析响应 - 简化版

    只保留核心维修相关字段，移除元数据字段
    """

    is_valid_image: bool = Field(
        ...,
        description="图片是否有效（清晰且包含办公设施）"
    )

    rejection_reason: Optional[str] = Field(
        None,
        description="如果图片无效，说明驳回原因"
    )

    spatial_and_state_analysis: Optional[str] = Field(
        None,
        description="空间与状态分析：描述看到的方向、线索，设备表面是否有可见损坏"
    )

    object_name: Optional[str] = Field(
        None,
        description="识别出的主要物件名称（尽可能具体，如'空调出风口盖板'）"
    )

    issue_description: Optional[str] = Field(
        None,
        description="问题的简短描述"
    )

    reasoning: Optional[str] = Field(
        None,
        description="推理过程，说明从图片中看到了什么"
    )

    category: Literal[
        "物理破损与脱落",
        "机械卡阻与五金故障",
        "功能失效与环境异常",
        "安装/加固/拆卸需求",
        "未知/需人工确认"
    ] = Field(
        ...,
        description="问题分类"
    )

    confidence: Literal["High", "Medium", "Low"] = Field(
        ...,
        description="置信度"
    )

    location: Optional[str] = Field(
        None,
        description="位置信息（仅提取图片中能看到的，如门牌号、标识牌）"
    )

    urgency: Literal["High", "Medium", "Low"] = Field(
        default="Medium",
        description="紧急程度: High(紧急)/Medium(一般)/Low(不紧急)"
    )

    frontend_display_text: Optional[str] = Field(
        None,
        description="一句自然流畅的中文，结合了物件、问题和需要的服务。直接用于前端展示。"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid_image": True,
                "rejection_reason": None,
                "spatial_and_state_analysis": "平视角度拍摄的门框特写，可见门与门框之间有明显缝隙",
                "object_name": "办公室玻璃门",
                "issue_description": "门关不严，有缝隙",
                "reasoning": "根据分支D推理：门看起来完好但拍摄特写缝隙，通常代表门关不上或地弹簧故障",
                "category": "机械卡阻与五金故障",
                "confidence": "Medium",
                "location": None,
                "urgency": "Medium",
                "frontend_display_text": "办公室玻璃门关不严有缝隙，请安排维修。"
            }
        }


# 保持向后兼容
class RepairIntentResponse(BaseModel):
    """
    报修意图分析响应 - 原版（向后兼容）
    """
    is_valid_image: bool
    rejection_reason: Optional[str] = None
    object_name: Optional[str] = None
    issue_description: Optional[str] = None
    reasoning: Optional[str] = None
    category: str
    confidence: str
