from pipeline import route_research, route_review
from schemas import BlogState, ReviewResult


def make_review(
    *,
    needs_revision: bool,
    score: int = 8,
) -> ReviewResult:
    return ReviewResult(
        score=score,
        strengths=["Good structure"],
        issues=["Needs more technical depth"]
        if needs_revision
        else [],
        needs_revision=needs_revision,
        summary="Test review result.",
    )


def test_route_research_when_research_is_needed():
    state: BlogState = {
        "research_mode": "research",
    }

    assert route_research(state) == "research"


def test_route_research_when_research_is_not_needed():
    state: BlogState = {
        "research_mode": "closed_book",
    }

    assert route_research(state) == "closed_book"


def test_route_review_to_revision():
    state: BlogState = {
        "revision_count": 0,
        "review": make_review(
            needs_revision=True,
            score=6,
        ),
    }

    assert route_review(state) == "needs_revision"


def test_route_review_to_finalize():
    state: BlogState = {
        "revision_count": 0,
        "review": make_review(
            needs_revision=False,
            score=9,
        ),
    }

    assert route_review(state) == "approved"


def test_route_review_stops_after_max_revision():
    state: BlogState = {
        "revision_count": 1,
        "review": make_review(
            needs_revision=True,
            score=6,
        ),
    }

    assert route_review(state) == "approved"