from schemas import (
    BlogPlan,
    BlogSection,
    EvidenceItem,
    ResearchDecision,
    ReviewResult,
)


def test_research_decision():
    decision = ResearchDecision(
        needs_research=True,
        research_mode="research",
        queries=["latest developments in RAG"],
        rationale="The topic requires current information.",
    )

    assert decision.needs_research is True
    assert decision.research_mode == "research"
    assert len(decision.queries) == 1


def test_evidence_item():
    evidence = EvidenceItem(
        title="Example Source",
        url="https://example.com",
        snippet="Relevant information.",
    )

    assert evidence.title == "Example Source"
    assert evidence.url.startswith("https://")


def test_blog_plan():
    section = BlogSection(
        heading="Introduction",
        purpose="Introduce the topic.",
        key_points=["Definition", "Why it matters"],
    )

    plan = BlogPlan(
        title="Understanding RAG",
        audience="AI engineers",
        tone="Technical and practical",
        purpose="Explain how RAG works.",
        sections=[section],
    )

    assert plan.title == "Understanding RAG"
    assert len(plan.sections) == 1
    assert plan.sections[0].heading == "Introduction"


def test_review_result():
    review = ReviewResult(
        score=8,
        strengths=["Clear explanation"],
        issues=["Add more examples"],
        needs_revision=True,
        summary="Good draft with minor improvements needed.",
    )

    assert 1 <= review.score <= 10
    assert review.needs_revision is True
    assert len(review.issues) == 1