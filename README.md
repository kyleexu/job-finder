# Job Finder

个人 AI Agent 学习项目：Python + FastAPI + LLM + Tool Calling。帮助用户找工作、改简历和准备面试。

## 项目结构

```text
job-finder/
├── app/                 # 应用层（API、Agent、Tools）
│   ├── agents/          # 业务 Agent
│   ├── routes/          # HTTP 路由
│   ├── tools/           # 工具定义与注册
│   └── models/          # Pydantic 请求/响应模型
├── core/                # Agent 核心（LLM、SimpleAgent）
├── run.py               # 启动入口
└── requirements.txt
```

## 快速开始

```bash
cd /Users/kylexu/workspace/job-finder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY
python run.py
```

服务默认运行在 `http://127.0.0.1:8001`。请求日志写在项目根目录的 **`run.log`**。

```bash
./start.sh
```

## 试一次对话

```bash
curl -X POST http://127.0.0.1:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我想转 backend，简历该怎么改？"}'
```

也可以打开页面：`http://127.0.0.1:8001/`，或 Swagger：`http://127.0.0.1:8001/docs`

## 内置工具

| 工具 | 作用 |
|------|------|
| `get_current_time` | 返回当前 UTC 时间 |
| `get_role_info` | 岗位方向简介 |
| `get_job_search_tip` | 求职流程小贴士 |
| `search_jobs` | 通过 JSearch 搜索在招岗位 |
| `get_job_details` | 按 job_id 拉岗位详情 |

Agent 通过 DeepSeek [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)（OpenAI 兼容 `tools` / `tool_calls`）调用工具。

## 接入 JSearch

搜岗是普通 HTTP 调用 [OpenWeb Ninja JSearch](https://www.openwebninja.com/api/jsearch)，不是 MCP：

```bash
curl -X GET 'https://api.openwebninja.com/jsearch/search-v2?query=developer%20jobs%20in%20chicago' \
  -H 'X-API-Key: your-key'
```

把 Key 写入 `.env` 的 `JSEARCH_API_KEY`。`search_jobs` 默认 1 页；未配置 Key 时工具会提示，应用仍可启动。

## 下一步你可以改什么

1. 在 `app/tools/builtin/job_tools.py` 加新工具
2. 在 `app/agents/job_finder_agent.py` 改 system prompt
3. 加 RAG：把岗位 JD / 面试题库向量化后检索

## 和 Java 的对应关系

| Python | Java 类比 |
|--------|-----------|
| `Tool` / `ToolRegistry` | Service 接口 + Bean 注册 |
| `SimpleAgent` | 编排层 Service |
| `LLMClient` | 外部 API Client |
| FastAPI route | `@RestController` |
