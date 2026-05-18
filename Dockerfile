FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.11-slim

WORKDIR /app

# 先复制依赖文件，利用层缓存（依赖不变时不重新安装）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 只复制后端代码
COPY main.py .
COPY app/ ./app/

# 确保 ChromaDB 持久化目录存在
RUN mkdir -p /app/data/chroma_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
