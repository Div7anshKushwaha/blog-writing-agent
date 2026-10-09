# agents.py

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas import (
    BlogPlan,
    BlogState,
    ResearchDecision,
    ReviewResult,
)
from tools import format_evidence, research_topic


load_dotenv()


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_MODEL = "gemini-3.7-flash"

# Keep prompts and generated responses bounded.
MAX_EVIDENCE_ITEMS = 5
MAX_EVIDENCE_CHARS = 500
MAX_DRAFT_CHARS_FOR_REVIEW = 12000
MAX_DRAFT_CHARS_FOR_REVISION = 12000

# Approximate output limits.
# Keep responses bounded to limit API usage and avoid oversized outputs.
RESEARCH_DECISION_TOKENS = 300
PLAN_TOKENS = 1500
WRITER_TOKENS = 2200
REVIEW_TOKENS = 500
REVISION_TOKENS = 2200


# =============================================================================
# Model
# =============================================================================


def get_llm(
    *,
    max_tokens: int | None = None,
) -> ChatGoogleGenerativeAI:
    """
    Create a Google Gemini chat model.

    API credentials are loaded from environment variables.
    """

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Google Gemini API key is not configured. "
            "Set GOOGLE_API_KEY (or GEMINI_API_KEY) in your .env file."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    kwargs = {
        "model": model,
        "temperature": 1.0,
        "api_key": api_key,
    }

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    return ChatGoogleGenerativeAI(**kwargs)


# =============================================================================
# Helper Functions
# =============================================================================


def _compact_evidence(state: BlogState) -> str:
    """
    Return only a small amount of research evidence.

    This prevents large Tavily results from being repeatedly sent to
    multiple LLM calls.
    """

    evidence = state.get("evidence", [])

    if not evidence:
        return "No external research was used."

    compact = []

    for index, item in enumerate(
        evidence[:MAX_EVIDENCE_ITEMS],
        start=1,
    ):
        snippet = item.snippet[:MAX_EVIDENCE_CHARS].strip()

        compact.append(
            f"[{index}] {item.title}\n"
            f"URL: {item.url}\n"
            f"Evidence: {snippet}"
        )

    return "\n\n".join(compact)


def _compact_plan(plan: BlogPlan) -> str:
    """
    Convert the blog plan into a compact representation.

    We do not need all Pydantic metadata or pretty JSON formatting.
    """

    sections = []

    for index, section in enumerate(plan.sections, start=1):
        points = "; ".join(section.key_points[:4])

        sections.append(
            f"{index}. {section.heading}\n"
            f"Purpose: {section.purpose}\n"
            f"Key points: {points}"
        )

    return (
        f"Title: {plan.title}\n"
        f"Audience: {plan.audience}\n"
        f"Tone: {plan.tone}\n"
        f"Purpose: {plan.purpose}\n\n"
        f"Sections:\n"
        + "\n\n".join(sections)
    )


def _safe_draft(draft: str, max_chars: int) -> str:
    """
    Bound draft size before sending it to another LLM call.
    """

    if len(draft) <= max_chars:
        return draft

    return (
        draft[:max_chars]
        + "\n\n[Draft truncated for context efficiency.]"
    )


def _extract_message_text(content: object) -> str:
    """Extract user-facing text from string or Gemini content-block output."""

    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return ""

    text_parts = []
    for block in content:
        if isinstance(block, str):
            text_parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str):
                text_parts.append(text)

    return "\n".join(text_parts)


# =============================================================================
# Research Decision Agent
# =============================================================================


RESEARCH_DECISION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Decide whether a technical blog topic needs web research.

Use research when:
- facts may have changed,
- current versions/releases/benchmarks matter,
- recent developments matter,
- reliable external grounding materially improves the article.

Use closed_book when:
- the topic is stable,
- general technical knowledge is sufficient.

If research is needed, provide at most 2 focused search queries.

Keep the rationale very short.""",
        ),
        (
            "human",
            """Topic: {topic}
As-of date: {as_of}

Decide the research strategy.""",
        ),
    ]
)


def decide_research(state: BlogState) -> dict:
    """
    Decide whether the workflow should use external research.
    """

    llm = get_llm(max_tokens=RESEARCH_DECISION_TOKENS)

    structured_llm = llm.with_structured_output(
        ResearchDecision,
        method="json_schema",
    )

    chain = RESEARCH_DECISION_PROMPT | structured_llm

    decision = chain.invoke(
        {
            "topic": state["topic"],
            "as_of": state.get("as_of", "current"),
        }
    )

    queries = (
        decision.queries[:2]
        if decision.needs_research
        else []
    )

    return {
        "research_mode": decision.research_mode,
        "research_queries": queries,
        "events": [
            (
                f"Research decision: {decision.research_mode} — "
                f"{decision.rationale}"
            )
        ],
    }


# =============================================================================
# Research Agent
# =============================================================================


def research(state: BlogState) -> dict:
    """
    Execute focused research queries selected by the decision agent.
    """

    queries = state.get("research_queries", [])

    if not queries:
        return {
            "evidence": [],
            "events": [
                "Research skipped: closed-book workflow selected."
            ],
        }

    evidence = research_topic(
        queries=queries,
        max_queries=2,
    )

    return {
        "evidence": evidence[:MAX_EVIDENCE_ITEMS],
        "events": [
            f"Research completed: collected {len(evidence)} unique sources."
        ],
    }


# =============================================================================
# Planner Agent
# =============================================================================


PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a technical content strategist.

Create a concise, practical blog plan.

The plan must:
- define the target audience,
- define the purpose,
- choose a technical tone,
- organize the article logically,
- provide useful key points for each section.

Use 3-4 sections, with exactly 3 concise key points per section.
Keep the title, audience, tone, purposes, headings, and key points brief.

Do not write the article.
Do not invent facts or sources.""",
        ),
        (
            "human",
            """Topic: {topic}
As-of date: {as_of}

Research evidence:
{evidence}

Create the structured blog plan.""",
        ),
    ]
)


def plan_blog(state: BlogState) -> dict:
    """
    Create a compact structured blog plan.
    """

    llm = get_llm(max_tokens=PLAN_TOKENS)

    structured_llm = llm.with_structured_output(
        BlogPlan,
        method="json_schema",
    )

    chain = PLANNER_PROMPT | structured_llm

    plan = chain.invoke(
        {
            "topic": state["topic"],
            "as_of": state.get("as_of", "current"),
            "evidence": _compact_evidence(state),
        }
    )

    return {
        "plan": plan,
        "events": [
            f"Blog plan created with {len(plan.sections)} sections."
        ],
    }


# =============================================================================
# Writer Agent
# =============================================================================


WRITER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert technical writer and AI engineer.

Write one complete technical blog in Markdown.

Requirements:
- Follow the supplied plan.
- Explain technical concepts accurately.
- Be practical and concise.
- Use examples only when useful.
- Do not invent citations or sources.
- Ground time-sensitive claims in supplied evidence.
- Do not mention agents, prompts, LangGraph, workflow, or internal implementation.
- Return only the Markdown article.

Target length: approximately 900-1400 words.""",
        ),
        (
            "human",
            """Topic: {topic}
As-of date: {as_of}

Blog plan:
{plan}

Research evidence:
{evidence}

Write the complete article.""",
        ),
    ]
)


def write_blog(state: BlogState) -> dict:
    """
    Generate the initial complete blog draft.
    """

    llm = get_llm(max_tokens=WRITER_TOKENS)

    chain = WRITER_PROMPT | llm

    response = chain.invoke(
        {
            "topic": state["topic"],
            "as_of": state.get("as_of", "current"),
            "plan": _compact_plan(state["plan"]),
            "evidence": _compact_evidence(state),
        }
    )

    draft = _extract_message_text(response.content)

    if not isinstance(draft, str) or not draft.strip():
        raise RuntimeError(
            "Writer returned an empty blog draft."
        )

    return {
        "draft": draft.strip(),
        "events": [
            "Initial technical blog draft generated."
        ],
    }


# =============================================================================
# Reviewer Agent
# =============================================================================


REVIEWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a strict technical blog reviewer.

Evaluate:
1. Technical correctness
2. Factual grounding
3. Coverage of the plan
4. Clarity
5. Practical usefulness

Approve strong drafts.

Set needs_revision=true only when there are meaningful issues
that should actually be fixed.

Keep feedback short and actionable.
Do not request cosmetic changes.""",
        ),
        (
            "human",
            """Topic: {topic}

Blog plan:
{plan}

Research evidence:
{evidence}

Current draft:
{draft}

Review the draft.""",
        ),
    ]
)


def review_blog(state: BlogState) -> dict:
    """
    Evaluate the current draft using structured output.
    """

    llm = get_llm(max_tokens=REVIEW_TOKENS)

    structured_llm = llm.with_structured_output(
        ReviewResult,
        method="json_schema",
    )

    chain = REVIEWER_PROMPT | structured_llm

    review = chain.invoke(
        {
            "topic": state["topic"],
            "plan": _compact_plan(state["plan"]),
            "evidence": _compact_evidence(state),
            "draft": _safe_draft(
                state["draft"],
                MAX_DRAFT_CHARS_FOR_REVIEW,
            ),
        }
    )

    return {
        "review": review,
        "events": [
            (
                f"Review completed: {review.score}/10 — "
                f"{'revision required' if review.needs_revision else 'approved'}."
            )
        ],
    }


# =============================================================================
# Revision Agent
# =============================================================================


REVISION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a senior technical editor.

Revise the complete Markdown article using the reviewer feedback.

Rules:
- Fix only substantive issues identified by the reviewer.
- Preserve accurate content.
- Preserve useful structure.
- Use supplied evidence for factual corrections.
- Do not invent sources.
- Return the ENTIRE revised article.
- Do not mention the review process.
- Return only Markdown.

Target length: approximately 900-1400 words.""",
        ),
        (
            "human",
            """Topic: {topic}

Blog plan:
{plan}

Research evidence:
{evidence}

Current draft:
{draft}

Reviewer feedback:
{review}

Produce the complete revised article.""",
        ),
    ]
)


def revise_blog(state: BlogState) -> dict:
    """
    Perform one controlled revision pass.

    LangGraph limits this workflow to one revision.
    """

    llm = get_llm(max_tokens=REVISION_TOKENS)

    chain = REVISION_PROMPT | llm

    review = state["review"]

    response = chain.invoke(
        {
            "topic": state["topic"],
            "plan": _compact_plan(state["plan"]),
            "evidence": _compact_evidence(state),
            "draft": _safe_draft(
                state["draft"],
                MAX_DRAFT_CHARS_FOR_REVISION,
            ),
            "review": (
                f"Score: {review.score}/10\n"
                f"Strengths: {'; '.join(review.strengths[:3])}\n"
                f"Issues: {'; '.join(review.issues[:4])}\n"
                f"Summary: {review.summary}"
            ),
        }
    )

    revised_draft = _extract_message_text(response.content)

    if (
        not isinstance(revised_draft, str)
        or not revised_draft.strip()
    ):
        raise RuntimeError(
            "Revision agent returned an empty article."
        )

    return {
        "draft": revised_draft.strip(),
        "revision_count": state.get("revision_count", 0) + 1,
        "events": [
            "Revision pass completed using reviewer feedback."
        ],
    }
