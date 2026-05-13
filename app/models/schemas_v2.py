"""多选项输出数据模型 - 支持1-3个维修选项"""
from pydantic import BaseModel, Field
from typing import List, Literal


class RepairOption(BaseModel):
    """单个维修选项"""

    category: Literal[
        "物理破损与脱落",
        "机械卡阻与五金故障",
        "功能失效与环境异常",
        "安装/加固/拆卸需求",
        "未知/需人工确认"
    ] = Field(
        ...,
        description="问题分类，用于后台派单"
    )

    frontend_display_text: str = Field(
        ...,
        description="一句自然流畅的报修文案，如：'窗帘拉珠卡住了，拉不下来'"
    )


class RepairIntentResponseV2(BaseModel):
    """
    报修意图分析响应 - 多选项版本

    模型根据确定性输出1-3个选项供用户选择
    """

    internal_reasoning: str = Field(
        ...,
        description="内部推理过程（空间分析+状态演绎），不展示给用户"
    )

    suggested_options: List[RepairOption] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="建议的维修选项列表。如果完全确定只输出1个，如果存在歧义输出2-3个"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "internal_reasoning": "平视角度拍摄的门框特写，可见门与门框之间有明显缝隙，门体无破损。根据分支D逻辑，这种特写通常代表门关不上（地弹簧坏了）或者锁卡住了。提供两个选项供用户确认。",
                "suggested_options": [
                    {
                        "category": "机械卡阻与五金故障",
                        "frontend_display_text": "办公室玻璃门地弹簧坏了，门关不严有缝隙。"
                    },
                    {
                        "category": "机械卡阻与五金故障",
                        "frontend_display_text": "门锁卡住了关不上，请安排维修。"
                    }
                ]
            }
        }
