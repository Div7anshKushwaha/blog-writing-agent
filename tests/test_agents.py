from unittest.mock import MagicMock

import agents
from langchain_core.runnables import RunnableLambda

from schemas import (
    BlogPlan,
    BlogSection,
    ResearchDecision,
    ReviewResult,
)


def test_decide_research(mocker):
    expected = ResearchDecision(
        needs_research=True,
        research_mode="research",
        queries=["latest developments in RAG"],
        rationale="The topic contains information that may have changed recently.",
    )

    mock_llm = MagicMock()

    structured_llm = RunnableLambda(
        lambda _: expected
    )

    mock_llm.with_structured_output.return_value = structured_llm

    mocker.patch(
        "agents.get_llm",
        return_value=mock_llm,
    )

    result = agents.decide_research(
        {
            "topic": "Latest developments in Retrieval Augmented Generation",
            "as_of": "2026-10-08",
        }
    )

    assert result["research_mode"] == "research"

    assert result["research_queries"] == [
        "latest developments in RAG"
    ]


def test_plan_blog(mocker):
    expected = BlogPlan(
        title="Understanding Retrieval Augmented Generation",
        audience="AI engineers",
        tone="Technical and practical",
        purpose="Explain the fundamentals and workflow of RAG.",
        sections=[
            BlogSection(
                heading="Introduction",
                purpose="Introduce RAG.",
                key_points=[
                    "Definition",
                    "Why it matters",
                ],
            )
        ],
    )

    mock_llm = MagicMock()

    structured_llm = RunnableLambda(
        lambda _: expected
    )

    mock_llm.with_structured_output.return_value = structured_llm

    mocker.patch(
        "agents.get_llm",
        return_value=mock_llm,
    )

    result = agents.plan_blog(
        {
            "topic": "Retrieval Augmented Generation",
            "as_of": "2026-10-08",
            "evidence": [],
        }
    )

    assert isinstance(result["plan"], BlogPlan)

    assert (
        result["plan"].title
        == "Understanding Retrieval Augmented Generation"
    )

    assert len(result["plan"].sections) == 1


def test_review_blog(mocker):
    expected = ReviewResult(
        score=8,
        strengths=["Clear structure"],
        issues=["Could include more examples"],
        needs_revision=True,
        summary="Good draft with a minor improvement needed.",
    )

    mock_llm = MagicMock()

    structured_llm = RunnableLambda(
        lambda _: expected
    )

    mock_llm.with_structured_output.return_value = structured_llm

    mocker.patch(
        "agents.get_llm",
        return_value=mock_llm,
    )

    plan = BlogPlan(
        title="RAG",
        audience="AI engineers",
        tone="Technical",
        purpose="Explain RAG.",
        sections=[
            BlogSection(
                heading="Introduction",
                purpose="Introduce RAG.",
                key_points=["Definition"],
            )
        ],
    )

    result = agents.review_blog(
        {
            "topic": "Retrieval Augmented Generation",
            "plan": plan,
            "evidence": [],
            "draft": "# RAG\n\nA technical explanation.",
        }
    )

    assert isinstance(result["review"], ReviewResult)
    assert result["review"].score == 8
    assert result["review"].needs_revision is True