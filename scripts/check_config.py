"""
配置验证脚本 - 检查环境配置是否正确

运行: python scripts/check_config.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def check_config():
    """检查配置是否正确"""
    print("=" * 60)
    print("配置检查")
    print("=" * 60)

    errors = []
    warnings = []

    # 检查 API Key
    print("\n[1/5] 检查 DASHSCOPE_API_KEY...")
    if not settings.DASHSCOPE_API_KEY or settings.DASHSCOPE_API_KEY == "your_dashscope_api_key_here":
        errors.append("DASHSCOPE_API_KEY 未配置或使用默认值")
        print("   [X] 未配置")
    else:
        print(f"   [OK] 已配置 (长度: {len(settings.DASHSCOPE_API_KEY)})")

    # 检查 API Base URL
    print("\n[2/5] 检查 API_BASE_URL...")
    if settings.API_BASE_URL:
        print(f"   [OK] {settings.API_BASE_URL}")
    else:
        errors.append("API_BASE_URL 未配置")
        print("   [X] 未配置")

    # 检查模型名称
    print("\n[3/5] 检查 MODEL_NAME...")
    if settings.MODEL_NAME:
        print(f"   [OK] {settings.MODEL_NAME}")
        if settings.MODEL_NAME not in ["qwen3.5-omni-flash", "qwen-vl-max", "qwen-vl-plus"]:
            warnings.append(f"模型名称 '{settings.MODEL_NAME}' 可能不正确")
    else:
        errors.append("MODEL_NAME 未配置")
        print("   [X] 未配置")

    # 检查服务器配置
    print("\n[4/5] 检查服务器配置...")
    print(f"   HOST: {settings.HOST}")
    print(f"   PORT: {settings.PORT}")
    print(f"   DEBUG: {settings.DEBUG}")

    # 检查 CORS 配置
    print("\n[5/5] 检查 CORS 配置...")
    print(f"   ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")

    # 显示结果
    print("\n" + "=" * 60)
    print("检查结果")
    print("=" * 60)

    if errors:
        print("\n[X] 发现错误:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("\n[!] 警告:")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print("\n[OK] 所有配置正确")
        print("\n下一步:")
        print("1. 运行服务: python main.py")
        print("2. 访问文档: http://localhost:8000/docs")
        print("3. 运行测试: pytest tests/ -v")
    elif not errors:
        print("\n[OK] 配置基本正确，但有警告")
        print("   可以继续运行，但建议检查警告项")
    else:
        print("\n[X] 配置有误，请修复错误后再运行")
        print("\n修复方法:")
        print("1. 编辑 .env 文件")
        print("2. 填入正确的 DASHSCOPE_API_KEY")
        print("3. 重新运行此脚本验证")

    print("=" * 60)

    return len(errors) == 0


if __name__ == "__main__":
    try:
        success = check_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[X] 配置检查失败: {str(e)}")
        print("\n可能的原因:")
        print("1. .env 文件不存在")
        print("2. .env 文件格式错误")
        print("3. 缺少必要的依赖")
        sys.exit(1)
