# pipeline.py

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterator

from langgraph.graph import END, START, StateGraph

from agents import (
    decide_research,
    plan_blog,
    research,
    review_blog,
    revise_blog,
    write_blog,
)
from schemas import BlogState


# =============================================================================
# Configuration
# =============================================================================

OUTPUT_DIR = Path("outputs")

# Maximum number of revision passes allowed.
# Keeping this at 1 controls Gemini API token usage.
MAX_REVISIONS = 1


# =============================================================================
# Routing
# =============================================================================

def route_research(state: BlogState) -> str:
    """
    Route the graph after the research-decision node.

    Returns:
        "research"      -> run Tavily research
        "closed_book"   -> skip research and go directly to planning
    """

    if state.get("research_mode") == "research":
        return "research"

    return "closed_book"


def route_review(state: BlogState) -> str:
    """
    Route the graph after reviewing the draft.

    A revision is allowed only when:
    1. The reviewer requests it.
    2. The maximum revision count has not been reached.
    """

    review = state.get("review")

    if review is None:
        raise ValueError(
            "Cannot route review: ReviewResult is missing from state."
        )

    revision_count = state.get("revision_count", 0)

    if review.needs_revision and revision_count < MAX_REVISIONS:
        return "needs_revision"

    return "approved"


# =============================================================================
# Finalization
# =============================================================================

def _slugify(text: str) -> str:
    """
    Convert a title/topic into a filesystem-safe slug.
    """

    slug = text.lower().strip()

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        slug,
    )

    slug = slug.strip("-")

    return slug[:80] or "technical-blog"


def finalize_blog(state: BlogState) -> dict:
    """
    Save the approved draft as a Markdown file.
    """

    final_content = state.get("draft", "").strip()

    if not final_content:
        raise ValueError(
            "Cannot finalize an empty blog."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plan = state.get("plan")

    if plan and plan.title:
        filename_base = plan.title
    else:
        filename_base = state["topic"]

    filename = (
        f"{_slugify(filename_base)}"
        f"-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    )

    output_path = OUTPUT_DIR / filename

    output_path.write_text(
        final_content,
        encoding="utf-8",
    )

    return {
        "final": final_content,
        "output_path": str(output_path),
        "events": [
            f"Blog finalized and saved to {output_path}."
        ],
    }


# =============================================================================
# Graph Construction
# =============================================================================

def build_graph():
    """
    Build and compile the LangGraph StateGraph.

    Architecture:

        START
          |
          v
    research_decision
       /          \
      /            \
 research       closed_book
    |                |
    |                |
    +-------+--------+
            |
            v
           plan
            |
            v
           write
            |
            v
          review
         /      \
        /        \
   revise       finalize
      |             |
      |             v
      +--------->  END
         |
         +-------> review
    """

    graph = StateGraph(BlogState)

    # -------------------------------------------------------------------------
    # Nodes
    # -------------------------------------------------------------------------

    graph.add_node(
        "research_decision",
        decide_research,
    )

    graph.add_node(
        "research",
        research,
    )

    graph.add_node(
        "plan",
        plan_blog,
    )

    graph.add_node(
        "write",
        write_blog,
    )

    graph.add_node(
        "review",
        review_blog,
    )

    graph.add_node(
        "revise",
        revise_blog,
    )

    graph.add_node(
        "finalize",
        finalize_blog,
    )

    # -------------------------------------------------------------------------
    # START → Research Decision
    # -------------------------------------------------------------------------

    graph.add_edge(
        START,
        "research_decision",
    )

    # -------------------------------------------------------------------------
    # Research Conditional Routing
    # -------------------------------------------------------------------------

    graph.add_conditional_edges(
        "research_decision",
        route_research,
        {
            "research": "research",
            "closed_book": "plan",
        },
    )

    # Research → Plan
    graph.add_edge(
        "research",
        "plan",
    )

    # -------------------------------------------------------------------------
    # Main Generation Pipeline
    # -------------------------------------------------------------------------

    graph.add_edge(
        "plan",
        "write",
    )

    graph.add_edge(
        "write",
        "review",
    )

    # -------------------------------------------------------------------------
    # Review Conditional Routing
    # -------------------------------------------------------------------------

    graph.add_conditional_edges(
        "review",
        route_review,
        {
            "needs_revision": "revise",
            "approved": "finalize",
        },
    )

    # -------------------------------------------------------------------------
    # Revision → Review
    # -------------------------------------------------------------------------

    graph.add_edge(
        "revise",
        "review",
    )

    # -------------------------------------------------------------------------
    # Finalize → END
    # -------------------------------------------------------------------------

    graph.add_edge(
        "finalize",
        END,
    )

    return graph.compile()


# =============================================================================
# Compiled Graph
# =============================================================================

blog_graph = build_graph()


# =============================================================================
# Initial State
# =============================================================================

def _create_initial_state(
    topic: str,
    as_of: str,
) -> BlogState:
    """
    Create the initial LangGraph state.
    """

    topic = topic.strip()

    if not topic:
        raise ValueError(
            "Topic cannot be empty."
        )

    return {
        "topic": topic,
        "as_of": as_of.strip() or "current",
        "revision_count": 0,
        "events": [],
    }


# =============================================================================
# Standard Execution
# =============================================================================

def run_blog(
    topic: str,
    as_of: str = "current",
) -> BlogState:
    """
    Execute the complete LangGraph workflow once.

    Use this when streaming is not required.
    """

    initial_state = _create_initial_state(
        topic=topic,
        as_of=as_of,
    )

    return blog_graph.invoke(
        initial_state
    )


# =============================================================================
# Streaming Execution
# =============================================================================

def stream_blog(
    topic: str,
    as_of: str = "current",
) -> Iterator[dict]:
    """
    Execute the LangGraph workflow once while streaming node updates.

    Each yielded item contains the state update produced by one or more
    LangGraph nodes.

    Example:

        for update in stream_blog("RAG", "2026-10-08"):
            print(update)
    """

    initial_state = _create_initial_state(
        topic=topic,
        as_of=as_of,
    )

    yield from blog_graph.stream(
        initial_state,
        stream_mode="updates",
    )


# =============================================================================
# Graph Visualization Helper
# =============================================================================

def get_graph_mermaid() -> str:
    """
    Return the LangGraph workflow as a Mermaid diagram.

    Useful for documentation and the Streamlit UI.
    """

    return blog_graph.get_graph().draw_mermaid()


# =============================================================================
# Local Execution
# =============================================================================

if __name__ == "__main__":

    topic = input(
        "\nEnter a technical blog topic: "
    ).strip()

    if not topic:
        raise SystemExit(
            "Topic cannot be empty."
        )

    print(
        "\nStarting LangGraph Blog Writing Agent...\n"
    )

    final_state = run_blog(
        topic=topic,
        as_of="current",
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "WORKFLOW COMPLETE"
    )

    print(
        "=" * 60
    )

    print(
        f"\nTopic: {final_state['topic']}"
    )

    print(
        f"Research Mode: "
        f"{final_state.get('research_mode', 'unknown')}"
    )

    if final_state.get("plan"):

        print(
            f"Title: "
            f"{final_state['plan'].title}"
        )

    if final_state.get("review"):

        review = final_state["review"]

        print(
            f"Review Score: "
            f"{review.score}/10"
        )

        print(
            f"Revision Required: "
            f"{review.needs_revision}"
        )

    print(
        f"Revision Count: "
        f"{final_state.get('revision_count', 0)}"
    )

    print(
        f"Output: "
        f"{final_state.get('output_path')}"
    )

    print("\nEvents:")

    for event in final_state.get(
        "events",
        [],
    ):
        print(
            f"  • {event}"
        )
