import json
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts_v2 import REPAIR_AGENT_SYSTEM_PROMPT_V2 as REPAIR_AGENT_SYSTEM_PROMPT
from app.models.schemas_v2 import RepairIntentResponseV2 as RepairIntentResponse

# 配置日志
logger = logging.getLogger(__name__)


class RepairAnalysisAgent:
    """报修图片分析 Agent"""

    def __init__(self):
        """初始化 Agent，配置通义千问 API 客户端"""
        self.client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.API_BASE_URL
        )
        self.model_name = settings.MODEL_NAME

    def _parse_llm_response(self, content: str) -> dict:
        """
        解析 LLM 响应，处理各种可能的格式问题

        Args:
            content: LLM 返回的原始内容

        Returns:
            dict: 解析后的 JSON 对象

        Raises:
            json.JSONDecodeError: 解析失败时抛出
        """
        # 1. 去除首尾空白
        content = content.strip()

        # 2. 使用括号匹配提取完整的 JSON 对象（统一处理所有情况）
        start = content.find("{")
        if start == -1:
            raise json.JSONDecodeError("未找到 JSON 对象", content, 0)

        # 使用栈匹配括号
        brace_count = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == "{":
                brace_count += 1
            elif content[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if brace_count != 0:
            raise json.JSONDecodeError("JSON 对象不完整", content, start)

        # 提取并解析
        json_str = content[start:end]
        return json.loads(json_str)

    async def analyze_repair_image(
        self,
        base64_image: str,
        temperature: float = 0.1,
        max_retries: int = 3
    ) -> RepairIntentResponse:
        """
        分析报修图片，返回结构化的报修意图

        Args:
            base64_image: Base64 编码的图片 Data URI
            temperature: 模型温度参数（0-1，越低越确定）
            max_retries: 最大重试次数

        Returns:
            RepairIntentResponse: 结构化的报修意图响应

        Raises:
            Exception: API 调用失败或解析失败时抛出异常
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"开始分析报修图片 (尝试 {attempt + 1}/{max_retries})")

                # 构造消息
                messages = [
                    {
                        "role": "system",
                        "content": REPAIR_AGENT_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "请分析这张报修图片，严格按照 JSON Schema 返回结果。"
                            }
                        ]
                    }
                ]

                # 调用大模型 API
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},  # 强制 JSON 输出
                    max_tokens=1000
                )

                # 提取响应内容
                content = response.choices[0].message.content
                logger.info(f"LLM 原始响应: {content[:200]}...")

                # 清理和解析 JSON
                result_dict = self._parse_llm_response(content)

                # 验证并转换为 Pydantic 模型
                repair_response = RepairIntentResponse(**result_dict)

                logger.info(f"分析完成: {repair_response.object_name}, 置信度: {repair_response.confidence}")
                return repair_response

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"JSON 解析失败: {str(e)}")

            except Exception as e:
                logger.error(f"分析失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"图片分析失败: {str(e)}")

        raise Exception("达到最大重试次数，分析失败")


# 全局 Agent 实例
_agent_instance: Optional[RepairAnalysisAgent] = None


def get_agent() -> RepairAnalysisAgent:
    """获取全局 Agent 实例（单例模式）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RepairAnalysisAgent()
    return _agent_instance


async def analyze_repair_image(base64_image: str) -> dict:
    """
    分析报修图片的便捷函数

    Args:
        base64_image: Base64 编码的图片 Data URI

    Returns:
        dict: 报修意图分析结果（字典格式）
    """
    agent = get_agent()
    result = await agent.analyze_repair_image(base64_image)
    return result.model_dump()
