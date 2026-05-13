import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from app.models.schemas_v2 import RepairIntentResponseV2
from app.prompts.templates import get_repair_prompt
from app.core.config import settings

logger = logging.getLogger(__name__)


class RepairAnalysisAgent:
    """基于 LangChain 的报修图片分析 Agent"""

    def __init__(self):
        """初始化 Agent，配置 LangChain Chain"""
        # 1. 初始化 LLM（通义千问，兼容 OpenAI 接口）
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.API_BASE_URL,
            temperature=0.1,
            max_tokens=1000,
            model_kwargs={
                "response_format": {"type": "json_object"}  # 强制 JSON 输出
            },
        )

        # 2. 初始化 Pydantic 输出解析器
        self.parser = PydanticOutputParser(pydantic_object=RepairIntentResponseV2)

        # 3. 获取 Prompt 模板（注入 format_instructions）
        self.prompt = get_repair_prompt(self.parser.get_format_instructions())

        # 4. 构建 LCEL Chain（管道语法）
        self.chain = self.prompt | self.llm | self.parser

        logger.info(f"RepairAnalysisAgent 初始化完成，模型: {settings.MODEL_NAME}")

    async def analyze(self, base64_image: str) -> dict:
        """
        分析报修图片，返回结构化的报修意图

        Args:
            base64_image: Base64 编码的图片 Data URI

        Returns:
            dict: 报修意图分析结果（字典格式）

        Raises:
            Exception: LangChain Chain 调用失败时抛出异常
        """
        try:
            logger.info("开始调用 LangChain Chain 分析报修图片")

            # 调用 Chain（异步）
            result = await self.chain.ainvoke({"image_url": base64_image})

            logger.info(
                f"LangChain 分析完成，返回 {len(result.suggested_options)} 个选项"
            )

            # 转换为字典返回
            return result.model_dump()

        except Exception as e:
            logger.error(f"LangChain Chain 调用失败: {str(e)}")
            raise Exception(f"图片分析失败: {str(e)}")


# 全局单例 Agent 实例
_agent_instance: Optional[RepairAnalysisAgent] = None


def get_agent() -> RepairAnalysisAgent:
    """获取全局 Agent 实例（单例模式）"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RepairAnalysisAgent()
    return _agent_instance
