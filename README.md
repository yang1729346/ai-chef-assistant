# 🍳 AI 私厨助手 (AI Chef Assistant)

基于 FastAPI + LangChain + 通义千问大模型的 AI 私厨助手，支持食材图片识别、智能食谱搜索推荐、多会话记忆管理等功能。

## 功能特性

- **🥗 食材识别** — 上传食材照片，AI 自动识别食材种类并评估新鲜度
- **📖 智能食谱推荐** — 基于可用食材，通过搜索引擎检索菜谱，从营养和难度多维度评分排序
- **💬 流式对话** — 基于 SSE 的流式响应，实时展示 AI 思考过程
- **📸 图片上传** — 对接阿里云 OSS，生成预签名上传 URL，支持图片一键上传
- **🧠 多记忆管理** — 支持创建多个独立对话上下文，为不同会话保留专属记忆
- **🗂️ 会话历史** — 自动保存对话记录，随时回溯历史消息

## 技术栈

| 模块 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| AI 框架 | LangChain + LangGraph |
| 大模型 | 通义千问 Qwen (DashScope API) |
| 搜索工具 | Tavily Search API |
| 对象存储 | 阿里云 OSS |
| 数据存储 | SQLite |
| 前端 | Next.js (静态构建) |

## 快速开始

### 前置条件

- Python 3.10+
- 阿里云 OSS 服务（用于图片上传）
- DashScope API Key（通义千问）
- Tavily Search API Key（网络搜索）

### 安装

```bash
# 克隆项目
git clone https://github.com/yang1729346/ai-chef-assistant.git
cd ai-chef-assistant

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
# 阿里云 OSS 配置（图片上传）
OSS_ACCESS_KEY_ID=your_oss_access_key
OSS_ACCESS_KEY_SECRET=your_oss_secret
OSS_BUCKET=your_bucket_name
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com

# 通义千问 API
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Tavily 搜索 API
TAVILY_API_KEY=your_tavily_api_key
```

### 启动

```bash
python -m app.main
```

服务默认运行在 `http://localhost:8001`。

## API 接口

### 1. 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/stream` | 流式对话（SSE） |
| GET | `/api/v1/chat/messages` | 获取历史消息 |
| DELETE | `/api/v1/chat/messages` | 清空会话历史 |
| GET | `/api/v1/chat/memory-contexts` | 获取所有记忆上下文 |
| GET | `/api/v1/chat/memory-contents` | 获取特定记忆内容 |

**流式对话请求示例：**

```json
{
  "message": "我今天买了西红柿和鸡蛋，能做什么菜？",
  "image_url": "https://your-bucket.oss-cn-beijing.aliyuncs.com/ingredients.jpg",
  "thread_id": "session_001"
}
```

### 2. 图片上传

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/oss/presign?filename=xxx.jpg` | 获取 OSS 上传签名 URL |

### 3. 记忆管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/memory/contexts` | 列出所有记忆上下文 |
| POST | `/api/v1/memory/contexts` | 创建记忆上下文 |
| GET | `/api/v1/memory/contexts/{id}` | 获取指定上下文 |
| DELETE | `/api/v1/memory/contexts/{id}` | 删除上下文 |
| PUT | `/api/v1/memory/contexts/{id}/description` | 更新描述 |
| GET | `/api/v1/memory/contents/{context_id}` | 获取记忆内容 |

## 项目结构

```
app/
├── main.py                 # 应用入口，路由挂载
├── agents/
│   └── person_chef.py      # AI 私厨智能体（LangChain Agent）
├── api/
│   └── v1/
│       ├── chat.py         # 对话接口（流式/历史）
│       ├── memory.py       # 记忆管理接口
│       └── oss.py          # 阿里云 OSS 上传接口
├── common/
│   ├── logger.py           # 日志配置
│   └── memory_manager.py   # 多记忆管理器
├── models/
│   └── schemas.py          # Pydantic 数据模型
└── static/                 # 前端静态文件（Next.js 构建产物）
```

## AI 工作流程

1. **食材识别** — 接收用户上传的食材图片或文字清单
2. **食材评估** — 评估食材新鲜度和可用量，整理可用食材清单
3. **智能检索** — 调用 Tavily 搜索基于食材的可行菜谱
4. **评分排序** — 从营养价值和制作难度两个维度量化打分
5. **结果输出** — 输出结构化的食谱建议（含评分、推荐理由、参考图片）
