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

服务默认运行在 `http://127.0.0.1:8001`。

## 试一次对话

```bash
curl -X POST http://127.0.0.1:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"我想转 backend，简历该怎么改？"}'
```

也可以打开 Swagger：`http://127.0.0.1:8001/docs`

## 内置工具

| 工具 | 作用 |
|------|------|
| `get_current_time` | 返回当前 UTC 时间 |
| `get_role_info` | 岗位方向简介 |
| `get_job_search_tip` | 求职流程小贴士 |

Agent 通过 `[TOOL_CALL:tool_name:params]` 格式调用工具（与 trip-planner 项目同一思路）。

## 下一步你可以改什么

1. 在 `app/tools/builtin/job_tools.py` 加新工具
2. 在 `app/agents/job_finder_agent.py` 改 system prompt
3. 接 MCP server（参考 helloagents-trip-planner 的 MCPTool）
4. 加 RAG：把岗位 JD / 面试题库向量化后检索

## 和 Java 的对应关系

| Python | Java 类比 |
|--------|-----------|
| `Tool` / `ToolRegistry` | Service 接口 + Bean 注册 |
| `SimpleAgent` | 编排层 Service |
| `LLMClient` | 外部 API Client |
| FastAPI route | `@RestController` |
