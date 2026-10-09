# schemas.py

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


# ============================================================================
# Research Decision
# ============================================================================

class ResearchDecision(BaseModel):
    """Decision produced by the research-decision node."""

    needs_research: bool = Field(
        description="Whether external web research is necessary for the topic."
    )

    research_mode: Literal["research", "closed_book"] = Field(
        description="Research strategy selected for the topic."
    )

    queries: list[str] = Field(
        default_factory=list,
        description="Focused web-search queries to use if research is required.",
    )

    rationale: str = Field(
        description="Short explanation for why research is or is not necessary."
    )


# ============================================================================
# Research Evidence
# ============================================================================

class EvidenceItem(BaseModel):
    """A compact piece of evidence returned from web research."""

    title: str = Field(description="Title of the source.")

    url: str = Field(description="URL of the source.")

    snippet: str = Field(
        description="Compact relevant information extracted from the source."
    )


# ============================================================================
# Blog Plan
# ============================================================================

class BlogSection(BaseModel):
    """Structure for one section of the blog."""

    heading: str = Field(description="Section heading.")

    purpose: str = Field(
        description="What this section should accomplish."
    )

    key_points: list[str] = Field(
        default_factory=list,
        description="Important points that should be covered.",
    )


class BlogPlan(BaseModel):
    """Structured plan used by the writer."""

    title: str = Field(description="Proposed technical blog title.")

    audience: str = Field(
        description="Target audience for the blog."
    )

    tone: str = Field(
        description="Writing tone for the blog."
    )

    purpose: str = Field(
        description="Overall purpose of the article."
    )

    sections: list[BlogSection] = Field(
        min_length=1,
        description="Ordered sections of the blog.",
    )


# ============================================================================
# Review Result
# ============================================================================

class ReviewResult(BaseModel):
    """Structured evaluation produced by the reviewer."""

    score: int = Field(
        ge=1,
        le=10,
        description="Overall quality score from 1 to 10.",
    )

    strengths: list[str] = Field(
        default_factory=list,
        description="Important strengths of the draft.",
    )

    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues that should be fixed.",
    )

    needs_revision: bool = Field(
        description="Whether the draft requires another revision pass."
    )

    summary: str = Field(
        description="Short overall assessment of the draft."
    )


# ============================================================================
# LangGraph State
# ============================================================================

class BlogState(TypedDict, total=False):
    """
    Shared state flowing through the LangGraph workflow.

    LangGraph nodes read values from this state and return partial state
    updates rather than manually passing data between functions.
    """

    # User input
    topic: str
    as_of: str

    # Research decision
    research_mode: Literal["research", "closed_book"]
    research_queries: list[str]

    # Research
    evidence: list[EvidenceItem]

    # Planning
    plan: BlogPlan

    # Generation
    draft: str

    # Evaluation
    review: ReviewResult

    # Revision control
    revision_count: int

    # Final output
    final: str
    output_path: str

    # UI / observability
    events: Annotated[list[str], lambda existing, new: existing + new]