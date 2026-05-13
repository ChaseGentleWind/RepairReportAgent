# Repair Report Agent

多模态 AI 报修助手 — 上传图片，自动生成一句话报修描述。

基于通义千问 Qwen3.5-Omni-Flash，通过 LangChain LCEL 管道完成图片理解与结构化输出。

## 特性

- 📸 上传图片即可获得自然语言报修描述（如"空调出风口盖板脱落，请安排维修"）
- 🚫 自动识别并驳回无效图片（模糊、过暗、内容无关）
- ⚡ 异步架构，1–3 秒响应
- 🖥️ 内置 Web 前端，开箱即用

## 项目结构

```
RepairReportAgent/
├── main.py                        # FastAPI 入口
├── .env.example                   # 环境变量模板
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── app/
│   ├── api/endpoints.py           # POST /api/v1/analyze-repair
│   ├── agents/repair_agent.py     # LangChain LCEL Chain
│   ├── models/schemas_v2.py       # Pydantic 数据模型
│   ├── prompts/
│   │   ├── templates.py           # ChatPromptTemplate
│   │   ├── few_shot_examples.py   # 少样本示例
│   │   └── fault_dictionary.py    # 故障词典
│   ├── services/image_utils.py    # 图片压缩 / Base64 编码
│   └── core/config.py             # 配置管理
├── frontend/                      # 测试用前端（静态页面）
├── data/                          # 测试数据（Excel 源文件 + JSON）
└── scripts/
    ├── check_config.py
    └── test_client.py
```

## 快速开始

### 方式一：Docker（推荐）

无需安装 Python 环境，只需有 Docker。

```bash
# 1. 克隆项目
git clone <repo-url>
cd RepairReportAgent

# 2. 配置 API Key
export DASHSCOPE_API_KEY=your_api_key_here

# 3. 构建并启动
docker compose up -d --build
```

服务启动后访问：
- API：`http://localhost:8000/api/v1/analyze-repair`
- 健康检查：`http://localhost:8000/health`
- Swagger 文档：`http://localhost:8000/docs`

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 3. 启动后端
python main.py

# 4. 启动前端（可选，仅测试用）
cd frontend && python -m http.server 5500
# 访问 http://localhost:5500
```

获取 API Key：[阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)

## API

**POST `/api/v1/analyze-repair`** — 上传图片，返回报修描述

```bash
curl -X POST http://localhost:8000/api/v1/analyze-repair \
  -F "file=@repair_image.jpg"
```

成功响应：
```json
{
  "success": true,
  "reply": "空调出风口盖板脱落，请安排维修。",
  "metadata": {
    "processing_time": 2.35,
    "image_size": "800x600"
  }
}
```

图片无效时返回 HTTP 400：
```json
{
  "success": false,
  "message": "图片内容无效，请重新拍摄清晰的设备细节。"
}
```

其他接口：
- `GET /health` — 健康检查
- `GET /docs` — Swagger UI

## 技术栈

- **FastAPI** + **Uvicorn** — 异步 Web 框架
- **LangChain LCEL** — `prompt | llm | parser` 管道
- **通义千问 Qwen3.5-Omni-Flash** — 多模态大模型
- **Pydantic** — 数据验证与结构化输出
- **Pillow** — 图片压缩与格式转换

## 注意事项

- `.env` 文件不要提交到版本控制，使用 `.env.example` 作为模板
- 每次调用产生 API 费用，建议设置预算告警
- 图片长边自动压缩至 1024px，建议前端预压缩以加快传输
