# Repair Report Agent

上传一张报修图片，自动返回一句话报修描述。

基于通义千问 Qwen3.5-Omni-Flash，通过 LangChain LCEL 管道完成图片理解与结构化输出。

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
└── test_batch_compare.py          # 批量对比测试脚本
```

## 快速开始

### 方式一：Docker（推荐）

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

# 4. 启动前端（可选）
cd frontend && python serve.py
# 访问 http://localhost:8080
```

获取 API Key：[阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)

## API

### POST `/api/v1/analyze-repair`

上传报修图片，返回一句话报修描述。

**请求**

| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | `multipart/form-data` | 图片文件，支持 JPEG、PNG、WebP、GIF、BMP、TIFF |

图片会自动压缩至长边 1024px，无需前端预处理。

```bash
curl -X POST http://localhost:8000/api/v1/analyze-repair \
  -F "file=@repair_image.jpg"
```

**成功响应（HTTP 200）**

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

**图片无效响应（HTTP 400）**

图片模糊、过暗、内容与设施无关时返回：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_IMAGE_FORMAT",
    "message": "不支持的文件格式: text/plain"
  }
}
```

**服务器错误（HTTP 500）**

```json
{
  "success": false,
  "error": {
    "code": "LLM_ANALYSIS_FAILED",
    "message": "图片分析失败: API timeout"
  }
}
```

### GET `/health`

健康检查，返回服务状态和当前模型配置。

### GET `/docs`

Swagger UI，可在线调试所有接口。

## 技术栈

- **FastAPI** + **Uvicorn** — 异步 Web 框架
- **LangChain LCEL** — `prompt | llm | parser` 管道
- **通义千问 Qwen3.5-Omni-Flash** — 多模态大模型
- **Pydantic** — 结构化输出解析
- **Pillow** — 图片压缩与格式转换

## 注意事项

- `.env` 文件不要提交到版本控制，使用 `.env.example` 作为模板
- 每次调用产生 API 费用，建议在阿里云控制台设置预算告警
