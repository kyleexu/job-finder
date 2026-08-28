"""Job Finder 主题示例工具"""

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from ..base import Tool
from .jsearch import build_jsearch_tools

JOB_ROLES = {
    "backend": "Backend: 服务端开发，常见栈 Python/Java/Go。看重系统设计、API、数据库与可靠性。",
    "frontend": "Frontend: 客户端与 Web UI，常见栈 React/TypeScript。看重交互、性能与工程化。",
    "fullstack": "Fullstack: 能独立交付前后端。适合中小团队，面试常覆盖两端基础。",
    "data": "Data: 数据分析/数据工程。看重 SQL、指标口径、pipeline 与业务理解。",
    "pm": "Product Manager: 产品经理。看重问题定义、优先级、沟通与交付结果。",
    "intern": "Intern: 实习岗。简历突出项目与可验证产出，面试以基础和学习能力为主。",
}

JOB_SEARCH_TIPS = {
    "resume": "简历：一页优先；用数字写结果（上线、性能、转化）；JD 关键词对齐，避免空泛形容词。",
    "interview": "面试：STAR 讲项目；先澄清需求再动手；不会的题说思路，不要沉默。",
    "networking": "内推：熟人 > 校友 > 招聘会。消息要短：你是谁、想做什么、为什么匹配、附件简历。",
    "offer": "Offer：对比职责、团队、成长、总包与期权归属。口头 offer 以书面为准。",
    "remote": "远程岗：时区重叠、沟通异步、文档习惯是加分项。申请时写清可工作时段。",
}


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = "Get the current UTC time."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def run(self, arguments: dict[str, Any]) -> str:
        del arguments
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class GetRoleInfoTool(Tool):
    name = "get_role_info"
    description = "Get brief info about a job role direction."
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Role key",
                "enum": ["backend", "frontend", "fullstack", "data", "pm", "intern"],
            }
        },
        "required": ["name"],
    }

    def run(self, arguments: dict[str, Any]) -> str:
        key = str(arguments.get("name") or "").lower()
        logger.info("get_role_info name={}", key)
        if not key:
            return "Please provide name"
        return JOB_ROLES.get(
            key,
            f"No preset info for '{key}'. Try: {', '.join(JOB_ROLES)}",
        )


class GetJobSearchTipTool(Tool):
    name = "get_job_search_tip"
    description = "Get job search tips for a topic."
    parameters = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "Tip topic",
                "enum": ["resume", "interview", "networking", "offer", "remote"],
            }
        },
        "required": ["topic"],
    }

    def run(self, arguments: dict[str, Any]) -> str:
        key = str(arguments.get("topic") or "").lower()
        logger.info("get_job_search_tip topic={}", key)
        if not key:
            return "Please provide topic"
        return JOB_SEARCH_TIPS.get(
            key,
            f"No preset tip for '{key}'. Try: {', '.join(JOB_SEARCH_TIPS)}",
        )


def build_default_tools() -> list[Tool]:
    return [
        GetCurrentTimeTool(),
        GetRoleInfoTool(),
        GetJobSearchTipTool(),
        *build_jsearch_tools(),
    ]
