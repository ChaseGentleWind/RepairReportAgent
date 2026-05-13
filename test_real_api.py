"""测试实际运行的 API"""
import requests
from pathlib import Path

# 测试图片
image_path = Path("data/image_002.png")

with open(image_path, "rb") as f:
    files = {"file": ("test.png", f, "image/png")}
    response = requests.post("http://localhost:8000/api/v1/analyze-repair", files=files)

print(f"HTTP Status: {response.status_code}")
print(f"Response: {response.json()}")
