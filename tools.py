# tools.py

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

from schemas import EvidenceItem


load_dotenv()


def _get_tavily_client() -> TavilyClient:
    """Create a Tavily client using the configured API key."""

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return TavilyClient(api_key=api_key)


@tool
def web_research(query: str) -> list[dict[str, str]]:
    """
    Search the web for focused, reliable information about a topic.

    Returns compact evidence containing:
    - source title
    - source URL
    - relevant snippet

    The tool intentionally limits the amount of returned content to
    reduce unnecessary downstream LLM token usage.
    """

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    client = _get_tavily_client()

    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=False,
            include_raw_content=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Tavily research failed for query '{query}': {exc}"
        ) from exc

    evidence: list[dict[str, str]] = []

    for result in response.get("results", []):
        title = str(result.get("title", "")).strip()
        url = str(result.get("url", "")).strip()
        content = str(result.get("content", "")).strip()

        if not title or not url or not content:
            continue

        # Keep individual evidence compact.
        evidence.append(
            EvidenceItem(
                title=title,
                url=url,
                snippet=content[:800],
            ).model_dump()
        )

    return evidence


def research_topic(
    queries: list[str],
    max_queries: int = 3,
) -> list[EvidenceItem]:
    """
    Execute a small number of focused Tavily searches.

    This function is intentionally bounded to keep API usage and
    downstream token consumption reasonable.
    """

    if not queries:
        return []

    all_evidence: list[EvidenceItem] = []
    seen_urls: set[str] = set()

    for query in queries[:max_queries]:
        results = web_research.invoke({"query": query})

        for item in results:
            evidence = EvidenceItem.model_validate(item)

            # Avoid passing duplicate sources downstream.
            if evidence.url in seen_urls:
                continue

            seen_urls.add(evidence.url)
            all_evidence.append(evidence)

    return all_evidence


def format_evidence(
    evidence: list[EvidenceItem],
    max_items: int = 8,
) -> str:
    """
    Convert structured evidence into a compact prompt-friendly format.

    Only the limited evidence required by downstream agents is included.
    """

    if not evidence:
        return "No external research evidence is available."

    selected = evidence[:max_items]

    chunks: list[str] = []

    for index, item in enumerate(selected, start=1):
        chunks.append(
            f"[Source {index}]\n"
            f"Title: {item.title}\n"
            f"URL: {item.url}\n"
            f"Evidence: {item.snippet}"
        )

    return "\n\n".join(chunks)