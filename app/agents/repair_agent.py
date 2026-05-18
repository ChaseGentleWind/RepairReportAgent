import json
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from app.models.schemas_v2 import RepairReplyResponse
from app.prompts.templates import get_repair_prompt
from app.prompts.tagging_prompt import tagging_prompt
from app.rag.retriever import SopRetriever
from app.rag.routing import get_dispatch_info
from app.core.config import settings

logger = logging.getLogger(__name__)


def _parse_keywords(raw: str) -> list[str]:
    """Parse JSON array from tagging LLM output, tolerating markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return [str(k) for k in result]
    except json.JSONDecodeError:
        pass
    return []


def _format_sop_context(chunks: list[str]) -> str:
    return "\n".join(f"- {c}" for c in chunks)


class RepairAnalysisAgent:
    def __init__(self):
        # 打标模型（轻量视觉模型，只提关键词）
        self.tagging_llm = ChatOpenAI(
            model=settings.TAGGING_MODEL_NAME,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.API_BASE_URL,
            temperature=0,
            max_tokens=100,
        )
        self.tagging_chain = tagging_prompt | self.tagging_llm

        # 推理模型（主模型）
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.API_BASE_URL,
            temperature=0.1,
            max_tokens=1000,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        self.parser = PydanticOutputParser(pydantic_object=RepairReplyResponse)

        # SOP 检索器
        self.retriever = SopRetriever()

        logger.info(f"RepairAnalysisAgent 初始化完成，模型: {settings.MODEL_NAME}")

    async def analyze(self, base64_image: str) -> dict:
        try:
            # 阶段一：打标，提取关键词
            tag_result = await self.tagging_chain.ainvoke({"image_url": base64_image})
            keywords = _parse_keywords(tag_result.content)
            logger.info(f"打标关键词: {keywords}")

            # 阶段二：RAG 检索
            sop_context = ""
            rag_used = False
            category = "未知/需人工确认"

            if keywords:
                query = " ".join(keywords)
                sop_chunks, is_confident = self.retriever.search(query)
                if is_confident:
                    sop_context = _format_sop_context(sop_chunks)
                    rag_used = True
                    logger.info(f"RAG 命中，注入 {len(sop_chunks)} 条 SOP 片段")
                else:
                    logger.info("RAG 置信度不足，降级为纯视觉推理")

            # 阶段三：推理（动态构建 prompt，注入 sop_context）
            print(f"\n{'='*60}")
            print(f"[DEBUG] RAG 是否命中: {rag_used}")
            print(f"[DEBUG] 注入的 SOP 内容:\n{sop_context if sop_context else '（无，纯视觉推理）'}")
            print(f"{'='*60}\n")
            prompt = get_repair_prompt(self.parser.get_format_instructions(), sop_context)
            chain = prompt | self.llm | self.parser
            result = await chain.ainvoke({"image_url": base64_image})

            logger.info(f"分析完成: reply={result.reply[:30]}...")

            # 附加路由信息（category 来自 RepairReplyResponse，若无则用默认）
            category = getattr(result, "category", "未知/需人工确认") or "未知/需人工确认"
            dispatch_info = get_dispatch_info(category)

            return {
                **result.model_dump(),
                "dispatch_info": dispatch_info,
                "rag_used": rag_used,
            }

        except Exception as e:
            logger.error(f"LangChain Chain 调用失败: {str(e)}")
            raise Exception(f"图片分析失败: {str(e)}")


_agent_instance: Optional[RepairAnalysisAgent] = None


def get_agent() -> RepairAnalysisAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = RepairAnalysisAgent()
    return _agent_instance
