"""求职助手 Agent"""

from functools import lru_cache

from core.llm import LLMClient
from core.simple_agent import SimpleAgent

from ..config import get_settings
from ..tools.builtin import build_default_tools
from ..tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是 Job Finder，一个帮助用户找工作、改简历和准备面试的 AI 助手。

你可以回答：
- 岗位方向选择（backend、frontend、data、PM 等）
- 求职流程（简历、面试、内推、Offer、远程岗）
- 针对 JD 的匹配建议与准备清单

规则：
1. 优先使用工具获取结构化信息，再组织自然语言回答。
2. 不确定的内容要明确说明，不要编造具体薪资、公司内推名额或招聘政策。
3. 默认用中文回答；用户用英文提问时可切换英文。
"""


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in build_default_tools():
        registry.register(tool)
    return registry


@lru_cache
def get_job_finder_agent() -> SimpleAgent:
    settings = get_settings()
    llm = LLMClient(
        model=settings.llm_model_id,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    return SimpleAgent(
        name="job-finder",
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tool_registry=create_tool_registry(),
    )
