"""求职助手 Agent"""

from functools import lru_cache

from loguru import logger

from core.llm import LLMClient
from core.simple_agent import SimpleAgent

from ..config import get_settings
from ..logging_setup import mask_secret
from ..tools.builtin import build_default_tools
from ..tools.registry import ToolRegistry

SYSTEM_PROMPT = """你是 Job Finder，一个帮助用户找工作、改简历和准备面试的 AI 助手。

你可以回答：
- 岗位方向选择（backend、frontend、data、PM 等）
- 求职流程（简历、面试、内推、Offer、远程岗）
- 针对 JD 的匹配建议与准备清单
- 用 search_jobs 搜索真实在招岗位（JSearch / Google for Jobs 聚合）

规则：
1. 需要实时岗位或结构化信息时调用工具，再组织自然语言回答。
2. 不确定的内容要明确说明，不要编造具体薪资、公司内推名额或招聘政策。
3. 默认用中文回答；用户用英文提问时可切换英文。
4. 搜岗时 query 写清职位和地点，country 用 ISO 国家码。用户明确要某条详情再用 get_job_details。num_pages 默认 1。
5. 用 Markdown，写成像对话助手那样可扫读的结构：
   - 开头用一句加粗，点出当前最关键的结论或问题。
   - 关键数字、区间、条件用引用块（>）单独列出。
   - 来源和投递入口写成 Markdown 链接，例如 [投递](完整URL) 或 [联邦就业局](完整URL)。
   - 结尾用加粗 + ↳ 给出下一步可以继续帮用户做的事（可并列几条 ↳）。
6. 列出岗位时必须带上工具返回的投递链接，优先 apply_link，没有则用 google_link。不要省略、截断或改写 URL；没有链接时写「无投递链接」。
"""


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in build_default_tools():
        registry.register(tool)
        logger.debug("注册工具 name={} description={}", tool.name, tool.description)
    logger.info("工具注册完成 tools={}", registry.names())
    return registry


def shutdown_job_finder_agent() -> None:
    logger.info("shutdown_job_finder_agent: cache_clear")
    get_job_finder_agent.cache_clear()


@lru_cache
def get_job_finder_agent() -> SimpleAgent:
    settings = get_settings()
    logger.info(
        "创建 Job Finder Agent model={} base_url={} llm_key={} jsearch_key={}",
        settings.llm_model_id,
        settings.llm_base_url,
        mask_secret(settings.llm_api_key),
        mask_secret(settings.jsearch_api_key),
    )
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
