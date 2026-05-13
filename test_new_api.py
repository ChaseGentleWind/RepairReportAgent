"""测试新的多选项 API"""
import asyncio
import base64
from pathlib import Path
from app.agents.repair_agent import get_agent


async def test_agent():
    """测试 Agent 直接调用"""
    # 读取测试图片
    image_path = Path("data/image_001.png")
    if not image_path.exists():
        print(f"测试图片不存在: {image_path}")
        return

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
        base64_image = f"data:image/png;base64,{image_data}"

    print("=== 测试 Agent 分析 ===\n")
    agent = get_agent()
    result = await agent.analyze(base64_image)

    print("Agent 返回结果:")
    print(f"  internal_reasoning: {result.get('internal_reasoning', 'N/A')[:100]}...")
    print(f"  选项数量: {len(result.get('suggested_options', []))}")

    for i, option in enumerate(result.get('suggested_options', []), 1):
        print(f"\n  选项 {i}:")
        print(f"    category: {option.get('category')}")
        print(f"    frontend_display_text: {option.get('frontend_display_text')}")


if __name__ == "__main__":
    asyncio.run(test_agent())
