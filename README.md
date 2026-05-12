# Repair Report Agent Backend

多模态 AI Agent 后端服务 - 报修图片智能识别与意图分析

基于通义千问 Qwen3.5-Omni-Flash 多模态大模型，自动识别报修图片中的物件、故障描述和问题分类。

## 特性

- 🤖 **AI 视觉推理**: 基于通义千问多模态大模型
- 📸 **智能图片处理**: 自动压缩、格式转换、质量检测
- 🎯 **精准识别**: 物件识别、故障分析、问题分类
- 📊 **置信度评估**: High/Medium/Low 三级置信度
- 🚫 **智能驳回**: 自动识别无效图片（过暗、模糊、无关内容）
- ⚡ **高性能**: 异步架构，1-3 秒响应
- 📝 **结构化输出**: 严格的 JSON Schema 验证
- 🔒 **完善的错误处理**: 统一的错误响应格式
- 🖥️ **Web 前端界面**: 简洁美观的图片上传和分析界面

## 项目结构

```
RepairReportAgent/
├── main.py                    # FastAPI 入口
├── requirements.txt           # 依赖清单
├── .env                       # 环境变量配置
├── app/
│   ├── api/
│   │   └── endpoints.py       # API 路由
│   ├── core/
│   │   ├── config.py          # 配置管理
│   │   └── prompts.py         # System Prompt
│   ├── models/
│   │   └── schemas.py         # Pydantic 数据模型
│   └── services/
│       ├── image_utils.py     # 图像处理
│       └── llm_agent.py       # LLM Agent
├── frontend/                  # Web 前端界面
│   ├── index.html             # 主页面
│   ├── style.css              # 样式文件
│   ├── script.js              # 脚本文件
│   └── README.md              # 前端使用说明
├── tests/                     # 测试
│   ├── test_image_utils.py
│   ├── test_llm_agent.py
│   └── test_api.py
├── scripts/                   # 工具脚本
│   ├── check_config.py        # 配置检查
│   └── test_client.py         # 测试客户端
└── docs/                      # 文档
    ├── api_guide.md           # API 使用指南
    ├── llm_agent_guide.md     # LLM Agent 指南
    ├── image_utils_guide.md   # 图像处理指南
    ├── phase3_summary.md      # Phase 3 总结
    └── phase4_summary.md      # Phase 4 总结
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，填入你的通义千问 API Key：

```env
# DashScope API Configuration (通义千问)
DASHSCOPE_API_KEY=your_dashscope_api_key_here
API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Model Configuration
MODEL_NAME=qwen3.5-omni-flash
MAX_IMAGE_SIZE=1024
```

**获取 API Key**: 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)

### 3. 检查配置

```bash
python scripts/check_config.py
```

### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问服务

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health
- **Web 前端**: 见下方"前端界面使用"

## 前端界面使用

### 启动前端

**方法一：Python HTTP 服务器（推荐）**

```bash
# 在项目根目录，打开新终端
cd frontend
python -m http.server 5500
```

然后访问: http://localhost:5500

**方法二：VS Code Live Server**

1. 安装 "Live Server" 插件
2. 右键点击 `frontend/index.html`
3. 选择 "Open with Live Server"

### 使用步骤

1. **上传图片**: 点击或拖拽图片到上传区域
2. **预览图片**: 查看上传的图片
3. **开始分析**: 点击"开始分析"按钮
4. **查看结果**: 查看 AI 分析的结果

详细说明请查看: [前端使用指南](frontend/README.md)

## API 使用

### 核心接口

**POST /api/v1/analyze-repair**

上传报修图片，AI 自动识别物件、故障描述和问题分类。

**请求示例（cURL）：**
```bash
curl -X POST http://localhost:8000/api/v1/analyze-repair \
  -F "file=@repair_image.jpg"
```

**请求示例（Python）：**
```python
import requests

url = "http://localhost:8000/api/v1/analyze-repair"
files = {"file": open("repair_image.jpg", "rb")}

response = requests.post(url, files=files)
result = response.json()

if result["success"] and result["data"]["is_valid_image"]:
    print(f"物件: {result['data']['object_name']}")
    print(f"问题: {result['data']['issue_description']}")
    print(f"置信度: {result['data']['confidence']}")
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "is_valid_image": true,
    "object_name": "空调出风口",
    "issue_description": "出风口盖板脱落",
    "reasoning": "图中可见白色塑料盖板与主体分离，且有固定卡扣断裂痕迹",
    "category": "硬件损坏/老化",
    "confidence": "High"
  },
  "metadata": {
    "processing_time": 2.35,
    "model": "qwen3.5-omni-flash",
    "image_size": "800x600"
  }
}
```

### 测试客户端

```bash
python scripts/test_client.py test_image.jpg
```

## 技术栈

- **FastAPI**: 高性能异步 Web 框架
- **Pydantic**: 数据验证与序列化
- **OpenAI SDK**: 兼容通义千问 API
- **通义千问 Qwen3.5-Omni-Flash**: 多模态大模型
- **Pillow**: 图像处理
- **Pytest**: 单元测试

## 核心功能

### 1. 图像处理
- ✅ 支持多种格式（JPEG, PNG, WebP, GIF, BMP, TIFF）
- ✅ 自动压缩（长边最大 1024px）
- ✅ 格式转换（统一转为 JPEG）
- ✅ Base64 编码

### 2. AI 视觉推理
- ✅ 物件识别
- ✅ 故障分析
- ✅ 问题分类（5 大类）
- ✅ 置信度评估（High/Medium/Low）
- ✅ 推理原因说明

### 3. 智能驳回
- ✅ 图片质量检测
- ✅ 自动驳回无效图片
- ✅ 提供驳回原因

### 4. 问题分类
- 硬件损坏/老化
- 安装/加固需求
- 异常状态/环境问题
- 调试/设置需求
- 未知/需人工确认

## 测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
# 图像处理测试
pytest tests/test_image_utils.py -v

# LLM Agent 测试
pytest tests/test_llm_agent.py -v

# API 测试
pytest tests/test_api.py -v
```

### 测试覆盖

- ✅ 图像处理: 8/8 测试通过
- ✅ LLM Agent: 9/9 测试通过
- ✅ API 接口: 11/11 测试通过

## 文档

- [API 使用指南](docs/api_guide.md) - 完整的 API 文档和示例
- [LLM Agent 指南](docs/llm_agent_guide.md) - Agent 使用说明
- [图像处理指南](docs/image_utils_guide.md) - 图像处理模块说明
- [配置说明](CONFIG.md) - 环境配置和模型选择
- [Phase 3 总结](docs/phase3_summary.md) - LLM Agent 实现总结
- [Phase 4 总结](docs/phase4_summary.md) - API 路由实现总结

## 开发进度

### Phase 1: 基础设施搭建 ✅
- [x] 项目目录结构
- [x] 依赖配置
- [x] 环境变量配置
- [x] 数据模型定义
- [x] FastAPI 基础框架
- [x] CORS 配置

### Phase 2: 图像处理模块 ✅
- [x] 图片上传和验证
- [x] 图片压缩和编码
- [x] Base64 Data URI 生成
- [x] 单元测试

### Phase 3: 核心 Agent 逻辑 ✅
- [x] LLM Agent 实现
- [x] 通义千问 API 集成
- [x] 结构化输出
- [x] 重试机制
- [x] 单元测试

### Phase 4: API 路由与联调 ✅
- [x] API 接口实现
- [x] 错误处理
- [x] API 文档
- [x] 测试客户端
- [x] 集成测试

## 性能指标

- **响应时间**: 1-3 秒
- **图片处理**: < 0.5 秒
- **LLM 分析**: 1-2.5 秒
- **并发支持**: 异步架构，支持高并发
- **准确率**: 依赖模型能力，建议对 Low 置信度结果人工确认

## 注意事项

1. **API Key 安全**: 不要将 `.env` 文件提交到版本控制系统
2. **成本控制**: 每次调用会产生 API 费用，建议设置预算告警
3. **置信度处理**: 对 Low 置信度结果进行人工确认
4. **图片大小**: 建议前端压缩图片，减少传输时间
5. **并发限制**: 注意 API 限流，避免过高并发

## 故障排查

### 服务无法启动

1. 检查依赖是否安装完整
2. 检查 `.env` 配置是否正确
3. 运行配置检查: `python scripts/check_config.py`

### API 调用失败

1. 检查 DASHSCOPE_API_KEY 是否有效
2. 检查网络连接
3. 查看服务日志

### 图片分析失败

1. 检查图片格式是否支持
2. 检查图片是否损坏
3. 检查 API 配额是否充足

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
