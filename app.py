# app.py

from __future__ import annotations

from datetime import date
from html import escape
import re
from textwrap import dedent

import streamlit as st

from pipeline import get_graph_mermaid, stream_blog


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="BlogForge — Agentic AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# HTML Helper
# =============================================================================

def render_html(markup: str) -> None:
    """
    Render custom HTML directly instead of passing it through Markdown.
    Markdown treats indented nested tags as code blocks, which exposes the
    HTML source in the UI.
    """
    st.html(dedent(markup).strip())


# =============================================================================
# Design System
# =============================================================================

render_html(
    """
    <style>

    :root {
        --bg: #080a0d;
        --surface: #0d1117;
        --surface-2: #11161d;
        --surface-3: #151b23;
        --border: #222a35;
        --text: #f0f3f6;
        --muted: #8b949e;
        --muted-2: #65707c;
        --accent: #7c5cff;
        --accent-soft: rgba(124, 92, 255, 0.12);
        --green: #3fb950;
        --green-soft: rgba(63, 185, 80, 0.10);
        --yellow: #d29922;
        --yellow-soft: rgba(210, 153, 34, 0.10);
    }

    /* ------------------------------------------------------------------ */
    /* Global                                                            */
    /* ------------------------------------------------------------------ */

    .stApp {
        background:
            radial-gradient(
                circle at 80% 5%,
                rgba(124, 92, 255, 0.08),
                transparent 26rem
            ),
            radial-gradient(
                circle at 10% 35%,
                rgba(56, 139, 253, 0.045),
                transparent 25rem
            ),
            var(--bg);
    }

    .block-container {
        max-width: 1380px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ------------------------------------------------------------------ */
    /* Typography                                                        */
    /* ------------------------------------------------------------------ */

    h1,
    h2,
    h3,
    h4 {
        color: var(--text) !important;
        letter-spacing: -0.025em;
    }

    p,
    li {
        color: #c4cbd3;
    }

    /* ------------------------------------------------------------------ */
    /* Sidebar                                                           */
    /* ------------------------------------------------------------------ */

    section[data-testid="stSidebar"] {
        background: #090c10;
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    .sidebar-brand {
        font-size: 1.35rem;
        font-weight: 850;
        letter-spacing: -0.04em;
        color: #f2f4f7;
    }

    .sidebar-brand span {
        color: var(--accent);
    }

    .sidebar-muted {
        color: #707b87;
        font-size: 0.74rem;
        line-height: 1.65;
    }

    .stack-item {
        display: flex;
        justify-content: space-between;
        padding: 0.45rem 0;
        border-bottom: 1px solid #171d25;
        color: #a8b1bb;
        font-size: 0.77rem;
    }

    .stack-item:last-child {
        border-bottom: none;
    }

    .stack-item span:last-child {
        color: #e1e6eb;
        font-weight: 650;
    }

    /* ------------------------------------------------------------------ */
    /* Hero                                                              */
    /* ------------------------------------------------------------------ */

    .hero {
        padding: 1rem 0 2.4rem;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.38rem 0.75rem;
        border: 1px solid #2b3340;
        border-radius: 999px;
        background: rgba(13, 17, 23, 0.8);
        color: #a9b2bd;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .hero-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 12px rgba(124, 92, 255, 0.75);
    }

    .hero-title {
        margin-top: 1rem;
        font-size: clamp(3rem, 5vw, 4.8rem);
        line-height: 0.98;
        font-weight: 850;
        letter-spacing: -0.055em;
        color: #f5f7fa;
    }

    .hero-title span {
        color: var(--accent);
    }

    .hero-subtitle {
        max-width: 760px;
        margin-top: 1.1rem;
        color: #929ba6;
        font-size: 1rem;
        line-height: 1.7;
    }

    /* ------------------------------------------------------------------ */
    /* Labels / Panels                                                   */
    /* ------------------------------------------------------------------ */

    .section-label {
        margin-bottom: 0.7rem;
        color: #747e89;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .panel {
        border: 1px solid var(--border);
        border-radius: 16px;
        background:
            linear-gradient(
                145deg,
                rgba(17, 22, 29, 0.96),
                rgba(11, 15, 20, 0.96)
            );
        padding: 1.25rem;
        box-shadow:
            0 18px 50px rgba(0, 0, 0, 0.14),
            inset 0 1px 0 rgba(255, 255, 255, 0.015);
    }

    .panel-title {
        color: var(--text);
        font-size: 1rem;
        font-weight: 750;
    }

    .panel-description {
        margin-top: 0.35rem;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.5;
    }

    /* ------------------------------------------------------------------ */
    /* Workflow                                                          */
    /* ------------------------------------------------------------------ */

    .workflow {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        overflow-x: auto;
        padding: 0.4rem 0 0.8rem;
    }

    .workflow-step {
        display: flex;
        align-items: center;
        gap: 0.42rem;
        min-width: max-content;
        padding: 0.52rem 0.7rem;
        border: 1px solid #252d38;
        border-radius: 9px;
        background: #0b0f14;
        color: #7f8995;
        font-size: 0.73rem;
        font-weight: 650;
    }

    .workflow-step.active {
        color: #c9c0ff;
        border-color: rgba(124, 92, 255, 0.65);
        background: var(--accent-soft);
        box-shadow: 0 0 20px rgba(124, 92, 255, 0.08);
    }

    .workflow-step.complete {
        color: #8cda98;
        border-color: rgba(63, 185, 80, 0.35);
        background: var(--green-soft);
    }

    .workflow-step.revision {
        color: #e6c56b;
        border-color: rgba(210, 153, 34, 0.35);
        background: var(--yellow-soft);
    }

    .workflow-arrow {
        color: #4d5763;
        font-size: 0.85rem;
    }

    /* ------------------------------------------------------------------ */
    /* Metrics                                                           */
    /* ------------------------------------------------------------------ */

    .metric-card {
        min-height: 104px;
        padding: 1rem;
        border: 1px solid var(--border);
        border-radius: 14px;
        background: var(--surface);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .metric-value {
        margin-top: 0.45rem;
        color: var(--text);
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }

    /* ------------------------------------------------------------------ */
    /* Sources                                                           */
    /* ------------------------------------------------------------------ */

    .source-card {
        padding: 1rem;
        margin-bottom: 0.65rem;
        border: 1px solid var(--border);
        border-radius: 12px;
        background: #0c1015;
    }

    .source-number {
        color: var(--accent);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .source-title {
        margin-top: 0.3rem;
        color: #e5e9ee;
        font-size: 0.9rem;
        font-weight: 700;
    }

    .source-url {
        margin-top: 0.25rem;
        color: #737f8c;
        font-size: 0.7rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .source-snippet {
        margin-top: 0.65rem;
        color: #9ca6b1;
        font-size: 0.78rem;
        line-height: 1.6;
    }

    /* ------------------------------------------------------------------ */
    /* Blog                                                              */
    /* ------------------------------------------------------------------ */

    .blog-surface {
        padding: 2rem 2.2rem;
        border: 1px solid var(--border);
        border-radius: 18px;
        background:
            linear-gradient(
                180deg,
                rgba(17, 22, 29, 0.98),
                rgba(10, 13, 17, 0.98)
            );
        box-shadow: 0 25px 80px rgba(0, 0, 0, 0.18);
    }

    /* ------------------------------------------------------------------ */
    /* Streamlit Controls                                                */
    /* ------------------------------------------------------------------ */

    .stTextArea textarea,
    .stTextInput input {
        background: #0b0f14 !important;
        border: 1px solid #29313d !important;
        color: #edf1f5 !important;
        border-radius: 11px !important;
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(124, 92, 255, 0.75) !important;
        box-shadow: 0 0 0 1px rgba(124, 92, 255, 0.2) !important;
    }

    div[data-testid="stDateInput"] input {
        background: #0b0f14 !important;
        border-color: #29313d !important;
        color: #edf1f5 !important;
    }

    div.stButton > button[kind="primary"] {
        min-height: 48px;
        border: 1px solid rgba(124, 92, 255, 0.55);
        border-radius: 11px;
        background: var(--accent);
        color: white;
        font-weight: 750;
        box-shadow: 0 10px 28px rgba(124, 92, 255, 0.16);
    }

    div.stButton > button[kind="primary"]:hover {
        border-color: #9b86ff;
        background: #876cff;
    }

    .stDownloadButton button {
        border-radius: 10px !important;
        font-weight: 700 !important;
    }

    div[data-testid="stExpander"] {
        border-color: var(--border) !important;
        border-radius: 11px !important;
        background: rgba(13, 17, 23, 0.65) !important;
    }

    </style>
    """
)


# =============================================================================
# Session State
# =============================================================================

if "result" not in st.session_state:
    st.session_state.result = None

if "events" not in st.session_state:
    st.session_state.events = []

if "completed_nodes" not in st.session_state:
    st.session_state.completed_nodes = []

if "current_node" not in st.session_state:
    st.session_state.current_node = None


# =============================================================================
# Constants
# =============================================================================

EXPECTED_NODES = [
    "research_decision",
    "research",
    "plan",
    "write",
    "review",
    "revise",
    "finalize",
]


# =============================================================================
# Helper Functions
# =============================================================================

def reset_execution_state() -> None:
    st.session_state.result = None
    st.session_state.events = []
    st.session_state.completed_nodes = []
    st.session_state.current_node = None


def render_metric(label: str, value: str) -> None:
    render_html(
        f"""
        <div class="metric-card">
            <div class="metric-label">
                {escape(label)}
            </div>

            <div class="metric-value">
                {escape(value)}
            </div>
        </div>
        """
    )


def render_workflow(
    current_node: str | None,
    completed_nodes: list[str],
) -> None:
    html = '<div class="workflow">'

    for index, node in enumerate(EXPECTED_NODES):

        if node == current_node:
            css_class = "active"
            icon = "●"

        elif node in completed_nodes:
            css_class = "complete"
            icon = "✓"

        else:
            css_class = ""
            icon = "○"

        if node == "revise" and node in completed_nodes:
            css_class = "revision"
            icon = "↻"

        html += (
            f'<div class="workflow-step {css_class}">'
            f"{icon} {escape(node)}"
            f"</div>"
        )

        if index < len(EXPECTED_NODES) - 1:
            html += '<div class="workflow-arrow">→</div>'

    html += "</div>"

    render_html(html)


def render_events(events: list[str]) -> None:
    if not events:
        st.caption("Waiting for workflow events…")
        return

    for event in events:
        render_html(
            f"""
            <div style="
                padding:0.55rem 0;
                border-bottom:1px solid #171d25;
                color:#9da7b2;
                font-size:0.76rem;
                line-height:1.5;
            ">
                <span style="color:#7c5cff;">›</span>
                {escape(event)}
            </div>
            """
        )


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar() -> None:

    with st.sidebar:

        render_html(
            """
            <div class="sidebar-brand">
                Blog<span>Forge</span>
            </div>

            <div class="sidebar-muted" style="margin-top:0.45rem;">
                Agentic technical blog generation powered by a
                stateful LangGraph workflow.
            </div>
            """
        )

        st.divider()

        st.markdown("### Architecture")

        render_html(
            """
            <div class="sidebar-muted">
                <b style="color:#e5e9ee;">START</b><br>
                ↓<br>
                research_decision<br>
                ↓<br>
                research / closed_book<br>
                ↓<br>
                plan<br>
                ↓<br>
                write<br>
                ↓<br>
                review<br>
                ↓<br>
                revise ↺ / finalize<br>
                ↓<br>
                <b style="color:#e5e9ee;">END</b>
            </div>
            """
        )

        st.divider()

        st.markdown("### Technology")

        stack = [
            ("Orchestration", "LangGraph"),
            ("LLM", "Gemini 3.7 Flash"),
            ("Research", "Tavily"),
            ("Abstractions", "LangChain"),
            ("Validation", "Pydantic"),
            ("Frontend", "Streamlit"),
            ("Testing", "pytest"),
        ]

        for label, value in stack:
            render_html(
                f"""
                <div class="stack-item">
                    <span>{escape(label)}</span>
                    <span>{escape(value)}</span>
                </div>
                """
            )

        st.divider()

        st.markdown("### Agent Behavior")

        render_html(
            """
            <div class="sidebar-muted">
                • Decides whether research is necessary<br>
                • Uses bounded web evidence<br>
                • Creates a structured writing plan<br>
                • Generates the complete article<br>
                • Reviews technical quality<br>
                • Conditionally performs one revision
            </div>
            """
        )


# =============================================================================
# Hero
# =============================================================================

def render_hero() -> None:

    render_html(
        """
        <div class="hero">

            <div class="hero-badge">
                <span class="hero-dot"></span>
                Agentic AI · LangGraph · Gemini 3.7 Flash · Tavily
            </div>

            <div class="hero-title">
                Blog<span>Forge</span>
            </div>

            <div class="hero-subtitle">
                An autonomous technical writing workflow that decides when
                to research, plans the article, writes it, evaluates the
                result, and conditionally revises it — all through a
                stateful LangGraph graph.
            </div>

        </div>
        """
    )


# =============================================================================
# Input Panel
# =============================================================================

def render_input_panel() -> tuple[str, date, bool]:

    st.markdown(
        '<div class="section-label">Workspace</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div class="panel">

            <div class="panel-title">
                Create a technical blog
            </div>

            <div class="panel-description">
                Give the agent a topic. It will decide whether external
                research is required before writing.
            </div>

        </div>
        """
    )

    st.markdown(
        "<div style='height:0.8rem'></div>",
        unsafe_allow_html=True,
    )

    topic = st.text_area(
        "Topic",
        placeholder=(
            "Example: How Retrieval-Augmented Generation works "
            "and when to use it"
        ),
        height=145,
        label_visibility="collapsed",
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        as_of = st.date_input(
            "Knowledge date",
            value=date.today(),
            help="Used by the research-decision agent.",
        )

    with col2:
        render_html(
            """
            <div style="
                margin-top:1.75rem;
                color:#707b87;
                font-size:0.72rem;
                line-height:1.5;
            ">
                The agent can operate in closed-book mode or
                invoke Tavily for current information.
            </div>
            """
        )

    run_button = st.button(
        "✦  Run Agentic Workflow",
        type="primary",
        use_container_width=True,
    )

    return topic, as_of, run_button


# =============================================================================
# Graph Panel
# =============================================================================

def render_graph_panel() -> None:

    st.markdown(
        '<div class="section-label">Orchestration</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div class="panel">

            <div class="panel-title">
                LangGraph workflow
            </div>

            <div class="panel-description">
                The graph controls state, branching, review, and revision.
            </div>

        </div>
        """
    )

    st.markdown(
        "<div style='height:0.8rem'></div>",
        unsafe_allow_html=True,
    )

    render_workflow(
        current_node=st.session_state.current_node,
        completed_nodes=st.session_state.completed_nodes,
    )

    with st.expander("View compiled graph definition"):

        try:
            st.code(
                get_graph_mermaid(),
                language="text",
            )

        except Exception as exc:
            st.warning(
                f"Could not load graph definition: {exc}"
            )


# =============================================================================
# Run LangGraph
# =============================================================================

def run_workflow(
    topic: str,
    as_of: date,
) -> None:

    reset_execution_state()

    st.divider()

    st.markdown(
        '<div class="section-label">Execution</div>',
        unsafe_allow_html=True,
    )

    progress_slot = st.empty()
    event_slot = st.empty()

    final_state: dict = {}

    try:

        with st.status(
            "Running BlogForge…",
            expanded=True,
        ) as status:

            for update in stream_blog(
                topic=topic,
                as_of=as_of.isoformat(),
            ):

                if not update:
                    continue

                node_names = list(update.keys())

                for node_name in node_names:

                    st.session_state.current_node = node_name

                    if (
                        node_name
                        not in st.session_state.completed_nodes
                    ):
                        st.session_state.completed_nodes.append(
                            node_name
                        )

                for node_update in update.values():

                    if not isinstance(node_update, dict):
                        continue

                    for key, value in node_update.items():

                        if key == "events":

                            if isinstance(value, list):

                                for event in value:

                                    if (
                                        event
                                        not in st.session_state.events
                                    ):
                                        st.session_state.events.append(
                                            event
                                        )

                        else:
                            final_state[key] = value

                with progress_slot.container():

                    render_workflow(
                        current_node=st.session_state.current_node,
                        completed_nodes=(
                            st.session_state.completed_nodes
                        ),
                    )

                with event_slot.container():

                    render_html(
                        """
                        <div class="panel">

                            <div class="panel-title">
                                Live execution
                            </div>

                            <div class="panel-description">
                                State transitions emitted by LangGraph.
                            </div>

                        </div>
                        """
                    )

                    render_events(
                        st.session_state.events
                    )

            final_state["events"] = (
                st.session_state.events
            )

            st.session_state.current_node = "finalize"

            status.update(
                label="Workflow completed",
                state="complete",
            )

        st.session_state.result = final_state

    except Exception as exc:
        error_text = str(exc)
        lower_error = error_text.lower()
        is_rate_limit = (
            getattr(exc, "status_code", None) == 429
            or getattr(exc, "code", None) == 429
            or any(
                marker in lower_error
                for marker in (
                    "rate_limit_exceeded",
                    "resource_exhausted",
                    "429 too many requests",
                )
            )
        )
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "code", None)
        is_temporary_provider_error = status_code in {500, 502, 503, 504} or any(
            marker in lower_error
            for marker in (
                "503 unavailable",
                "currently experiencing high demand",
                "service unavailable",
                "502 bad gateway",
                "504 gateway timeout",
            )
        )
        is_daily_free_quota = any(
            marker in lower_error
            for marker in (
                "generate_content_free_tier_requests",
                "perdaypermodel-freetier",
                "quota exceeded for metric",
            )
        )
        retry_match = re.search(
            r"retry in\s+([0-9hms.]+s)",
            error_text,
            re.IGNORECASE,
        )
        retry_after = retry_match.group(1) if retry_match else None
        if retry_after:
            retry_after = re.sub(r"\.\d+(?=s$)", "", retry_after)
        limit_match = re.search(r"limit:\s*(\d+)", error_text, re.IGNORECASE)
        daily_limit = limit_match.group(1) if limit_match else None

        if is_daily_free_quota:
            limit_text = (
                f"Google reports a limit of {daily_limit} requests per day."
                if daily_limit
                else ""
            )
            retry_text = (
                f" The provider says to retry in about {retry_after}."
                if retry_after
                else ""
            )
            st.warning(
                "Gemini's free-tier daily request quota for this project/model "
                f"is exhausted. {limit_text}{retry_text} This is a Google "
                "quota, not a Streamlit error. Wait for the reset, check your "
                "Google AI Studio limits, or set GEMINI_MODEL to another model "
                "that has available quota."
            )
        elif is_temporary_provider_error:
            st.warning(
                "Gemini is temporarily unavailable or under high demand. "
                "Wait a few minutes and try again. If the problem persists, "
                "set GEMINI_MODEL to another available Gemini model in your "
                ".env file and restart the app. This is a provider-side "
                "availability issue, not a Streamlit code error."
            )
        elif is_rate_limit:
            st.warning(
                "The Gemini API rate limit or quota has been reached. "
                "Check your Google AI Studio limits, wait for quota to reset, "
                "or set GEMINI_MODEL to a model with available quota and "
                "restart the app."
            )
        else:
            st.error(
                "The LangGraph workflow could not be completed."
            )

        with st.expander("Technical error details"):
            st.exception(exc)


# =============================================================================
# Results
# =============================================================================

def render_results(result: dict) -> None:

    if not result:
        return

    st.divider()

    st.markdown(
        '<div class="section-label">Output</div>',
        unsafe_allow_html=True,
    )

    render_html(
        """
        <div style="
            font-size:2rem;
            font-weight:820;
            letter-spacing:-0.045em;
            color:#f2f4f7;
            margin-bottom:1.25rem;
        ">
            Workflow Results
        </div>
        """
    )

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    review = result.get("review")
    evidence = result.get("evidence", [])
    revision_count = result.get("revision_count", 0)

    metric_cols = st.columns(4)

    with metric_cols[0]:
        render_metric(
            "Research",
            str(
                result.get(
                    "research_mode",
                    "unknown",
                )
            ).replace("_", " "),
        )

    with metric_cols[1]:
        render_metric(
            "Sources",
            str(len(evidence)),
        )

    with metric_cols[2]:
        render_metric(
            "Review",
            f"{review.score}/10"
            if review
            else "—",
        )

    with metric_cols[3]:
        render_metric(
            "Revisions",
            str(revision_count),
        )

    st.markdown(
        "<div style='height:1.5rem'></div>",
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Research Decision
    # -------------------------------------------------------------------------

    research_mode = result.get("research_mode")

    if research_mode:

        left, right = st.columns(
            [1.4, 1],
            gap="large",
        )

        with left:

            st.markdown(
                '<div class="section-label">Decision</div>',
                unsafe_allow_html=True,
            )

            if research_mode == "research":
                st.success(
                    "External research was selected."
                )
            else:
                st.info(
                    "Closed-book mode was selected."
                )

        with right:

            queries = result.get(
                "research_queries",
                [],
            )

            query_word = (
                "query"
                if len(queries) == 1
                else "queries"
            )

            render_html(
                f"""
                <div class="panel">

                    <div class="panel-title">
                        Research strategy
                    </div>

                    <div class="panel-description">
                        {len(queries)} search {query_word}
                        selected by the decision agent.
                    </div>

                </div>
                """
            )

    # -------------------------------------------------------------------------
    # Evidence
    # -------------------------------------------------------------------------

    if evidence:

        st.markdown(
            "<div style='height:1rem'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Grounding</div>',
            unsafe_allow_html=True,
        )

        render_html(
            """
            <div style="
                font-size:1.4rem;
                font-weight:780;
                letter-spacing:-0.03em;
                margin-bottom:0.8rem;
                color:#f0f3f6;
            ">
                Research Evidence
            </div>
            """
        )

        source_cols = st.columns(2)

        for index, item in enumerate(evidence):

            with source_cols[index % 2]:

                render_html(
                    f"""
                    <div class="source-card">

                        <div class="source-number">
                            SOURCE {index + 1}
                        </div>

                        <div class="source-title">
                            {escape(item.title)}
                        </div>

                        <div class="source-url">
                            {escape(item.url)}
                        </div>

                        <div class="source-snippet">
                            {escape(item.snippet)}
                        </div>

                    </div>
                    """
                )

    # -------------------------------------------------------------------------
    # Blog Plan
    # -------------------------------------------------------------------------

    plan = result.get("plan")

    if plan:

        st.markdown(
            "<div style='height:1.2rem'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Planning</div>',
            unsafe_allow_html=True,
        )

        render_html(
            f"""
            <div class="panel">

                <div style="
                    font-size:1.55rem;
                    font-weight:800;
                    letter-spacing:-0.035em;
                    color:#f0f3f6;
                ">
                    {escape(plan.title)}
                </div>

                <div style="
                    margin-top:0.65rem;
                    color:#8b949e;
                    font-size:0.8rem;
                    line-height:1.6;
                ">
                    <b style="color:#b9c1ca;">
                        Audience:
                    </b>
                    {escape(plan.audience)}

                    &nbsp;&nbsp;·&nbsp;&nbsp;

                    <b style="color:#b9c1ca;">
                        Tone:
                    </b>
                    {escape(plan.tone)}
                </div>

                <div style="
                    margin-top:0.7rem;
                    color:#9aa4af;
                    font-size:0.8rem;
                    line-height:1.6;
                ">
                    {escape(plan.purpose)}
                </div>

            </div>
            """
        )

        for index, section in enumerate(
            plan.sections,
            start=1,
        ):

            points = "".join(
                f"<li>{escape(point)}</li>"
                for point in section.key_points
            )

            render_html(
                f"""
                <div class="plan-section">

                    <div class="plan-number">
                        SECTION {index:02d}
                    </div>

                    <div class="plan-heading">
                        {escape(section.heading)}
                    </div>

                    <div class="plan-purpose">
                        {escape(section.purpose)}
                    </div>

                    <div class="plan-points">

                        <ul style="
                            margin:0.35rem 0 0 1rem;
                            padding:0;
                        ">
                            {points}
                        </ul>

                    </div>

                </div>
                """
            )

    # -------------------------------------------------------------------------
    # Review
    # -------------------------------------------------------------------------

    if review:

        st.markdown(
            "<div style='height:1.2rem'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Quality Control</div>',
            unsafe_allow_html=True,
        )

        review_left, review_right = st.columns(
            [1, 2],
            gap="large",
        )

        with review_left:

            if revision_count > 0:
                status_html = (
                    '<span class="review-revised">'
                    'REVISION PERFORMED'
                    '</span>'
                )
            elif not review.needs_revision:
                status_html = (
                    '<span class="review-approved">'
                    'APPROVED'
                    '</span>'
                )
            else:
                status_html = (
                    '<span class="review-revised">'
                    'REVISION REQUESTED'
                    '</span>'
                )

            render_html(
                f"""
                <div class="panel">

                    <div class="review-score">

                        <span class="review-score-number">
                            {review.score}
                        </span>

                        <span class="review-score-max">
                            / 10
                        </span>

                    </div>

                    {status_html}

                    <div style="
                        margin-top:0.9rem;
                        color:#89939e;
                        font-size:0.78rem;
                        line-height:1.6;
                    ">
                        {escape(review.summary)}
                    </div>

                </div>
                """
            )

        with review_right:

            render_html(
                """
                <div class="panel">

                    <div class="panel-title">
                        Reviewer feedback
                    </div>
                """
            )

            if review.strengths:

                st.markdown("**Strengths**")

                for strength in review.strengths:
                    st.markdown(
                        f"- {strength}"
                    )

            if review.issues:

                st.markdown(
                    "**Issues addressed / identified**"
                )

                for issue in review.issues:
                    st.markdown(
                        f"- {issue}"
                    )

            render_html("</div>")

    # -------------------------------------------------------------------------
    # Final Blog
    # -------------------------------------------------------------------------

    final_blog = result.get("final")

    if final_blog:

        st.markdown(
            "<div style='height:1.6rem'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-label">Final Artifact</div>',
            unsafe_allow_html=True,
        )

        render_html(
            """
            <div style="
                font-size:1.8rem;
                font-weight:820;
                letter-spacing:-0.04em;
                color:#f0f3f6;
                margin-bottom:0.8rem;
            ">
                Technical Blog
            </div>
            """
        )

        render_html(
            """
            <div class="blog-surface">
            """
        )

        st.markdown(final_blog)

        render_html("</div>")

        st.markdown(
            "<div style='height:0.8rem'></div>",
            unsafe_allow_html=True,
        )

        download_col, path_col = st.columns(
            [1, 2]
        )

        with download_col:

            st.download_button(
                "↓  Download Markdown",
                data=final_blog,
                file_name="technical_blog.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with path_col:

            output_path = result.get(
                "output_path"
            )

            if output_path:
                st.caption(
                    f"Saved locally to `{output_path}`"
                )

    # -------------------------------------------------------------------------
    # Event Log
    # -------------------------------------------------------------------------

    events = result.get(
        "events",
        [],
    )

    if events:

        st.markdown(
            "<div style='height:1rem'></div>",
            unsafe_allow_html=True,
        )

        with st.expander(
            "View complete workflow event log"
        ):

            for event in events:
                st.markdown(
                    f"• {event}"
                )


# =============================================================================
# Application
# =============================================================================

render_sidebar()

render_hero()


# =============================================================================
# Main Workspace
# =============================================================================

input_col, graph_col = st.columns(
    [1.15, 1],
    gap="large",
)


with input_col:
    topic, as_of, run_button = (
        render_input_panel()
    )


with graph_col:
    render_graph_panel()


# =============================================================================
# Execute
# =============================================================================

if run_button:

    if not topic.strip():

        st.warning(
            "Enter a technical topic before running the agent."
        )

    else:

        run_workflow(
            topic.strip(),
            as_of,
        )


# =============================================================================
# Results
# =============================================================================

if st.session_state.result:
    render_results(
        st.session_state.result
    )
