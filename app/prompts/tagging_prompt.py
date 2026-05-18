from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage

TAGGING_SYSTEM = (
    "你是设施巡检专家。提取图片中的核心物件名称、场景位置和状态特征。如果图片中存在多个主体，一并提取。"
    "只输出 JSON 数组，3-5 个关键词，不要任何其他文字。"
    '示例：["地下车库", "倒车杆", "弯曲变形"]'
)

tagging_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=TAGGING_SYSTEM),
    ("human", [
        {
            "type": "image_url",
            "image_url": {"url": "{image_url}"},
        },
        {
            "type": "text",
            "text": "请提取关键词，只输出 JSON 数组。",
        },
    ]),
])
