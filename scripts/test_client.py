"""
API 测试客户端 - 用于快速测试 API 接口

使用方法:
1. 启动服务: python main.py
2. 运行测试: python scripts/test_client.py <image_path>

示例:
python scripts/test_client.py test_images/broken_ac.jpg
"""

import sys
import requests
from pathlib import Path
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试健康检查接口")
    print("=" * 60)

    try:
        response = requests.get("http://localhost:8000/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"[X] 健康检查失败: {e}")
        return False


def test_analyze_repair(image_path: str):
    """测试报修图片分析接口"""
    print("\n" + "=" * 60)
    print("测试报修图片分析接口")
    print("=" * 60)

    # 检查文件是否存在
    if not Path(image_path).exists():
        print(f"[X] 文件不存在: {image_path}")
        return False

    print(f"图片路径: {image_path}")

    try:
        # 发送请求
        with open(image_path, "rb") as f:
            files = {"file": f}
            print("\n发送请求...")
            response = requests.post(
                "http://localhost:8000/api/v1/analyze-repair",
                files=files
            )

        print(f"状态码: {response.status_code}")

        # 解析响应
        result = response.json()

        print("\n" + "=" * 60)
        print("分析结果")
        print("=" * 60)

        if result.get("success"):
            data = result.get("data", {})
            metadata = result.get("metadata", {})

            # 显示结果
            if data.get("is_valid_image"):
                print(f"\n[OK] 图片有效")
                print(f"\n识别物件: {data.get('object_name')}")
                print(f"故障描述: {data.get('issue_description')}")
                print(f"推理原因: {data.get('reasoning')}")
                print(f"问题分类: {data.get('category')}")
                print(f"置信度: {data.get('confidence')}")

                # 置信度提示
                if data.get('confidence') == 'Low':
                    print("\n[!] 置信度较低，建议人工确认")
                elif data.get('confidence') == 'High':
                    print("\n[OK] 高置信度，可直接处理")
            else:
                print(f"\n[X] 图片无效")
                print(f"驳回原因: {data.get('rejection_reason')}")

            # 显示元数据
            print(f"\n处理时间: {metadata.get('processing_time')} 秒")
            print(f"使用模型: {metadata.get('model')}")
            print(f"图片尺寸: {metadata.get('image_size')}")

            return True
        else:
            error = result.get("error", {})
            print(f"\n[X] 请求失败")
            print(f"错误码: {error.get('code')}")
            print(f"错误信息: {error.get('message')}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n[X] 连接失败: 服务未启动")
        print("请先启动服务: python main.py")
        return False
    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Repair Report Agent API 测试客户端")
    print("=" * 60)

    # 1. 测试健康检查
    if not test_health():
        print("\n[X] 服务未启动或不可用")
        print("请先启动服务: python main.py")
        sys.exit(1)

    # 2. 测试图片分析
    if len(sys.argv) < 2:
        print("\n[!] 未提供图片路径")
        print("\n使用方法:")
        print("  python scripts/test_client.py <image_path>")
        print("\n示例:")
        print("  python scripts/test_client.py test_images/broken_ac.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    success = test_analyze_repair(image_path)

    print("\n" + "=" * 60)
    if success:
        print("[OK] 测试完成")
    else:
        print("[X] 测试失败")
    print("=" * 60 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
