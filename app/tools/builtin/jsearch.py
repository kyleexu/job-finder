"""JSearch HTTP 工具：OpenWeb Ninja GET /search-v2（不是 MCP）。"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
from loguru import logger

from ...config import Settings, get_settings
from ...logging_setup import preview
from ..base import Tool


class JSearchClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.jsearch_api_key.strip()
        self._base_url = settings.jsearch_base_url.rstrip("/")
        self._timeout = settings.jsearch_timeout
        self._use_rapidapi = "rapidapi.com" in self._base_url

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._api_key:
            raise RuntimeError(
                "JSEARCH_API_KEY 未配置。把 OpenWeb Ninja 的 X-API-Key 写入 .env。"
            )
        headers = {"Accept": "application/json"}
        if self._use_rapidapi:
            headers["x-rapidapi-key"] = self._api_key
            headers["x-rapidapi-host"] = "jsearch.p.rapidapi.com"
        else:
            headers["X-API-Key"] = self._api_key

        query = {key: value for key, value in params.items() if value not in (None, "", [])}
        url = f"{self._base_url}{path}"
        logger.info(
            "JSearch 请求 method=GET url={} params={} rapidapi={} timeout={}",
            url,
            query,
            self._use_rapidapi,
            self._timeout,
        )
        started = time.perf_counter()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers, params=query)
        except Exception:
            logger.exception(
                "JSearch 网络异常 elapsed_ms={:.0f} url={}",
                (time.perf_counter() - started) * 1000,
                url,
            )
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "JSearch 响应 elapsed_ms={:.0f} status={} bytes={} body={}",
            elapsed_ms,
            response.status_code,
            len(response.content),
            preview(response.text, 600),
        )
        if response.status_code == 429:
            raise RuntimeError("JSearch 配额已用完或触发限流，请稍后再试。")
        if response.status_code in {401, 403}:
            raise RuntimeError(f"JSearch 鉴权失败 HTTP {response.status_code}: {response.text[:300]}")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected JSearch response")
        return payload


def _jobs_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("jobs"), list):
        return [item for item in data["jobs"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    jobs = payload.get("jobs")
    if isinstance(jobs, list):
        return [item for item in jobs if isinstance(item, dict)]
    return []


def _cursor_from_payload(payload: dict[str, Any]) -> str | None:
    if payload.get("cursor"):
        return str(payload["cursor"])
    data = payload.get("data")
    if isinstance(data, dict) and data.get("cursor"):
        return str(data["cursor"])
    return None


def _summarize_job(job: dict[str, Any], *, max_desc: int = 280) -> dict[str, Any]:
    description = str(job.get("job_description") or "").strip().replace("\n", " ")
    if len(description) > max_desc:
        description = description[: max_desc - 1] + "…"
    location = job.get("job_location") or ", ".join(
        str(part) for part in (job.get("job_city"), job.get("job_state"), job.get("job_country")) if part
    )
    return {
        "job_id": job.get("job_id") or job.get("job_uid"),
        "title": job.get("job_title"),
        "employer": job.get("employer_name"),
        "employer_website": job.get("employer_website"),
        "publisher": job.get("job_publisher"),
        "location": location or None,
        "remote": job.get("job_is_remote"),
        "employment_type": job.get("job_employment_type"),
        "posted_at": job.get("job_posted_at") or job.get("job_posted_at_datetime_utc"),
        "apply_link": job.get("job_apply_link"),
        "google_link": job.get("job_google_link"),
        "salary": job.get("job_salary_string"),
        "salary_min": job.get("job_min_salary"),
        "salary_max": job.get("job_max_salary"),
        "description": description or None,
    }


class SearchJobsTool(Tool):
    name = "search_jobs"
    description = (
        "Search live jobs via OpenWeb Ninja JSearch HTTP API (GET /search-v2). "
        "Put job title and location in query, e.g. 'backend engineer in Berlin'. "
        "Each job includes apply_link / google_link; always pass those URLs through to the user."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Free-form search, include title and location",
            },
            "country": {
                "type": "string",
                "description": "ISO country code, e.g. us, de, gb",
            },
            "date_posted": {
                "type": "string",
                "enum": ["all", "today", "3days", "week", "month"],
            },
            "work_from_home": {
                "type": "boolean",
                "description": "Only remote jobs",
            },
            "employment_types": {
                "type": "string",
                "description": "Comma list: FULLTIME, PARTTIME, CONTRACTOR, INTERN",
            },
            "num_pages": {
                "type": "integer",
                "description": "Pages to fetch, 1-20. Each page costs one request.",
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor from a previous search",
            },
        },
        "required": ["query"],
    }

    def __init__(self, client: JSearchClient) -> None:
        self._client = client

    def run(self, arguments: dict[str, Any]) -> str:
        logger.info("search_jobs 入参 {}", arguments)
        query = str(arguments.get("query") or arguments.get("keywords") or "").strip()
        if not query:
            return "Please provide query, e.g. developer jobs in chicago"

        request: dict[str, Any] = {
            "query": query,
            "country": str(arguments.get("country") or "us").lower(),
            "num_pages": int(arguments.get("num_pages") or 1),
        }
        if arguments.get("date_posted"):
            request["date_posted"] = arguments["date_posted"]
        if arguments.get("cursor"):
            request["cursor"] = arguments["cursor"]
        if arguments.get("language"):
            request["language"] = arguments["language"]
        if arguments.get("employment_types"):
            request["employment_types"] = arguments["employment_types"]
        wfh = arguments.get("work_from_home", arguments.get("remote"))
        if wfh is True or str(wfh).lower() in {"1", "true", "yes"}:
            request["work_from_home"] = "true"

        try:
            payload = self._client.get("/search-v2", request)
        except Exception as exc:
            return str(exc)

        jobs = [_summarize_job(job) for job in _jobs_from_payload(payload)]
        titles = [job.get("title") for job in jobs]
        logger.info(
            "search_jobs 结果 status={} count={} titles={}",
            payload.get("status"),
            len(jobs),
            titles,
        )
        return json.dumps(
            {
                "status": payload.get("status"),
                "count": len(jobs),
                "cursor": _cursor_from_payload(payload),
                "jobs": jobs,
            },
            ensure_ascii=False,
            indent=2,
        )


class GetJobDetailsTool(Tool):
    name = "get_job_details"
    description = "Get JSearch job details by job_id returned from search_jobs (GET /job-details)."
    parameters = {
        "type": "object",
        "properties": {
            "job_id": {
                "type": "string",
                "description": "job_id from search_jobs",
            },
            "country": {
                "type": "string",
                "description": "ISO country code, default us",
            },
        },
        "required": ["job_id"],
    }

    def __init__(self, client: JSearchClient) -> None:
        self._client = client

    def run(self, arguments: dict[str, Any]) -> str:
        logger.info("get_job_details 入参 {}", arguments)
        job_id = str(arguments.get("job_id") or "").strip()
        if not job_id:
            return "Please provide job_id from search_jobs"
        try:
            payload = self._client.get(
                "/job-details",
                {
                    "job_id": job_id,
                    "country": str(arguments.get("country") or "us").lower(),
                },
            )
        except Exception as exc:
            return str(exc)

        jobs = _jobs_from_payload(payload)
        if not jobs:
            return json.dumps(payload, ensure_ascii=False, indent=2)[:8000]
        summarized = _summarize_job(jobs[0], max_desc=1500)
        extra = jobs[0]
        summarized["apply_options"] = extra.get("apply_options")
        summarized["benefits"] = extra.get("job_benefits_strings")
        logger.info(
            "get_job_details 结果 title={} employer={} apply_link={}",
            summarized.get("title"),
            summarized.get("employer"),
            summarized.get("apply_link"),
        )
        return json.dumps(summarized, ensure_ascii=False, indent=2)


def build_jsearch_tools(settings: Settings | None = None) -> list[Tool]:
    client = JSearchClient(settings or get_settings())
    return [SearchJobsTool(client), GetJobDetailsTool(client)]
